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

bpy_props = {
    bpy.props.BoolProperty,
    bpy.props.BoolVectorProperty,
    bpy.props.IntProperty,
    bpy.props.IntVectorProperty,
    bpy.props.FloatProperty,
    bpy.props.FloatVectorProperty,
    bpy.props.StringProperty,
    bpy.props.EnumProperty,
    bpy.props.PointerProperty,
    bpy.props.CollectionProperty,
}

join_before_export = {
    "export_mesh.ply",
}

def is_bpy_prop(value):
    if isinstance(value, tuple) and (len(value) == 2):
        if (value[0] in bpy_props) and isinstance(value[1], dict):
            return True
    return False

def iter_public_bpy_props(cls, exclude_hidden=False):
    #for key, value in cls.__dict__.items():
    for key in dir(cls):
        if key.startswith("_"):
            continue
        value = getattr(cls, key)
        if is_bpy_prop(value):
            if exclude_hidden:
                options = value[1].get("options", "")
                if 'HIDDEN' in options:
                    continue
            yield (key, value)

def get_op(idname):
    category_name, op_name = idname.split(".")
    category = getattr(bpy.ops, category_name)
    return getattr(category, op_name)

def iter_exporters():
    #categories = dir(bpy.ops)
    categories = ["export_anim", "export_mesh", "export_scene"]
    for category_name in categories:
        op_category = getattr(bpy.ops, category_name)
        
        for name in dir(op_category):
            total_name = category_name + "." + name
            
            if total_name == ExportSelected.bl_idname:
                continue
            
            if "export" in total_name:
                op = getattr(op_category, name)
                
                yield total_name, op

class CurrentFormatProperties(bpy.types.PropertyGroup):
    @classmethod
    def _clear_props(cls):
        keys_to_remove = list(cls._keys())
        
        for key in keys_to_remove:
            delattr(cls, key)
    
    @classmethod
    def _add_props(cls, template):
        for key, value in iter_public_bpy_props(template):
            setattr(cls, key, value)
    
    @classmethod
    def _keys(cls, exclude_hidden=False):
        for kv in iter_public_bpy_props(cls, exclude_hidden):
            yield kv[0]

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
        CurrentFormatProperties._clear_props()
        
        if self.format:
            op = get_op(self.format)
            op_class = type(op.get_instance())
            
            CurrentFormatProperties._add_props(op_class)
            
            if self.format == "wm.collada_export":
                # Special case: Collada (built-in) -- has no
                # explicitly defined Python properties
                CurrentFormatProperties.second_life = BoolProperty(
                    name="Export for Second Life",
                    description="Compatibility mode for Second Life",
                    default=False,
                    )
        else:
            self.visible_name = "Blend"
            self.filename_ext = ".blend"
            self.filter_glob = "*.blend"
        
        self.filepath = context.object.name + self.filename_ext
        return ExportHelper.invoke(self, context, event)
    
    def clear_world(self, context):
        message = "Killing everything but the Chosen Ones"
        if self.include_children:
            message += " and their children"
        bpy.ops.ed.undo_push(message=message)
        
        for scene in bpy.data.scenes:
            if scene != context.scene:
                bpy.data.scenes.remove(scene)
        
        objs = set()
        
        def add_obj(obj):
            objs.add(obj)
            if self.include_children:
                for child in obj.children:
                    add_obj(child)
        
        for obj in context.scene.objects:
            if obj.select:
                add_obj(obj)
        
        for obj in context.scene.objects:
            if obj not in objs:
                context.scene.objects.unlink(obj)
        context.scene.update()
        
        bpy.ops.object.select_all(action='SELECT')
        
        if self.format in join_before_export:
            bpy.ops.object.convert()
            bpy.ops.object.join()
    
    def execute(self, context):
        self.clear_world(context)
        
        if self.format:
            props = {}
            for key in CurrentFormatProperties._keys():
                props[key] = getattr(self.format_props, key)
            props["filepath"] = self.filepath
            
            op = get_op(self.format)
            
            op(**props)
        else:
            bpy.ops.wm.save_as_mainfile(
                filepath=self.filepath,
                copy=True,
            )
        
        bpy.ops.ed.undo()
        
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        
        layout.label("Export " + self.visible_name)
        
        layout.prop(self, "include_children")
        
        if not self.format:
            return
        
        layout.box()
        
        op = get_op(self.format)
        op_class = type(op.get_instance())
        
        if 0:#hasattr(op_class, "draw"):
            # Some bugs here
            self.format_props.layout = layout
            op_class.draw(self.format_props, context)
        else:
            for key in CurrentFormatProperties._keys(True):
                layout.prop(self.format_props, key)

class OBJECT_MT_selected_export(bpy.types.Menu):
    bl_idname = "OBJECT_MT_selected_export"
    bl_label = "Selected"
    
    def draw(self, context):
        layout = self.layout
        
        def def_op(visible_name, total_name="", layout=layout):
            if visible_name.lower().startswith("export "):
                visible_name = visible_name[len("export "):]
            
            if total_name:
                op = get_op(total_name)
                if not op.poll():
                    layout = layout.row()
                    layout.enabled = False
            
            op_info = layout.operator(
                ExportSelected.bl_idname,
                text=visible_name,
                )
            op_info.format = total_name
            op_info.visible_name = visible_name
            
            return op_info
        
        # Special case: export to .blend (the default)
        def_op("Blend")
        
        # Special case: Collada is built-in, resides
        # in an unconventional category, and has no
        # explicit ext/glob properties defined
        op_info = def_op("Collada", "wm.collada_export")
        op_info.filename_ext = ".dae"
        op_info.filter_glob = "*.dae"
        
        for total_name, op in iter_exporters():
            op_class = type(op.get_instance())
            rna = op.get_rna()
            
            op_info = def_op(rna.rna_type.name, total_name)
            
            if hasattr(op_class, "filename_ext"):
                op_info.filename_ext = op_class.filename_ext
            
            if hasattr(rna, "filter_glob"):
                op_info.filter_glob = rna.filter_glob

def menu_func_export(self, context):
    self.layout.menu("OBJECT_MT_selected_export", text="Selected")

def register():
    bpy.utils.register_class(CurrentFormatProperties)
    bpy.utils.register_class(ExportSelected)
    bpy.utils.register_class(OBJECT_MT_selected_export)
    bpy.types.INFO_MT_file_export.prepend(menu_func_export)

def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(OBJECT_MT_selected_export)
    bpy.utils.unregister_class(ExportSelected)
    bpy.utils.unregister_class(CurrentFormatProperties)

if __name__ == "__main__":
    register()
