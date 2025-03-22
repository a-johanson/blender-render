import bpy
from dataclasses import dataclass
from typing import Sequence, Optional

@dataclass
class MeshTriangles:
    vertices: Sequence[Sequence[float]]
    normals: Sequence[Sequence[float]]
    indices: Optional[Sequence[Sequence[int]]] # One index sequence per triangle; if None, each triplet of vertices forms a triangle.

class BlenderScene:
    def __init__(self):
        self.camera = self._first_camera()
        assert self.camera is not None, "No camera found in the scene"
        bpy.context.scene.camera = self.camera
        bpy.context.view_layer.update()
        # TODO: get first light in scene

    def _first_camera(self):
        for obj in bpy.context.scene.objects:
            if obj.type == "CAMERA":
                return obj
        return None

    def _view_matrix(self):
        return self.camera.matrix_world.inverted()
    
    def projection_matrix(self):
        return self.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get())
    
    def triangle_data(self) -> MeshTriangles:
        view_matrix = self._view_matrix()
        # projection_matrix = self._projection_matrix()

        all_vertices = []
        all_normals = []
        # all_indices = []

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

            # vertex_offest = len(all_vertices)
            # assert vertex_offest == len(all_normals), "Vertices and normals should have the same length"
            # all_vertices.extend(view_vertices)
            # all_normals.extend(view_normals)

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
