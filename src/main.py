import math
import os
import sys

import numpy as np


print("Script arguments:", sys.argv)

module_path = os.path.dirname(os.path.abspath(__file__))
print("Module path:", module_path)
sys.path.append(module_path)

modules_to_remove = [module for module in sys.modules if module.startswith("blender_render")]
print("Modules to remove:", modules_to_remove)
for module in modules_to_remove:
    del sys.modules[module]


from blender_render import BlenderScene, BlenderShaderRenderer, ndarray_to_gz_file

scene = BlenderScene("Camera", "Light")

triangle_data = scene.world_triangle_data()
print("Vertex count:", len(triangle_data.vertices))
print("Normal count:", len(triangle_data.normals))

renderer = BlenderShaderRenderer()
height = 512
aspect_ratio = 1.5
width = int(height * aspect_ratio)
print("Image size:", width, "x", height)

view_matrix = scene.camera_view_matrix()
projection_matrix = scene.camera_projection_matrix(aspect_ratio)
view_projection_matrix = projection_matrix @ view_matrix
camera_position = scene.camera_position()
light_position = scene.light_position()
print("View matrix:", view_matrix)
print("Projection matrix:", projection_matrix)
print("View-projection matrix:", view_projection_matrix)
print("Camera position:", camera_position)
print("Light position:", light_position)

image_orientation_depth = renderer.render_orientation_and_depth(
    triangle_data,
    view_projection_matrix,
    camera_position,
    light_position,
    0.5 * math.pi,
    width,
    height
)
image_rgb = BlenderShaderRenderer.render_blender_scene(width, height)

print("Image RGB shape:", image_rgb.shape)
print("Image Orientation-Depth shape:", image_orientation_depth.shape)

image_orientation_depth_rgb = np.flip(np.concatenate((image_orientation_depth, image_rgb), axis=-1), axis=0)
# Scale dynamic range of the RGB channels
max_rgb = image_orientation_depth_rgb[:, :, 2:].max()
image_orientation_depth_rgb[:, :, 2:] /= max_rgb
# Apply gamma correction to the RGB channels
gamma = 2.2
image_orientation_depth_rgb[:, :, 2:] = np.power(image_orientation_depth_rgb[:, :, 2:], 1.0 / gamma)
print("Merged image shape:", image_orientation_depth_rgb.shape)
print("Orientation range:", image_orientation_depth_rgb[:, :, 0].min(), image_orientation_depth_rgb[:, :, 0].max())
print("Depth range:", image_orientation_depth_rgb[:, :, 1].min(), image_orientation_depth_rgb[:, :, 1].max())
print("RGB range:", image_orientation_depth_rgb[:, :, 2:].min(), image_orientation_depth_rgb[:, :, 2:].max())

ndarray_to_gz_file(image_orientation_depth_rgb, os.path.join(module_path, "render.bin.gz"))
print("Image written to disk")
