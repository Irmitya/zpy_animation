import bpy
from zpy import Is


class GP_OT_toggle_space(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'zpy.toggle_gp_space'
    bl_label = "Toggle Space"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'gpencil')

    def execute(self, context):
        layers = context.gpencil.layers
        if layers.active:
            layers = [layers.active]

        for layer in layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    stroke.display_mode = self.space

        return {'FINISHED'}

    space: bpy.props.EnumProperty(
        items=[
            ('3DSPACE', "3D Space", ""),
            ('2DSPACE', "2D Space", ""),
            ('2DIMAGE', "2D Image", ""),
            ('SCREEN', "Screen", ""),
        ],
        default='3DSPACE',
        name="",
        description="",
    )


# def draw(self, context):
    # layout = self.layout
    # layout.operator_menu_enum('zpy.toggle_gp_space', 'space', text="", icon='NONE')


# def register():
    # bpy.types.DATA_PT_gpencil_strokes.append(draw)


# def unregister():
    # bpy.types.DATA_PT_gpencil_strokes.remove(draw)
