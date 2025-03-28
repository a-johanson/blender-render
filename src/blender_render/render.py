from typing import Sequence, Set
import bpy
import gpu
from dataclasses import dataclass
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

        flipped_data = self.data.reshape((self.height, self.width, self.channels))[::-1, :, :].flatten()

        with open(path, "wb") as file:
            file.write(self.width.to_bytes(4, "little"))
            file.write(self.height.to_bytes(4, "little"))
            file.write(len(channels_to_store).to_bytes(4, "little"))
            iter = np.nditer(flipped_data, flags=["c_index"])
            for value in iter:
                if iter.index % self.channels in channels_to_store:
                    file.write(struct.pack("<f", value))


@dataclass
class ShaderAttribute:
    data_type: str
    name: str


class BlenderShaderRenderer:
    def __init__(self):
        self.main_shader = __class__._shader_setup(
            name="main_shader",
            vertex_source=__class__._read_file("vertex_shader.glsl"),
            fragment_source=__class__._read_file("fragment_shader.glsl"),
            constants=[
                ShaderAttribute("MAT4", "viewProjectionMatrix"),
                ShaderAttribute("VEC3", "cameraPosition"),
                ShaderAttribute("VEC3", "lightDirection"),
                ShaderAttribute("FLOAT", "orientationOffset"),
            ],
            vertex_in=[
                ShaderAttribute("VEC3", "position"),
                ShaderAttribute("VEC3", "normal"),
            ],
            vertex_out=[
                ShaderAttribute("VEC3", "pos"),
                ShaderAttribute("VEC3", "norm"),
            ],
            fragment_out=[
                ShaderAttribute("VEC4", "FragColor"),
            ]
        )
        self.depth_shader = __class__._shader_setup(
            name="depth_shader",
            vertex_source=__class__._read_file("vertex_shader_depth.glsl"),
            fragment_source=__class__._read_file("fragment_shader_depth.glsl"),
            constants=[
                ShaderAttribute("MAT4", "viewProjectionMatrix"),
                ShaderAttribute("VEC3", "cameraPosition"),
            ],
            vertex_in=[
                ShaderAttribute("VEC3", "position"),
            ],
            vertex_out=[
                ShaderAttribute("VEC3", "pos"),
            ],
            fragment_out=[
                ShaderAttribute("VEC4", "FragColor"),
            ]
        )

    @staticmethod
    def _read_file(relative_path: str) -> str:
        filepath = os.path.join(os.path.dirname(__file__), relative_path)
        with open(filepath, "r") as file:
            return file.read()
    
    @staticmethod
    def _shader_setup(
            name: str,
            vertex_source: str,
            fragment_source: str,
            constants: Sequence[ShaderAttribute],
            vertex_in: Sequence[ShaderAttribute],
            vertex_out: Sequence[ShaderAttribute],
            fragment_out: Sequence[ShaderAttribute],
        ) -> gpu.types.GPUShader:
        shader_info = gpu.types.GPUShaderCreateInfo()

        for constant in constants:
            shader_info.push_constant(constant.data_type, constant.name)
        for idx, vin in enumerate(vertex_in):
            shader_info.vertex_in(idx, vin.data_type, vin.name)

        vertex_out_info = gpu.types.GPUStageInterfaceInfo(name)
        for idx, vout in enumerate(vertex_out):
            vertex_out_info.smooth(vout.data_type, vout.name)
        shader_info.vertex_out(vertex_out_info)

        for idx, fout in enumerate(fragment_out):
            shader_info.fragment_out(idx, fout.data_type, fout.name)

        shader_info.vertex_source(vertex_source)
        shader_info.fragment_source(fragment_source)

        return gpu.shader.create_from_info(shader_info)
    
    @staticmethod
    def _prepare_batch(triangles: MeshTriangles, pass_normals=True) -> gpu.types.GPUBatch:
        vertex_format = gpu.types.GPUVertFormat()
        vertex_format.attr_add(id="position", comp_type="F32", len=3, fetch_mode="FLOAT")
        if pass_normals:
            vertex_format.attr_add(id="normal", comp_type="F32", len=3, fetch_mode="FLOAT")

        vertex_buffer = gpu.types.GPUVertBuf(vertex_format, len(triangles.vertices))
        vertex_buffer.attr_fill("position", triangles.vertices)
        if pass_normals:
            vertex_buffer.attr_fill("normal", triangles.normals)

        batch = None
        if triangles.indices is not None:
            index_buffer = gpu.types.GPUIndexBuf(type="TRIS", seq=triangles.indices)
            batch = gpu.types.GPUBatch(type="TRIS", buf=vertex_buffer, elem=index_buffer)
        else:
            batch = gpu.types.GPUBatch(type="TRIS", buf=vertex_buffer)

        return batch
    
    @staticmethod
    def _set_gpu_state():
        gpu.state.depth_mask_set(True)
        gpu.state.depth_test_set("LESS")
        gpu.state.face_culling_set("BACK")
        gpu.state.front_facing_set(False)
    
    @staticmethod
    def _reset_gpu_state():
        gpu.state.depth_mask_set(False)
        gpu.state.depth_test_set("NONE")
        gpu.state.face_culling_set("NONE")
        gpu.state.front_facing_set(False)

    def render_triangles(
            self,
            triangles: MeshTriangles,
            view_projection_matrix: Matrix,
            camera_position: Vector,
            light_direction: Vector,
            orientation_offset: float,
            width: int,
            height: int
        ) -> FloatImage:
        batch = __class__._prepare_batch(triangles)

        offscreen = gpu.types.GPUOffScreen(width, height, format="RGBA32F")

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(0.0, 0.0, 0.0, 0.0), depth=float("inf"))
            self.main_shader.uniform_float("viewProjectionMatrix", view_projection_matrix)
            self.main_shader.uniform_float("cameraPosition", camera_position)
            self.main_shader.uniform_float("lightDirection", light_direction)
            self.main_shader.uniform_float("orientationOffset", orientation_offset)
            __class__._set_gpu_state()
            batch.draw(self.main_shader)
            __class__._reset_gpu_state()
            buffer = fb.read_color(0, 0, width, height, 4, 0, "FLOAT")
        offscreen.free()
        buffer.dimensions = width * height * 4
        image_data = [v for v in buffer]
        return FloatImage(width, height, 4, image_data)
