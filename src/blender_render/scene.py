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
        self.camera = self._first_object("CAMERA")
        assert self.camera is not None, "No camera found in the scene"
        self.light = self._first_object("LIGHT")
        assert self.light is not None, "No light found in the scene"
        assert self.light.data.type == "POINT", "Only point lights are supported"
        bpy.context.scene.camera = self.camera
        bpy.context.view_layer.update()

    def _first_object(self, type_name: str) -> Optional[bpy.types.Object]:
        for obj in bpy.context.scene.objects:
            if obj.type == type_name:
                return obj
        return None

    def _view_matrix(self) -> (Any | Matrix):
        return self.camera.matrix_world.inverted()

    def projection_matrix(self) -> Matrix:
        return self.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get())

    def light_position(self) -> Vector:
        light_model_matrix = self.light.matrix_world
        return (self._view_matrix() @ light_model_matrix).to_translation()

    def triangle_data(self) -> MeshTriangles:
        view_matrix = self._view_matrix()

        all_vertices = []
        all_normals = []

        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

        for obj in mesh_objects:
            mesh = obj.data
            print(f"Processing object: {obj.name}")

            model_matrix = obj.matrix_world
            model_view_matrix = view_matrix @ model_matrix
            normal_matrix = model_view_matrix.inverted().transposed().to_3x3()

            print("Model-View Matrix:")
            print(model_view_matrix)

            print("Normal Matrix")
            print(normal_matrix)

            view_vertices = [(model_view_matrix @ vertex.co.to_4d()).to_3d() for vertex in mesh.vertices]
            view_vertex_normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]

            for face in mesh.polygons:
                face_loops = [mesh.loops[loop_index] for loop_index in face.loop_indices]
                face_vertices = [view_vertices[loop.vertex_index] for loop in face_loops]
                if face.use_smooth:
                    face_normals = [view_vertex_normals[loop.vertex_index] for loop in face_loops]
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
