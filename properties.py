import bpy
from bpy.props import IntProperty, BoolProperty
from zpy import utils


class Animation(bpy.types.AddonPreferences, utils.Preferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        self.draw_keymaps(context)

        # row = layout.row(align=True)
        # row.active = self.on_steps
        # row.prop(self, 'on_steps', icon=('IPO_CONSTANT'), icon_only=True)

        # sub = row.row(align=True)
        # sub.scale_x = 0.75
        # sub.prop(self, 'frame_step', icon_only=True)


    class motion(bpy.types.PropertyGroup):
        use_relative_range: BoolProperty(
            name="Bake Using Relative Frame Range",
            description="Bake frames using range relative to current frame",
            default=True, options={'SKIP_SAVE'},
        )
        frame_before: IntProperty(
            name="Frame Range Before",
            description="Number of frames to bake before the current frame",
            default=50, min=1, soft_max=250, options={'SKIP_SAVE'},
        )
        frame_after: IntProperty(
            name="Frame Range After",
            description="Number of frames to bake after the current frame",
            default=50, min=1, soft_max=250, options={'SKIP_SAVE'},
        )
        show_panel: BoolProperty()
    motion: utils.register_pointer(motion)


class step_frames(bpy.types.PropertyGroup):
    frame_step: IntProperty(name="Frame Step", default=2, min=1)
    on_steps: BoolProperty(name="On Steps", default=False)


def register():
    bpy.types.Scene.step_frames = utils.register_pointer(step_frames)


def unregister():
    del bpy.types.Scene.step_frames
