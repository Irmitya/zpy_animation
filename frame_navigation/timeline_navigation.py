import bpy
from zpy import register_keymaps
km = register_keymaps()


class NAV_OT_frame_offset(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'zpy.step_frame_offset'
    bl_label = "Frame Offset"
    # Disable undo to run faster
    # bl_options = {'UNDO_GROUPED'}
    # bl_undo_group = "Frame Change"

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.scene.frame_current += self.delta
        return {'FINISHED'}

    delta: bpy.props.IntProperty()


def register():
    # Frames
    # args = dict(idname='screen.frame_offset',
    args = dict(idname=NAV_OT_frame_offset,
                name='Frames', value='PRESS', alt=True)
    km.add(**args, type='WHEELDOWNMOUSE', delta=1)
    km.add(**args, type='WHEELUPMOUSE', delta=-1)

    # Timeline >> Start/End
    args = dict(name='Frames', value='PRESS')
    km.add('screen.frame_jump', **args, type='F18', end=False)
    km.add('anim.start_frame_set', **args, type='Q', shift=True)
    km.add('anim.end_frame_set', **args, type='W', shift=True)
    km.add('screen.frame_jump', **args, type='F19', end=True)

    # 2.8 hotkeys to 2.7
    # # Animation Playback
    # km.add('screen.animation_play', name='Frames', type='SPACE', value='PRESS')
    # km.add('screen.animation_play', name='Frames', type='SPACE', shift=True, ctrl=True, value='PRESS', properties={'reverse': True})
    # km.toggle('screen.animation_play', name='Frames', type='A', alt=True, value='PRESS')
    # km.toggle('screen.animation_play', name='Frames', type='A', shift=True, alt=True, value='PRESS')

    # # Dynamic Spacebar
    # km.toggle('wm.call_menu', name='3D View', type='SPACE', value='PRESS', addon=True)  # currently added twice
    # km.toggle('wm.search_menu', name='Window', type='SPACE', value='PRESS')


def unregister():
    km.remove()
