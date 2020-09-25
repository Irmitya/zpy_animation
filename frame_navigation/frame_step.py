import bpy
from zpy import utils, register_keymaps
km = register_keymaps()


class NAV_OT_frame(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'zpy.step_frame_change'
    bl_label = "Stepped Frame Change"
    # Disable undo to run faster
    # bl_options = {'UNDO_GROUPED'}
    # bl_undo_group = "Frame Change"

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        scn = context.scene

        start = scn.frame_start
        frame = scn.frame_current
        frame_step = (scn.step_frames.frame_step) * (self.factor)

        if scn.step_frames.on_steps:
            if start > 0:
                frame -= start
            else:
                frame += start

            if not abs((frame + start) - scn.frame_current):
                frame += (1, -1)[self.backwards]
            while (frame % frame_step):
                frame += (1, -1)[self.backwards]
            step = abs((frame + start) - scn.frame_current)
        else:
            step = frame_step

        if self.backwards:
            scn.frame_current -= step
            # bpy.ops.screen.frame_offset(delta=step * -1)
        else:
            scn.frame_current += step
            # bpy.ops.screen.frame_offset(delta=step)

        return {'FINISHED'}

    backwards: bpy.props.BoolProperty()
    factor: bpy.props.IntProperty(options={'SKIP_SAVE'}, min=1)


def register():
    # Frame Offset
    args = dict(idname=NAV_OT_frame, name='Frames', value='PRESS', factor=1)
    km.add(type='BUTTON5MOUSE', **args, backwards=False)
    km.add(type='BUTTON4MOUSE', **args, backwards=True)

    args['factor'] = 5
    km.add(type='BUTTON5MOUSE', **args, backwards=False, alt=True)
    km.add(type='BUTTON4MOUSE', **args, backwards=True, alt=True)

    args['factor'] = 10
    km.add(type='BUTTON5MOUSE', **args, backwards=False, ctrl=True)
    km.add(type='BUTTON4MOUSE', **args, backwards=True, ctrl=True)

    args['factor'] = 15
    km.add(type='BUTTON5MOUSE', **args, backwards=False, ctrl=True, alt=True)
    km.add(type='BUTTON4MOUSE', **args, backwards=True, ctrl=True, alt=True)


def unregister():
    km.remove()
