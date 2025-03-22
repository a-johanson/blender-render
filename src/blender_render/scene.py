import bpy
from dataclasses import dataclass
from typing import Sequence

@dataclass
class MeshTriangles:
    vertices: Sequence[Sequence[float]]
    normals: Sequence[Sequence[float]]
    indices: Sequence[Sequence[int]] # one index sequence per triangle

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

    def triangulate_scene(self):
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                print(f"Ensuring object {obj.name} is triangulated")
                bpy.context.view_layer.objects.active = obj
                bpy.context.view_layer.update()
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.quads_convert_to_tris()
                bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()
    
    def triangle_data(self) -> MeshTriangles:
        view_matrix = self._view_matrix()
        # projection_matrix = self._projection_matrix()

        all_vertices = []
        all_normals = []
        all_indices = []

        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

        for obj in mesh_objects:
            print(f"Processing object: {obj.name}")
            model_matrix = obj.matrix_world
            model_view_matrix = view_matrix @ model_matrix
            normal_matrix = model_view_matrix.inverted().transposed().to_3x3()
            
            print("Model-View Matrix:")
            print(model_view_matrix)

            print("Normal Matrix")
            print(normal_matrix)

            view_vertices = [(model_view_matrix @ vertex.co.to_4d()).to_3d() for vertex in obj.data.vertices]
            view_normals  = [(normal_matrix @ vertex.normal).normalized() for vertex in obj.data.vertices]

            vertex_offest = len(all_vertices)
            assert vertex_offest == len(all_normals), "Vertices and normals should have the same length"
            all_vertices.extend(view_vertices)
            all_normals.extend(view_normals)

            for face in obj.data.polygons:
                # print(f"Face {face.index}:")
                assert len(face.vertices) == 3, "Only triangles are supported"
                face_indices = [vertex_offest + vert_idx for vert_idx in face.vertices]
                all_indices.append(face_indices)
        
        return MeshTriangles(all_vertices, all_normals, all_indices)
