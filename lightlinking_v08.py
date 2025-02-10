bl_info = {
    "name": "Light Link (Multi-Select Custom Lists with Clear Filter, Scroll & Light Linking)",
    "author": "Your Name",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "description": (
        "For the first selected light, create a new light linking receiver collection "
        "(using bpy.ops.object.light_linking_receiver_collection_new) and add the selected "
        "meshes (including those from selected collections) to it using bpy.ops.object.light_linking_add. "
        "Then assign that linking group to all selected lights by storing its name in a custom property. "
        "Also provides clear buttons for filter fields and always shows a scrollable list."
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
#   Update Functions for Full List Population
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
    scene.ll_light_index = 0 if scene.ll_light_items else -1
    print("Updated Light Items:", [item.name for item in scene.ll_light_items])

def update_mesh_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_mesh_items}
    scene.ll_mesh_items.clear()
    for obj in scene.objects:
        if obj.type == 'MESH':
            item = scene.ll_mesh_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = prev_sel.get(obj.name, False)
    scene.ll_mesh_index = 0 if scene.ll_mesh_items else -1
    print("Updated Mesh Items:", [item.name for item in scene.ll_mesh_items])

def update_collection_items(scene, context):
    prev_sel = {item.name: item.selected for item in scene.ll_collection_items}
    scene.ll_collection_items.clear()
    for coll in bpy.data.collections:
        if "Light Linking for" in coll.name:
            continue  # Skip linking collections
        item = scene.ll_collection_items.add()
        item.name = coll.name
        item.coll = coll
        item.selected = prev_sel.get(coll.name, False)
    scene.ll_collection_index = 0 if scene.ll_collection_items else -1
    print("Updated Collection Items:", [item.name for item in scene.ll_collection_items])

def force_redraw(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

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
#   Operators for Refreshing/Resetting Lists
# -------------------------------------------------------------------
class LL_OT_RefreshSelectedLights(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_lights"
    bl_label = "Refresh Selected Lights"
    bl_description = "Filter the lights list to show only lights selected in the viewport. If none are selected, use the active light."
    
    def execute(self, context):
        scene = context.scene
        selected_lights = [obj for obj in context.selected_objects if obj.type == 'LIGHT']
        if not selected_lights:
            active_obj = context.view_layer.objects.active
            if active_obj and active_obj.type == 'LIGHT':
                selected_lights.append(active_obj)
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected in the viewport")
            return {'CANCELLED'}
        scene.ll_light_items.clear()
        for obj in selected_lights:
            item = scene.ll_light_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = True
        scene.ll_light_index = 0 if scene.ll_light_items else -1
        force_redraw(context)
        self.report({'INFO'}, f"Filtered lights to {len(selected_lights)} item(s)")
        return {'FINISHED'}

class LL_OT_RefreshSelectedMeshes(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_meshes"
    bl_label = "Refresh Selected Meshes"
    bl_description = "Filter the mesh list to show only meshes selected in the viewport. If none are selected, use the active mesh."
    
    def execute(self, context):
        scene = context.scene
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            active_obj = context.view_layer.objects.active
            if active_obj and active_obj.type == 'MESH':
                selected_meshes.append(active_obj)
        if not selected_meshes:
            self.report({'WARNING'}, "No meshes selected in the viewport")
            return {'CANCELLED'}
        scene.ll_mesh_items.clear()
        for obj in selected_meshes:
            item = scene.ll_mesh_items.add()
            item.name = obj.name
            item.obj = obj
            item.selected = True
        scene.ll_mesh_index = 0 if scene.ll_mesh_items else -1
        force_redraw(context)
        self.report({'INFO'}, f"Filtered meshes to {len(selected_meshes)} item(s)")
        return {'FINISHED'}

class LL_OT_RefreshSelectedCollections(bpy.types.Operator):
    bl_idname = "light_link.refresh_selected_collections"
    bl_label = "Refresh Selected Collections"
    bl_description = (
        "Filter the collection list to show only collections selected in the Outliner, "
        "or, as a fallback, the active UI list collection."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_collections = []
        if hasattr(context, "selected_ids"):
            for id_item in context.selected_ids:
                if isinstance(id_item, bpy.types.Collection):
                    selected_collections.append(id_item)
        if not selected_collections:
            selected_collections = [item.coll for item in scene.ll_collection_items if item.selected and item.coll]
        if not selected_collections and scene.ll_collection_index >= 0:
            active_item = scene.ll_collection_items[scene.ll_collection_index]
            if active_item.coll:
                selected_collections.append(active_item.coll)
        if not selected_collections:
            self.report({'WARNING'}, "No collections selected")
            return {'CANCELLED'}
        scene.ll_collection_items.clear()
        for coll in selected_collections:
            item = scene.ll_collection_items.add()
            item.name = coll.name
            item.coll = coll
            item.selected = True
        scene.ll_collection_index = 0 if scene.ll_collection_items else -1
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        self.report({'INFO'}, f"Filtered collections to {len(selected_collections)} item(s)")
        return {'FINISHED'}

class LL_OT_RefreshAllLights(bpy.types.Operator):
    bl_idname = "light_link.refresh_all_lights"
    bl_label = "Refresh All Lights"
    bl_description = "Display all lights in the scene"
    
    def execute(self, context):
        update_light_items(context.scene, context)
        force_redraw(context)
        self.report({'INFO'}, f"Listed all {len(context.scene.ll_light_items)} lights")
        return {'FINISHED'}

class LL_OT_ResetLights(bpy.types.Operator):
    bl_idname = "light_link.reset_lights"
    bl_label = "Reset Lights"
    bl_description = "Deselect all lights in the list"
    
    def execute(self, context):
        for item in context.scene.ll_light_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Light selections reset")
        return {'FINISHED'}

class LL_OT_RefreshAllMeshes(bpy.types.Operator):
    bl_idname = "light_link.refresh_all_meshes"
    bl_label = "Refresh All Meshes"
    bl_description = "Display all meshes in the scene"
    
    def execute(self, context):
        update_mesh_items(context.scene, context)
        force_redraw(context)
        self.report({'INFO'}, f"Listed all {len(context.scene.ll_mesh_items)} meshes")
        return {'FINISHED'}

class LL_OT_ResetMeshes(bpy.types.Operator):
    bl_idname = "light_link.reset_meshes"
    bl_label = "Reset Meshes"
    bl_description = "Deselect all meshes in the list"
    
    def execute(self, context):
        for item in context.scene.ll_mesh_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Mesh selections reset")
        return {'FINISHED'}

class LL_OT_ResetCollections(bpy.types.Operator):
    bl_idname = "light_link.reset_collections"
    bl_label = "Reset Collections"
    bl_description = "Deselect all collections in the list"
    
    def execute(self, context):
        for item in context.scene.ll_collection_items:
            item.selected = False
        force_redraw(context)
        self.report({'INFO'}, "Collection selections reset")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operators for Linking/Unlinking (Light Linking)
# -------------------------------------------------------------------
class LL_OT_Link(bpy.types.Operator):
    bl_idname = "light_link.link"
    bl_label = "Link Lights to Objects"
    bl_description = (
        "For each selected light, create (or use an existing) light linking receiver collection and add "
        "the selected meshes (including those from selected collections) to it, storing the linking group in a custom property."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        selected_meshes = [item.obj for item in scene.ll_mesh_items if item.selected and item.obj]
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
        
        total_linked_meshes = 0
        for light in selected_lights:
            bpy.ops.object.select_all(action='DESELECT')
            light.select_set(True)
            context.view_layer.objects.active = light

            group_name = light.get("light_linking_receiver_collection") or f"Light Linking for {light.name}"
            new_group = bpy.data.collections.get(group_name)
            if not new_group:
                try:
                    bpy.ops.object.light_linking_receiver_collection_new()
                    group_name = light.get("light_linking_receiver_collection") or group_name
                    new_group = bpy.data.collections.get(group_name)
                    if not new_group:
                        self.report({'WARNING'}, f"Failed to create linking group '{group_name}' for {light.name}")
                        continue
                except Exception as e:
                    self.report({'ERROR'}, f"Error creating linking group for {light.name}: {str(e)}")
                    continue
            linked_meshes = 0
            for obj in all_meshes:
                if obj.name not in new_group.objects:
                    new_group.objects.link(obj)
                    linked_meshes += 1
            light["light_linking_receiver_collection"] = group_name
            total_linked_meshes += linked_meshes
        
        self.report({'INFO'}, f"Linked {len(selected_lights)} light(s) to {total_linked_meshes} mesh(es)")
        return {'FINISHED'}

class LL_OT_Unlink(bpy.types.Operator):
    bl_idname = "light_link.unlink"
    bl_label = "Unlink Lights from Objects"
    bl_description = (
        "For each selected light, remove the objects (from the Mesh and Collection lists) "
        "that are linked via the light linking receiver collection and clear the linking property."
    )
    
    def execute(self, context):
        scene = context.scene
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}
        
        total_removed = 0
        for light in selected_lights:
            group_name = light.get("light_linking_receiver_collection")
            if not group_name:
                continue
            linking_group = bpy.data.collections.get(group_name)
            if not linking_group:
                continue
            removed = 0
            for obj in list(linking_group.objects):
                if obj.name in [m_obj.name for m_obj in scene.ll_mesh_items if m_obj.selected]:
                    linking_group.objects.unlink(obj)
                    removed += 1
            total_removed += removed
            if "light_linking_receiver_collection" in light:
                del light["light_linking_receiver_collection"]
        self.report({'INFO'}, f"Unlinked objects from {len(selected_lights)} light(s); removed {total_removed} object(s)")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   Operators for Linking/Unlinking (Shadow Linking)
#   These operators mirror the light linking operators but use a separate
#   custom property and collection naming for shadow linking.
# -------------------------------------------------------------------
class LL_OT_ShadowLink(bpy.types.Operator):
    bl_idname = "light_link.shadow_link"
    bl_label = "Shadow Link Lights to Objects"
    bl_description = (
        "For each selected light, create (or use an existing) shadow linking blocker collection and add "
        "the selected meshes (including those from selected collections) to it, storing the linking group "
        "in a custom property on the light."
    )

    def execute(self, context):
        scene = context.scene

        # Gather selected lights, meshes, and collection meshes
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        selected_meshes = [item.obj for item in scene.ll_mesh_items if item.selected and item.obj]
        collection_meshes = []
        for item in scene.ll_collection_items:
            if item.selected and item.coll:
                for obj in item.coll.all_objects:
                    if obj.type == 'MESH':
                        collection_meshes.append(obj)

        # Combine meshes uniquely by name
        all_meshes = {obj.name: obj for obj in (selected_meshes + collection_meshes)}.values()

        if not selected_lights:
            self.report({'WARNING'}, "No lights selected for shadow linking.")
            return {'CANCELLED'}
        if not list(all_meshes):
            self.report({'WARNING'}, "No mesh objects selected for shadow linking.")
            return {'CANCELLED'}

        total_linked_meshes = 0

        # For each light, create or retrieve the shadow linking blocker collection
        for light in selected_lights:
            # Make this light active (just in case you need that context):
            bpy.ops.object.select_all(action='DESELECT')
            light.select_set(True)
            context.view_layer.objects.active = light

            # Use a custom property for storing the collection name.
            # Note: we use "shadow_linking_blocker_collection" so it’s clear which operator was used.
            group_name = light.get("shadow_linking_blocker_collection") or f"Shadow Linking for {light.name}"
            new_group = bpy.data.collections.get(group_name)
            if not new_group:
                try:
                    bpy.ops.object.light_linking_blocker_collection_new()
                    # After running the operator, the light’s property might be updated;
                    # otherwise we fall back to our original name.
                    group_name = light.get("shadow_linking_blocker_collection") or group_name
                    new_group = bpy.data.collections.get(group_name)
                    if not new_group:
                        self.report({'WARNING'}, f"Failed to create shadow linking group '{group_name}' for {light.name}")
                        continue
                except Exception as e:
                    self.report({'ERROR'}, f"Error creating shadow linking group for {light.name}: {str(e)}")
                    continue

            # Link all selected meshes that are not already in the collection
            linked_meshes = 0
            for obj in all_meshes:
                if obj.name not in new_group.objects:
                    new_group.objects.link(obj)
                    linked_meshes += 1

            # Store the group name in the light’s custom property
            light["shadow_linking_blocker_collection"] = group_name
            total_linked_meshes += linked_meshes

        self.report({'INFO'}, f"Shadow Linked {len(selected_lights)} light(s) to {total_linked_meshes} mesh(es)")
        return {'FINISHED'}


class LL_OT_ShadowUnlink(bpy.types.Operator):
    bl_idname = "light_link.shadow_unlink"
    bl_label = "Shadow Unlink Lights from Objects"
    bl_description = (
        "For each selected light, remove the objects (from the Mesh and Collection lists) that are linked "
        "via the shadow linking blocker collection and clear the linking property."
    )

    def execute(self, context):
        scene = context.scene
        selected_lights = [item.obj for item in scene.ll_light_items if item.selected and item.obj]
        if not selected_lights:
            self.report({'WARNING'}, "No lights selected")
            return {'CANCELLED'}

        total_removed = 0
        for light in selected_lights:
            group_name = light.get("shadow_linking_blocker_collection")
            if not group_name:
                self.report({'INFO'}, f"No shadow linking group found for light '{light.name}'")
                continue

            linking_group = bpy.data.collections.get(group_name)
            if not linking_group:
                self.report({'INFO'}, f"Shadow linking group '{group_name}' not found for light '{light.name}'")
                continue

            removed = 0
            for obj in list(linking_group.objects):
                # Unlink only if the object's name appears in the selected mesh list.
                if obj.name in [m_obj.name for m_obj in scene.ll_mesh_items if m_obj.selected]:
                    try:
                        linking_group.objects.unlink(obj)
                        removed += 1
                    except Exception as e:
                        print(f"DEBUG: Error unlinking {obj.name}: {e}")

            total_removed += removed
            # Remove the shadow linking property from the light after unlinking.
            if "shadow_linking_blocker_collection" in light:
                del light["shadow_linking_blocker_collection"]

        self.report({'INFO'}, f"Shadow Unlinked objects from {len(selected_lights)} light(s); removed {total_removed} object(s)")
        return {'FINISHED'}

# -------------------------------------------------------------------
#   UIList Classes for Scrollable Lists
# -------------------------------------------------------------------
class LL_UL_LightList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = True
        row = layout.row(align=True)
        row.prop(item, "selected", text="")  # Checkbox for selection
        row.label(text=item.name)

class LL_UL_MeshList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = True
        row = layout.row(align=True)
        row.prop(item, "selected", text="")
        row.label(text=item.name)

class LL_UL_CollectionList_UI(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = True
        row = layout.row(align=True)
        row.prop(item, "selected", text="")
        row.label(text=item.name)

# -------------------------------------------------------------------
#   Panel – Three Columns with the UILists on Top, a Shared List Height Slider,
#   and the Operator Buttons (for each column) below the slider.
#   The third row now has two rows:
#     • The first row has the Light Link and Light Unlink buttons.
#     • The second row adds the Shadow Link and Shadow Unlink buttons.
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

        # First row: UILists for Lights, Meshes, and Collections
        main_row = layout.row(align=True)
        
        # Lights Column (only UIList)
        col_lights = main_row.column(align=True)
        col_lights.label(text="Lights")
        col_lights.template_list("LL_UL_LightList_UI", "", scene, "ll_light_items", scene, "ll_light_index", rows=scene.ll_list_rows)
        
        # Meshes Column (only UIList)
        col_meshes = main_row.column(align=True)
        col_meshes.label(text="Meshes")
        col_meshes.template_list("LL_UL_MeshList_UI", "", scene, "ll_mesh_items", scene, "ll_mesh_index", rows=scene.ll_list_rows)
        
        # Collections Column (only UIList)
        col_colls = main_row.column(align=True)
        col_colls.label(text="Collections")
        col_colls.template_list("LL_UL_CollectionList_UI", "", scene, "ll_collection_items", scene, "ll_collection_index", rows=scene.ll_list_rows)
        
        layout.separator()
        # Shared slider for list height
        layout.prop(scene, "ll_list_rows", text="List Height")
        
        layout.separator()
        # Second row: Operator Buttons for each column below the slider
        op_row = layout.row(align=True)
        
        col_light_ops = op_row.column(align=True)
        col_light_ops.operator("light_link.refresh_selected_lights", text="Selected Lights")
        col_light_ops.operator("light_link.refresh_all_lights", text="All Lights")
        col_light_ops.operator("light_link.reset_lights", text="Reset")
        
        col_mesh_ops = op_row.column(align=True)
        col_mesh_ops.operator("light_link.refresh_selected_meshes", text="Selected Meshes")
        col_mesh_ops.operator("light_link.refresh_all_meshes", text="All Meshes")
        col_mesh_ops.operator("light_link.reset_meshes", text="Reset")
        
        col_coll_ops = op_row.column(align=True)
        col_coll_ops.label(text="")  # dummy
        col_coll_ops.label(text="")  # dummy
        col_coll_ops.operator("light_link.reset_collections", text="Reset")
        
        layout.separator()
        # Third row: Link/Unlink Buttons
        link_row = layout.row(align=True)
        link_row.operator("light_link.link", text="Light Link")
        link_row.operator("light_link.unlink", text="Light Unlink")
        
        # Fourth row: Shadow Link/Unlink Buttons
        shadow_link_row = layout.row(align=True)
        shadow_link_row.operator("light_link.shadow_link", text="Shadow Link")
        shadow_link_row.operator("light_link.shadow_unlink", text="Shadow Unlink")

# -------------------------------------------------------------------
#   Registration
# -------------------------------------------------------------------
classes = (
    LL_LightItem,
    LL_MeshItem,
    LL_CollectionItem,
    LL_OT_ToggleSelection,
    LL_OT_RefreshSelectedLights,
    LL_OT_RefreshSelectedMeshes,
    LL_OT_RefreshSelectedCollections,
    LL_OT_RefreshAllLights,
    LL_OT_ResetLights,
    LL_OT_RefreshAllMeshes,
    LL_OT_ResetMeshes,
    LL_OT_ResetCollections,
    LL_OT_Link,
    LL_OT_Unlink,
    LL_OT_ShadowLink,
    LL_OT_ShadowUnlink,
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
    bpy.types.Scene.ll_list_rows = bpy.props.IntProperty(
        name="List Height",
        description="Number of rows to display in each list",
        default=10,
        min=1,
        max=50
    )
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
    del bpy.types.Scene.ll_list_rows

if __name__ == "__main__":
    register()
