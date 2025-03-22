import sys
import os

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

triangle_data = scene.triangle_data()
print("Vertex count:", len(triangle_data.vertices))
print("Normal count:", len(triangle_data.normals))

renderer = BlenderShaderRenderer()
projection_matrix = scene.projection_matrix()
image = renderer.render_triangles(triangle_data, projection_matrix, 512, 512)
image.normalize_channels_independently(value_range=1.0)
image.to_png(os.path.join(module_path, "output.png"))
