import math
import os
import sys

from mathutils import Vector

# import numpy as np


print("Script arguments:", sys.argv)

module_path = os.path.dirname(os.path.abspath(__file__))
print("Module path:", module_path)
sys.path.append(module_path)

modules_to_remove = [module for module in sys.modules if module.startswith("blender_render")]
print("Modules to remove:", modules_to_remove)
for module in modules_to_remove:
    del sys.modules[module]


from blender_render import BlenderScene, BlenderShaderRenderer, DepthDirectionValueGrid, GreasePencilDrawing, flow_field_streamlines, streamlines_to_strokes
# from blender_render import ndarray_to_gz_file

scene = BlenderScene("Light")

triangle_data = scene.world_triangle_data()
print("Vertex count:", len(triangle_data.vertices))
print("Normal count:", len(triangle_data.normals))

width, height = scene.render_resolution()
aspect_ratio = width / height
aspect_ratio_inverse = height / width
ratio_sensor_size_to_focal_length = scene.ratio_sensor_size_to_focal_length()
print(f"Image size: {width} x {height}, Aspect ratio: {aspect_ratio:.5f}")
print(f"Sensor size to focal length ratio: {ratio_sensor_size_to_focal_length:.5f}")

view_matrix = scene.camera_view_matrix()
projection_matrix = scene.camera_projection_matrix(aspect_ratio)
view_projection_matrix = projection_matrix @ view_matrix
camera_rotation = scene.camera_rotation_matrix()
camera_position = scene.camera_position()
light_position = scene.light_position()
print("View matrix:", view_matrix)
print("Projection matrix:", projection_matrix)
print("View-projection matrix:", view_projection_matrix)
print("Camera position:", camera_position)
print("Light position:", light_position)

frame_center = camera_position + (camera_rotation @ Vector((0.0, 0.0, -1.0)))
frame_dir_x = camera_rotation @ Vector((1.0, 0.0, 0.0))
frame_dir_y = camera_rotation @ Vector((0.0, 1.0, 0.0))
frame_x_axis = ratio_sensor_size_to_focal_length * min(aspect_ratio, 1.0) * frame_dir_x
frame_y_axis = ratio_sensor_size_to_focal_length * min(aspect_ratio_inverse, 1.0) * frame_dir_y
frame_origin = frame_center - (0.5 - 0.5/width) * frame_x_axis - (0.5 - 0.5/height) * frame_y_axis
print("Frame center:", frame_center)
print("Frame direction X:", frame_dir_x)
print("Frame direction Y:", frame_dir_y)
print("Frame X axis:", frame_x_axis)
print("Frame Y axis:", frame_y_axis)
print("Frame origin:", frame_origin)


renderer = BlenderShaderRenderer()
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

grid = DepthDirectionValueGrid(width, height, pixels_orientation_depth_value)

d_sep = 11.0
step_size = 0.9
streamlines = flow_field_streamlines(
    grid,
    rng_seed=420163298,
    seed_box_size=1.9*d_sep,
    d_sep=d_sep,
    d_test_factor=0.65,
    d_step=step_size,
    max_depth_step=0.05,
    max_accum_angle=5.0,
    max_steps=110,
    min_steps=10
)

strokes = streamlines_to_strokes(
    width,
    height,
    frame_origin.to_tuple(),
    frame_x_axis.to_tuple(),
    frame_y_axis.to_tuple(),
    streamlines
)

gp_drawing = GreasePencilDrawing("HatchLines", "Layer")
gp_drawing.clear()
gp_drawing.add_strokes(strokes, radius=0.0004)


# image_depth_orientation_value = np.array(pixels_orientation_depth_value, dtype=np.float32).reshape((height, width, 3))
# print(image_depth_orientation_value.shape)
# print("Depth range:", image_depth_orientation_value[:, :, 0].min(), image_depth_orientation_value[:, :, 0].max())
# print("Orientation range:", image_depth_orientation_value[:, :, 1].min(), image_depth_orientation_value[:, :, 1].max())
# print("Value range:", image_depth_orientation_value[:, :, 2].min(), image_depth_orientation_value[:, :, 2].max())

# ndarray_to_gz_file(image_depth_orientation_value, os.path.join(module_path, f"render_dov.bin.gz"))
# print("Rendered image data written to disk")
