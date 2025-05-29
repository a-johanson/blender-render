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

scene = BlenderScene("Light")

triangle_data = scene.world_triangle_data()
print("Vertex count:", len(triangle_data.vertices))
print("Normal count:", len(triangle_data.normals))

renderer = BlenderShaderRenderer()
width, height = scene.render_resolution()
aspect_ratio = width / height
print(f"Image size: {width} x {height} (aspect ratio: {aspect_ratio})")

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

pixels_orientation_depth_value = renderer.render_depth_orientation_value(
    triangle_data,
    view_projection_matrix,
    camera_position,
    light_position,
    True,
    0.5 * math.pi,
    width,
    height
)
image_depth_orientation_value = np.array(pixels_orientation_depth_value, dtype=np.float32).reshape((height, width, 3))
print(image_depth_orientation_value.shape)
print("Depth range:", image_depth_orientation_value[:, :, 0].min(), image_depth_orientation_value[:, :, 0].max())
print("Orientation range:", image_depth_orientation_value[:, :, 1].min(), image_depth_orientation_value[:, :, 1].max())
print("Value range:", image_depth_orientation_value[:, :, 2].min(), image_depth_orientation_value[:, :, 2].max())

ndarray_to_gz_file(image_depth_orientation_value, os.path.join(module_path, f"render_dov.bin.gz"))
print("Rendered image data written to disk")
