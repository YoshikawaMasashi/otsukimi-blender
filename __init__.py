import bpy
import bmesh
import collections
from typing import Optional, Any, List
import math
import numpy as np

bl_info = {
    "name": "otsukimi",
    "author": "marshi",
    "description": "otsukimi blender addon",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "",
    "url": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "marshi"
}


class OtsukimiLeafMaker(bpy.types.Operator):

    bl_idname = "otsukimi.leaf_maker"
    bl_label = "Leaf Maker"
    bl_options = {"REGISTER",}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        if bpy.context.scene.otsukimi_leaf_object is not '' and len(bpy.context.selected_objects) > 0:
            leaves_objs = []
            target_objects = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in target_objects:
                area = np.sum([p.area for p in obj.data.polygons])

                obj.modifiers.new("part", type='PARTICLE_SYSTEM')
                part = obj.particle_systems[0]
                part.settings.type = 'HAIR'

                part.settings.hair_length = bpy.context.scene.otsukimi_leaf_hair_length
                part.settings.count = int(bpy.context.scene.otsukimi_leaf_density * area)

                part.settings.hair_step = bpy.context.scene.otsukimi_leaf_segment
                part.seed = bpy.context.scene.otsukimi_leaf_seed

                part.settings.use_advanced_hair = True
                part.settings.use_rotations = True
                part.settings.rotation_factor_random = bpy.context.scene.otsukimi_leaf_rotation_randamize
                part.settings.phase_factor = bpy.context.scene.otsukimi_leaf_rotation_phase
                part.settings.phase_factor_random = bpy.context.scene.otsukimi_leaf_rotation_randamize_phase

                part.settings.render_type = 'OBJECT'
                part.settings.particle_size = 1.0
                part.settings.instance_object = bpy.data.objects[bpy.context.scene.otsukimi_leaf_object]

                obj.select_set(True)
                bpy.ops.object.duplicates_make_real()
                bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=False)
                bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
                bpy.ops.object.join()

                part_settings_name = part.settings.name

                obj.modifiers.remove(obj.modifiers["part"])
                bpy.data.particles.remove(particle=bpy.data.particles[part_settings_name])

                leaves_obj = bpy.context.selected_objects[0]
                leaves_obj.name = "Leaves"
                
                leaves_objs.append(leaves_obj)

            bpy.ops.object.select_all(action='DESELECT')
            for leaves_obj in leaves_objs:
                leaves_obj.select_set(True)
            bpy.context.view_layer.objects.active = leaves_objs[0]
            bpy.ops.object.join()
            bpy.context.selected_objects[0].name = "Leaves"
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            leaves_obj = bpy.context.selected_objects[0]

            bm = bmesh.new()
            bm.from_mesh(leaves_obj.data)

            min_z = np.min([v.co.z for v in bm.verts])
            normal_sphere_radius = 1.05 * np.sqrt(np.max(
                [v.co.x * v.co.x + v.co.y * v.co.y + (v.co.z - min_z) * (v.co.z - min_z) for v in bm.verts]
                ))
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=normal_sphere_radius,
                enter_editmode=True,
                align='WORLD',
                location=(0, 0, min_z),
                scale=(1, 1, 1)
            )
            bm=bmesh.from_edit_mesh(bpy.context.selected_objects[0].data)
            for v in bm.verts:
                if v.co.z < -1e-5:
                    bm.verts.remove(v)

            bpy.ops.object.mode_set(mode="OBJECT")
            normal_sphere = bpy.context.selected_objects[0]
            normal_sphere.name = "Normal_Sphere"

            bpy.ops.object.select_all(action='DESELECT')
            leaves_obj.select_set(True)
            bpy.context.view_layer.objects.active = leaves_obj
            bpy.context.object.data.use_auto_smooth = True
            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'CUSTOM_NORMAL'}
            bpy.context.object.modifiers["DataTransfer"].loop_mapping = 'NEAREST_POLY'
            bpy.context.object.modifiers["DataTransfer"].object = normal_sphere
            bpy.ops.object.modifier_apply(modifier="DataTransfer")

            bpy.data.objects.remove(normal_sphere)

            return {'FINISHED'}
        return {'CANCELLED'}


class OtsukimiPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "otsukimi"
    bl_label = "otsukimi"

    #--- draw ---#
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        scene = context.scene
        col.label(text="Make Leaves")
        col.label(text="Leaf Object")
        col.prop_search(scene, "otsukimi_leaf_object", scene, "objects")
        col.label(text="Hair Length")
        col.prop(scene, 'otsukimi_leaf_hair_length')
        col.label(text="Density")
        col.prop(scene, 'otsukimi_leaf_density')
        col.label(text="Segments")
        col.prop(scene, 'otsukimi_leaf_segment')
        col.label(text="Seed")
        col.prop(scene, 'otsukimi_leaf_seed')
        col.label(text="Rotation Randamize")
        col.prop(scene, 'otsukimi_leaf_rotation_randamize')
        col.label(text="Rotation Phase")
        col.prop(scene, 'otsukimi_leaf_rotation_phase')
        col.label(text="Rotation Randamize Phase")
        col.prop(scene, 'otsukimi_leaf_rotation_randamize_phase')
        col.operator("otsukimi.leaf_maker", text="make leaves")


classes = [
    OtsukimiLeafMaker,
    OtsukimiPanel,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.otsukimi_leaf_object = bpy.props.StringProperty()
    bpy.types.Scene.otsukimi_leaf_hair_length = bpy.props.FloatProperty(default=1.0, min=0.0)
    bpy.types.Scene.otsukimi_leaf_density = bpy.props.FloatProperty(default=10.0, min=0.0)
    bpy.types.Scene.otsukimi_leaf_segment = bpy.props.IntProperty(default=2, min=0)
    bpy.types.Scene.otsukimi_leaf_seed = bpy.props.IntProperty(default=0, min=0)
    bpy.types.Scene.otsukimi_leaf_rotation_randamize = bpy.props.FloatProperty(default=0.771, min=0.0, max=1.0)
    bpy.types.Scene.otsukimi_leaf_rotation_phase = bpy.props.FloatProperty(default=0.169, min=0.0, max=1.0)
    bpy.types.Scene.otsukimi_leaf_rotation_randamize_phase = bpy.props.FloatProperty(default=0.606, min=0.0, max=1.0)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.otsukimi_leaf_object
    del bpy.types.Scene.otsukimi_leaf_hair_length
    del bpy.types.Scene.otsukimi_leaf_density
    del bpy.types.Scene.otsukimi_leaf_segment
    del bpy.types.Scene.otsukimi_leaf_seed
    del bpy.types.Scene.otsukimi_leaf_rotation_randamize
    del bpy.types.Scene.otsukimi_leaf_rotation_phase
    del bpy.types.Scene.otsukimi_leaf_rotation_randamize_phase

if __name__ == "__main__":
    register()
