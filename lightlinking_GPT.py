bl_info = {
    "name": "Light Link (Multi-Select Custom Lists with Clear Filter, Scroll & Light Linking)",
    "author": "Your Name",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "description": (
        "For the first selected light, create a new light linking receiver collection "
        "(using bpy.ops.object.light_linking_receiver_collection_new) and add the selected "
        "meshes (including those from selected collections) to it using bpy.ops.object.light_linking_add. "
        "Then assign that linking group to all selected lights by storing its name in a custom property. "
        "Also provides clear buttons for filter fields and always shows a scrollable list (20 rows tall)."
    ),
    "category": "Object",
}

import bpy

# -------------------------------------------------------------------
#   Property Groups for List Items (with multi-selection support)
# -------------------------------------------------------------------

class LL_LightItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    selected: bpy.props.BoolProperty(default=False)

class LL_MeshItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    selected: bpy.props.BoolProperty(default=False)

class LL_CollectionItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    coll: bpy.props.PointerProperty(type=bpy.types.Collection)
    selected: bpy.props.BoolProperty(default=False)

# -------------------------------------------------------------------
#   Update Functions for Dynamic Filtering (preserving selection)
# -------------------------------------------------------------------

def update_light_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_light_items}
    scene.ll_light_items.clear()
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            item = scene.ll_light_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = prev_sel.get(obj.name, False)

def update_mesh_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_mesh_items}
    scene.ll_mesh_items.clear()
    for obj in scene.objects:
        if obj.type == 'MESH':
            item = scene.ll_mesh_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = prev_sel.get(obj.name, False)

def update_collection_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_collection_items}
    scene.ll_collection_items.clear()
    for coll in bpy.data.collections:
        item = scene.ll_collection_items.add()
        item.name = coll.name
        item.coll = coll
        item.selected = prev_sel.get(coll.name, False)

# -------------------------------------------------------------------
#   Operator to Toggle an Item’s Selection
# -------------------------------------------------------------------

class LL_OT_ToggleSelection(bpy.types.Operator):
    bl_idname = "light_link.toggle_selection"
    bl_label = "Toggle Selection"
    bl_description = "Toggle the selection state for this item"
    
    item_name: bpy.props.StringProperty()
    item_type: bpy.props.EnumProperty(
        items=[
            ('LIGHT', "Light", ""),
            ('MESH', "Mesh", ""),
            ('COLLECTION', "Collection", ""),
        ]
    )
    
    def execute(self, context):
        scene = context.scene
        if self.item_type == 'LIGHT':
            for item in scene.ll_light_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        elif self.item_type == 'MESH':
            for item in scene.ll_mesh_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        elif self.item_type == 'COLLECTION':
            for item in scene.ll_collection_items:
                if item.name == self.item_name:
                    item.selected = not item.selected
                    break
        else:
            self.report({'WARNING'}, "Unknown item type")
            return {'CANCELLED'}
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Refresh the Lists
# -------------------------------------------------------------------

class LL_OT_Refresh(bpy.types.Operator):
    bl_idname = "light_link.refresh"
    bl_label = "Refresh Lists"
    bl_description = "Refresh the light, mesh, and collection lists"
    
    def execute(self, context):
        scene = context.scene
        update_light_items(scene, context)
        update_mesh_items(scene, context)
        update_collection_items(scene, context)
        self.report({'INFO'}, "Lists refreshed")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Reset All Selections
# -------------------------------------------------------------------

class LL_OT_Reset(bpy.types.Operator):
    bl_idname = "light_link.reset"
    bl_label = "Reset Selections"
    bl_description = "Deselect all items in all lists"
    
    def execute(self, context):
        scene = context.scene
        for item in scene.ll_light_items:
            item.selected = False
        for item in scene.ll_mesh_items:
            item.selected = False
        for item in scene.ll_collection_items:
            item.selected = False
        self.report({'INFO'}, "Selections reset")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operator to Link the Selected Lights to Selected Meshes/Collections
#   (Using bpy.ops.object.light_linking_receiver_collection_new and bpy.ops.object.light_linking_add)
# -------------------------------------------------------------------

class LL_OT_Link(bpy.types.Operator):
    bl_idname = "light_link.link"
    bl_label = "Link Lights to Objects"
    bl_description = (
        "For the first selected light, create a new light linking receiver collection "
        "using bpy.ops.object.light_linking_receiver_collection_new and add the selected "
        "meshes (including those from selected collections) to it using bpy.ops.object.light_linking_add. "
        "Then assign that linking group to all selected lights by storing its name in a custom property."
    )
    
    def execute(self, context):
        scene = context.scene

        # Gather selected lights.
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        # Gather selected meshes.
        selected_meshes = [item.obj for item in scene.ll_mesh_items if item.selected and item.obj]
        # Gather mesh objects from selected collections.
        collection_meshes = []
        for item in scene.ll_collection_items:
            if item.selected and item.coll:
                for obj in item.coll.all_objects:
                    if obj.type == 'MESH':
                        collection_meshes.append(obj)
        
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}
        
        all_meshes = {obj.name: obj for obj in (selected_meshes + collection_meshes)}.values()
        if not list(all_meshes):
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Use the first selected light as the active one.
        active_light = selected_lights[0]
        
        # Ensure the active light is selected and active.
        bpy.ops.object.select_all(action='DESELECT')
        active_light.select_set(True)
        context.view_layer.objects.active = active_light
        
        # Create a new light linking receiver collection.
        try:
            bpy.ops.object.light_linking_receiver_collection_new()
            
            group_name = active_light.get("light_linking_receiver_collection", None)
            if not group_name:
                self.report({'WARNING'}, "No light linking group name found on the active light")
                return {'CANCELLED'}
            
            # Try to retrieve the linking group from bpy.data.collections,
            # and if not found, search in the scene's collection children.
            new_group = bpy.data.collections.get(group_name)
            if not new_group:
                for coll in context.scene.collection.children:
                    if coll.name == group_name:
                        new_group = coll
                        break
            
            if not new_group:
                self.report({'WARNING'}, f"Light linking group '{group_name}' not found")
                return {'CANCELLED'}
            
            linked_meshes = 0
            # For each mesh object, call the built-in operator to add it to the linking group.
            for obj in all_meshes:
                try:
                    override_obj = {"active_object": obj, "selected_objects": [obj]}
                    result = bpy.ops.object.light_linking_add(override_obj, linking_collection=group_name)
                    if result == {'FINISHED'}:
                        linked_meshes += 1
                except Exception as e:
                    self.report({'WARNING'}, f"Could not add {obj.name} to linking group: {str(e)}")
            
            if linked_meshes == 0:
                self.report({'WARNING'}, "No meshes were linked to the light linking group")
                return {'CANCELLED'}
            
            for light in selected_lights:
                light["light_linking_receiver_collection"] = group_name
            
            self.report({'INFO'}, f"Created light linking group '{group_name}' linking {len(selected_lights)} light(s) to {linked_meshes} mesh(es)")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create/configure light linking receiver collection: {str(e)}")
            return {'CANCELLED'}

# -------------------------------------------------------------------
#   UIList Classes for Scrollable Lists (always show 20 rows)
# -------------------------------------------------------------------

class LL_UL_LightList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.selected:
            row.alert = True
        op = row.operator("light_link.toggle_selection", text=item.name, emboss=True)
        op.item_name = item.name
        op.item_type = 'LIGHT'

class LL_UL_MeshList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.selected:
            row.alert = True
        op = row.operator("light_link.toggle_selection", text=item.name, emboss=True)
        op.item_name = item.name
        op.item_type = 'MESH'

class LL_UL_CollectionList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.selected:
            row.alert = True
        op = row.operator("light_link.toggle_selection", text=item.name, emboss=True)
        op.item_name = item.name
        op.item_type = 'COLLECTION'

# -------------------------------------------------------------------
#   Panel – Three Columns Side-by-Side in the N-Panel
# -------------------------------------------------------------------

class LL_PT_Panel(bpy.types.Panel):
    bl_label = "Light Link"
    bl_idname = "LL_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Light Link"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        
        # --- Lights Column ---
        col_lights = row.column(align=True)
        col_lights.label(text="Lights")
        col_lights.template_list("LL_UL_LightList_UI", "", scene, "ll_light_items", scene, "ll_light_index", rows=20)
        
        # --- Meshes Column ---
        col_meshes = row.column(align=True)
        col_meshes.label(text="Meshes")
        col_meshes.template_list("LL_UL_MeshList_UI", "", scene, "ll_mesh_items", scene, "ll_mesh_index", rows=20)
        
        # --- Collections Column ---
        col_colls = row.column(align=True)
        col_colls.label(text="Collections")
        col_colls.template_list("LL_UL_CollectionList_UI", "", scene, "ll_collection_items", scene, "ll_collection_index", rows=20)
        
        layout.separator()
        layout.operator("light_link.refresh", text="Refresh")
        layout.operator("light_link.reset", text="Reset")
        layout.operator("light_link.link", text="Link")

# -------------------------------------------------------------------
#   Registration
# -------------------------------------------------------------------

classes = (
    LL_LightItem,
    LL_MeshItem,
    LL_CollectionItem,
    LL_OT_ToggleSelection,
    LL_OT_Refresh,
    LL_OT_Reset,
    LL_OT_Link,
    LL_UL_LightList_UI,
    LL_UL_MeshList_UI,
    LL_UL_CollectionList_UI,
    LL_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ll_light_items = bpy.props.CollectionProperty(type=LL_LightItem)
    bpy.types.Scene.ll_mesh_items = bpy.props.CollectionProperty(type=LL_MeshItem)
    bpy.types.Scene.ll_collection_items = bpy.props.CollectionProperty(type=LL_CollectionItem)
    
    bpy.types.Scene.ll_light_index = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.ll_mesh_index = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.ll_collection_index = bpy.props.IntProperty(default=-1)
    
    # Initialize the lists on registration.
    update_light_items(bpy.context.scene, bpy.context)
    update_mesh_items(bpy.context.scene, bpy.context)
    update_collection_items(bpy.context.scene, bpy.context)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.ll_light_items
    del bpy.types.Scene.ll_mesh_items
    del bpy.types.Scene.ll_collection_items
    del bpy.types.Scene.ll_light_index
    del bpy.types.Scene.ll_mesh_index
    del bpy.types.Scene.ll_collection_index

if __name__ == "__main__":
    register()
