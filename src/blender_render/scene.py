import bpy
from dataclasses import dataclass
from typing import Any, Optional, Sequence
from mathutils import Matrix, Vector

@dataclass
class MeshTriangles:
    vertices: Sequence[Vector]
    normals: Sequence[Vector]
    indices: Optional[Sequence[Sequence[int]]] # One index sequence per triangle; if None, each triplet of vertices forms a triangle.

class BlenderScene:
    def __init__(self):
        self.camera = self._scene_camera()
        assert self.camera is not None, "No main camera found in the scene"
        self.light_camera = self._first_camera(camera_type="ORTHO")
        assert self.light_camera is not None, "No camera with orthogonal projection found in the scene for lighting"
        bpy.context.scene.camera = self.camera
        bpy.context.view_layer.update()

    def _first_camera(self, camera_type="PERSP") -> Optional[bpy.types.Object]:
        for obj in bpy.context.scene.objects:
            if obj.type == "CAMERA" and obj.data.type == camera_type:
                return obj
        return None

    def _scene_camera(self) -> Optional[bpy.types.Object]:
        if bpy.context.scene.camera is not None:
            return bpy.context.scene.camera
        return self._first_camera()

    def camera_view_matrix(self) -> (Any | Matrix):
        return self.camera.matrix_world.inverted()

    def camera_projection_matrix(self, aspect_ratio: float) -> Matrix:
        return self.camera.calc_matrix_camera(depsgraph=bpy.context.evaluated_depsgraph_get(), scale_x=aspect_ratio)

    def camera_position(self) -> Vector:
        return self.camera.matrix_world.to_translation()

    def light_direction(self) -> Vector:
        return self.light_camera.matrix_world.col[2].to_3d().normalized()

    def light_matrix(self, aspect_ratio: float) -> Matrix:
        view = self.light_camera.matrix_world.inverted()
        projection = self.light_camera.calc_matrix_camera(depsgraph=bpy.context.evaluated_depsgraph_get(), scale_x=aspect_ratio)
        return projection @ view

    def world_triangle_data(self) -> MeshTriangles:
        all_vertices = []
        all_normals = []

        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        depsgraph = bpy.context.evaluated_depsgraph_get()

        for obj in mesh_objects:
            evaluated_obj = depsgraph.objects.get(obj.name)
            if not evaluated_obj:
                continue
            mesh = evaluated_obj.data
            print(f"Processing object: {obj.name}")

            model_matrix = obj.matrix_world
            normal_matrix = model_matrix.inverted().transposed().to_3x3()

            print("Model Matrix:")
            print(model_matrix)

            print("Normal Matrix")
            print(normal_matrix)

            world_vertices = [(model_matrix @ vertex.co.to_4d()).to_3d() for vertex in mesh.vertices]
            world_vertex_normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]

            for face in mesh.polygons:
                face_loops = [mesh.loops[loop_index] for loop_index in face.loop_indices]
                face_vertices = [world_vertices[loop.vertex_index] for loop in face_loops]
                if face.use_smooth:
                    face_normals = [world_vertex_normals[loop.vertex_index] for loop in face_loops]
                else:
                    face_normals = [(normal_matrix @ loop.normal).normalized() for loop in face_loops]
                if len(face_vertices) == 3:
                    all_vertices.extend(face_vertices)
                    all_normals.extend(face_normals)
                elif len(face_vertices) == 4: # Triangulate quads on the fly
                    all_vertices.extend(face_vertices[:3])
                    all_normals.extend(face_normals[:3])
                    all_vertices.extend([face_vertices[0], face_vertices[2], face_vertices[3]])
                    all_normals.extend([face_normals[0], face_normals[2], face_normals[3]])
                else:
                    raise ValueError("Only triangles and quads are supported")

        return MeshTriangles(all_vertices, all_normals, None)
