#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****

# <pep8-80 compliant>

bl_info = {
    "name": "Export Selected",
    "author": "dairin0d, rking",
    "version": (1, 0),
    "blender": (2, 6, 0),
    "location": "File > Export > Selected",
    "description": "Export selected objects to a chosen format",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}
#============================================================================#

import bpy

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

class CurrentFormatProperties(bpy.types.PropertyGroup):
    pass

class ExportSelected(bpy.types.Operator, ExportHelper):
    '''Export selected objects to a chosen format'''
    bl_idname = "export_scene.selected"
    bl_label = "Export Selected"
    
    filename_ext = StringProperty(
        default="",
        options={'HIDDEN'},
        )
    
    filter_glob = StringProperty(
        default="*.*",
        options={'HIDDEN'},
        )
    
    include_children = BoolProperty(
        name="Include Children",
        description="Keep children even if they're not selected",
        default=True,
        )
    
    visible_name = bpy.props.StringProperty(
        name="Format",
        description="Export format",
        options={'HIDDEN'},
        )
    
    format = bpy.props.StringProperty(
        name="Format",
        description="Export format",
        options={'HIDDEN'},
        )
    
    format_props = bpy.props.PointerProperty(
        type=CurrentFormatProperties,
        options={'HIDDEN'},
        )
    
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) != 0
    
    def invoke(self, context, event):
        category_name, op_name = self.format.split(".")
        category = getattr(bpy.ops, category_name)
        op = getattr(category, op_name)
        
        inst = op.get_instance()
        op_class = type(inst)
        
        rna = op.get_rna()
        
        keys_to_remove = []
        for key in dir(CurrentFormatProperties):
            if key.startswith("_"):
                continue
            value = getattr(CurrentFormatProperties, key)
            if isinstance(value, tuple):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            delattr(CurrentFormatProperties, key)
        
        for key in dir(op_class):
            if key.startswith("_"):
                continue
            value = getattr(op_class, key)
            if isinstance(value, tuple):
                setattr(CurrentFormatProperties, key, value)
        
        # TODO:
        # Collada properties: selected, second_life
        
        self.filepath = context.object.name + self.filename_ext
        return ExportHelper.invoke(self, context, event)
    
    def add_obj(self, obj, objs):
        objs.add(obj)
        if self.include_children:
            for child in obj.children:
                self.add_obj(child, objs)
    
    def clear_world(self, context):
        message = "Killing everything but the Chosen Ones"
        if self.include_children:
            message += " and their children"
        bpy.ops.ed.undo_push(message=message)
        
        for scene in bpy.data.scenes:
            if scene != context.scene:
                bpy.data.scenes.remove(scene)
        
        objs = set()
        
        for obj in context.scene.objects:
            if obj.select:
                self.add_obj(obj, objs)
        
        for obj in context.scene.objects:
            if obj not in objs:
                context.scene.objects.unlink(obj)
        context.scene.update()
    
    def execute(self, context):
        self.clear_world(context)
        
        category_name, op_name = self.format.split(".")
        category = getattr(bpy.ops, category_name)
        op = getattr(category, op_name)
        
        props = {}
        for key in self.iter_prop_names():
            props[key] = getattr(self.format_props, key)
        props["filepath"] = self.filepath
        
        op(**props)
        
        bpy.ops.ed.undo()
        
        return {'FINISHED'}
    
    def iter_prop_names(self):
        # TODO: ignore_hidden (for uilayout drawing)?
        for key in dir(CurrentFormatProperties):
            if key.startswith("_"):
                continue
            value = getattr(CurrentFormatProperties, key)
            if isinstance(value, tuple):
                yield key
    
    def draw(self, context):
        category_name, op_name = self.format.split(".")
        category = getattr(bpy.ops, category_name)
        op = getattr(category, op_name)
        
        inst = op.get_instance()
        op_class = type(inst)
        
        layout = self.layout
        
        layout.label("Export " + self.visible_name)
        
        layout.prop(self, "include_children")
        
        layout.box()
        
        if 0:#hasattr(op_class, "draw"):
            self.format_props.layout = layout
            op_class.draw(self.format_props, context)
        else:
            for key in self.iter_prop_names():
                layout.prop(self.format_props, key)

class OBJECT_MT_selected_export(bpy.types.Menu):
    bl_idname = "OBJECT_MT_selected_export"
    bl_label = "Selected"
    
    def draw(self, context):
        layout = self.layout
        
        for op_name in dir(bpy.ops):
            op_category = getattr(bpy.ops, op_name)
            
            for name in dir(op_category):
                total_name = op_name + "." + name
                
                if total_name == ExportSelected.bl_idname:
                    continue
                
                if "export" in total_name:
                    op = getattr(op_category, name)
                    if not op.poll():
                        continue
                    
                    inst = op.get_instance()
                    op_class = type(inst)
                    
                    rna = op.get_rna()
                    
                    visible_name = rna.rna_type.name
                    if visible_name.lower().startswith("export "):
                        visible_name = visible_name[len("export "):]
                    
                    op_info = layout.operator(
                        ExportSelected.bl_idname,
                        text=visible_name,
                        )
                    op_info.format = total_name
                    op_info.visible_name = visible_name
                    
                    if hasattr(op_class, "filename_ext"):
                        op_info.filename_ext = op_class.filename_ext
                    elif total_name.endswith("collada_export"):
                        # Collada is built-in, so we have to
                        # fix this manually for now
                        op_info.filename_ext = ".dae"
                    
                    if hasattr(rna, "filter_glob"):
                        op_info.filter_glob = rna.filter_glob
                    elif total_name.endswith("collada_export"):
                        # Collada is built-in, so we have to
                        # fix this manually for now
                        op_info.filter_glob = "*.dae"

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.menu("OBJECT_MT_selected_export", text="Selected")


def register():
    bpy.utils.register_class(CurrentFormatProperties)
    bpy.utils.register_class(ExportSelected)
    bpy.utils.register_class(OBJECT_MT_selected_export)
    
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    
    bpy.utils.unregister_class(OBJECT_MT_selected_export)
    bpy.utils.unregister_class(ExportSelected)
    bpy.utils.unregister_class(CurrentFormatProperties)


if __name__ == "__main__":
    register()
