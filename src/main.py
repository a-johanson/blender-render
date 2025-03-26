import sys
import os
import math
import numpy as np

print("Script arguments:", sys.argv)

module_path = os.path.dirname(os.path.abspath(__file__))
print("Module path:", module_path)
sys.path.append(module_path)

modules_to_remove = [module for module in sys.modules if module.startswith("blender_render")]
print("Modules to remove:", modules_to_remove)
for module in modules_to_remove:
    del sys.modules[module]


from blender_render import BlenderScene, BlenderShaderRenderer, scene

scene = BlenderScene()

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

image = renderer.render_triangles(triangle_data, view_projection_matrix, camera_position, light_position, 0.5 * math.pi, width, height)
print("Lightness range:", np.min(image.data[::image.channels]), np.max(image.data[::image.channels]))
print("Orientation range:", np.min(image.data[1::image.channels]), np.max(image.data[1::image.channels]))
print("Depth range:", np.min(image.data[2::image.channels]), np.max(image.data[2::image.channels]))
# image.normalize_channels_independently(value_range=1.0)
# image.to_png(os.path.join(module_path, "output.png"))
image.to_binary_file(os.path.join(module_path, "output.bin"), channels_to_store={0, 1, 2})
