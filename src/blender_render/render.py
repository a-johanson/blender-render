from typing import Sequence, Set
import bpy
import gpu
from mathutils import Matrix, Vector
import os
import struct
import numpy as np
from .scene import MeshTriangles


class FloatImage:
    def __init__(self, width: int, height: int, channels: int, data: Sequence[float]):
        assert len(data) == width * height * channels, "Data length does not match image dimensions"
        self.width = width
        self.height = height
        self.channels = channels
        self.data = np.array(data, dtype=np.float32)

    def normalize_channel(self, channel: int, value_range: float = 1.0):
        max_value = np.max(self.data[channel::self.channels])
        min_value = np.min(self.data[channel::self.channels])
        if max_value == min_value:
            self.data[channel::self.channels] = 0.0
        else:
            self.data[channel::self.channels] = value_range * ((self.data[channel::self.channels] - min_value) / (max_value - min_value))

    def normalize_channels_independently(self, value_range: float = 1.0):
        for channel in range(self.channels):
            self.normalize_channel(channel, value_range)

    def to_png(self, path: str):
        IMAGE_NAME = "BlenderRenderImage"
        if IMAGE_NAME in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[IMAGE_NAME])
        bpy.data.images.new(IMAGE_NAME, self.width, self.height)
        image = bpy.data.images[IMAGE_NAME]
        image.scale(self.width, self.height)

        image.pixels = self.data.tolist()
        image.file_format = "PNG"
        image.save(filepath=path)

    def to_binary_file(self, path: str, channels_to_store: Set[int] = None):
        if channels_to_store is None or len(channels_to_store) == 0:
            channels_to_store = set(range(self.channels))
        assert all(0 <= channel < self.channels for channel in channels_to_store), "Invalid channel index"

        with open(path, "wb") as file:
            file.write(self.width.to_bytes(4, "little"))
            file.write(self.height.to_bytes(4, "little"))
            file.write(len(channels_to_store).to_bytes(4, "little"))
            iter = np.nditer(self.data, flags=["c_index"])
            for value in iter:
                if iter.index % self.channels in channels_to_store:
                    file.write(struct.pack("<f", value))


class BlenderShaderRenderer:
    def __init__(self):
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.push_constant("MAT4", "projectionMatrix")
        shader_info.push_constant("VEC3", "lightPosition")
        shader_info.vertex_in(0, "VEC3", "position")
        shader_info.vertex_in(1, "VEC3", "normal")

        vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
        vert_out.smooth("VEC3", "pos")
        vert_out.smooth("VEC3", "norm")
        shader_info.vertex_out(vert_out)

        shader_info.fragment_out(0, "VEC4", "FragColor")

        shader_info.vertex_source(self._read_file("vertex_shader.glsl"))
        shader_info.fragment_source(self._read_file("fragment_shader.glsl"))

        self.shader = gpu.shader.create_from_info(shader_info)

    def _read_file(self, relative_path: str):
        filepath = os.path.join(os.path.dirname(__file__), relative_path)
        with open(filepath, "r") as file:
            return file.read()

    def render_triangles(
            self,
            triangles: MeshTriangles,
            projection_matrix: Matrix,
            light_position: Vector,
            width: int,
            height: int
        ) -> FloatImage:
        vertex_format = gpu.types.GPUVertFormat()
        vertex_format.attr_add(id="position", comp_type="F32", len=3, fetch_mode="FLOAT")
        vertex_format.attr_add(id="normal", comp_type="F32", len=3, fetch_mode="FLOAT")

        vertex_buffer = gpu.types.GPUVertBuf(vertex_format, len(triangles.vertices))
        vertex_buffer.attr_fill("position", triangles.vertices)
        vertex_buffer.attr_fill("normal", triangles.normals)

        batch = None
        if triangles.indices is not None:
            index_buffer = gpu.types.GPUIndexBuf(type="TRIS", seq=triangles.indices)
            batch = gpu.types.GPUBatch(type="TRIS", buf=vertex_buffer, elem=index_buffer)
        else:
            batch = gpu.types.GPUBatch(type="TRIS", buf=vertex_buffer)

        offscreen = gpu.types.GPUOffScreen(width, height, format="RGBA32F")

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(0.0, 0.0, 0.0, 0.0), depth=float("inf"))
            gpu.state.depth_mask_set(True)
            gpu.state.depth_test_set("LESS")
            gpu.state.face_culling_set("BACK")
            gpu.state.front_facing_set(False)
            self.shader.uniform_float("projectionMatrix", projection_matrix)
            self.shader.uniform_float("lightPosition", light_position)
            batch.draw(self.shader)
            buffer = fb.read_color(0, 0, width, height, 4, 0, "FLOAT")
            gpu.state.depth_mask_set(False)
            gpu.state.depth_test_set("NONE")
            gpu.state.face_culling_set("NONE")
            gpu.state.front_facing_set(False)
        offscreen.free()
        buffer.dimensions = width * height * 4
        image_data = [v for v in buffer]
        return FloatImage(width, height, 4, image_data)
