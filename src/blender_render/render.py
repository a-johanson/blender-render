import os
from dataclasses import dataclass
from collections.abc import Sequence

import bpy
import gpu
import numpy as np
from mathutils import Matrix, Vector

from .scene import MeshTriangles


@dataclass
class ShaderAttribute:
    data_type: str
    name: str

class BlenderShaderRenderer:
    def __init__(self):
        self.shader = __class__._shader_setup(
            name="main_br_shader",
            vertex_source=__class__._read_file("vertex_shader.glsl"),
            fragment_source=__class__._read_file("fragment_shader.glsl"),
            constants=[
                ShaderAttribute("MAT4", "viewProjectionMatrix"),
                ShaderAttribute("VEC3", "cameraPosition"),
                ShaderAttribute("VEC3", "light"),
                ShaderAttribute("BOOL", "isDirectionalLight"),
                ShaderAttribute("FLOAT", "orientationOffset"),
            ],
            samplers=[
            ],
            vertex_in=[
                ShaderAttribute("VEC3", "position"),
                ShaderAttribute("VEC3", "normal"),
            ],
            vertex_out=[
                ShaderAttribute("VEC3", "fragPos"),
                ShaderAttribute("VEC3", "fragNorm"),
            ],
            fragment_out=[
                ShaderAttribute("VEC4", "fragColor"),
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
            samplers: Sequence[ShaderAttribute],
            vertex_in: Sequence[ShaderAttribute],
            vertex_out: Sequence[ShaderAttribute],
            fragment_out: Sequence[ShaderAttribute],
        ) -> gpu.types.GPUShader:
        shader_info = gpu.types.GPUShaderCreateInfo()

        for constant in constants:
            shader_info.push_constant(constant.data_type, constant.name)
        for idx, sampler in enumerate(samplers):
            shader_info.sampler(idx, sampler.data_type, sampler.name)
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

    @staticmethod
    def render_scene_to_disk(filepath: str, width: int, height: int):
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.context.scene.render.image_settings.color_mode = "RGB"
        bpy.context.scene.render.image_settings.color_depth = "8"
        bpy.context.scene.render.image_settings.compression = 100
        bpy.context.scene.render.filepath = filepath
        bpy.context.scene.render.use_overwrite = True

        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
        bpy.context.scene.render.pixel_aspect_x = 1.0
        bpy.context.scene.render.pixel_aspect_y = 1.0
        bpy.context.scene.render.resolution_percentage = 100

        bpy.ops.render.render(animation=False, write_still=True, use_viewport=False)

    @staticmethod
    def render_scene(width: int, height: int) -> np.ndarray:
        # See https://ammous88.wordpress.com/2015/01/16/blender-access-render-results-pixels-directly-from-python-2/
        assert bpy.context.scene.use_nodes, "Blender scene does not use the compositing node tree -- ensure to enable it in the scene"
        viewer_image = bpy.data.images.get("Viewer Node")
        assert viewer_image is not None, "Viewer Node image not found -- make sure to add a Viewer Node to the compositing node tree"

        bpy.context.scene.render.resolution_x = width
        bpy.context.scene.render.resolution_y = height
        bpy.context.scene.render.pixel_aspect_x = 1.0
        bpy.context.scene.render.pixel_aspect_y = 1.0
        bpy.context.scene.render.resolution_percentage = 100

        bpy.ops.render.render(animation=False, write_still=False, use_viewport=False)

        assert viewer_image.size[0] == width and viewer_image.size[1] == height, "Viewer Node image size does not match the width and height of the rendered image"
        pixels = np.array(viewer_image.pixels[:], dtype=np.float32)
        rgb_pixels = pixels.reshape((height, width, 4))[:, :, :3]
        return rgb_pixels

    def render_depth_orientation_value(
            self,
            triangles: MeshTriangles,
            view_projection_matrix: Matrix,
            camera_position: Vector,
            light: Vector,
            is_directional_light: bool,
            orientation_offset: float,
            width: int,
            height: int
        ) -> Sequence[tuple[float, float, float]]:
        batch = __class__._prepare_batch(triangles)
        depth_texture = gpu.types.GPUTexture(size=(width, height), format="DEPTH_COMPONENT32F")
        depth_texture.clear(format="FLOAT", value=(1.0,))
        color_texture = gpu.types.GPUTexture(size=(width, height), format="RGBA32F")
        color_texture.clear(format="FLOAT", value=(-1.0, 0.0, 0.0, 1.0))
        fb = gpu.types.GPUFrameBuffer(depth_slot=depth_texture, color_slots=color_texture)
        with fb.bind():
            self.shader.uniform_float("viewProjectionMatrix", view_projection_matrix)
            self.shader.uniform_float("cameraPosition", camera_position)
            self.shader.uniform_float("light", light)
            self.shader.uniform_bool("isDirectionalLight", is_directional_light)
            self.shader.uniform_float("orientationOffset", orientation_offset)
            __class__._set_gpu_state()
            batch.draw(self.shader)
            __class__._reset_gpu_state()
            buffer = color_texture.read()
            buffer.dimensions = width * height * 4
            buffer_values = [v for v in buffer]
        depth_orientation_value_pixels = [
            tuple(buffer_values[i:i+3]) for i in range(0, len(buffer_values), 4)
        ]
        return depth_orientation_value_pixels
