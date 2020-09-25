import bpy
from bpy.props import BoolProperty
from zpy import register_keymaps
km = register_keymaps()


class MARKER_OT_frame_jump(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'zpy.marker_jump'
    bl_label = "Jump to Markers"
    bl_options = {'UNDO_GROUPED', 'INTERNAL'}

    @classmethod
    def poll(self, context):
        return context.scene.timeline_markers

    def execute(self, context):
        scn = context.scene
        new_frame = frame = scn.frame_current

        previous = []
        current = []
        next = []
        for m in scn.timeline_markers:
            mframe = m.frame
            if mframe < frame:
                previous.append(mframe)
            if mframe > frame:
                next.append(mframe)
            if mframe == frame:
                current.append(mframe)
        previous = list(set(previous))
        previous.sort()
        current = list(set(current))
        current.sort()
        next = list(set(next))
        next.sort()

        if (self.next and not next) or (not self.next and not previous):
            self.report({'INFO'}, "No more markers to jump to in this direction")
            return {'CANCELLED'}
            # return {'PASS_THROUGH'}

        if self.next:
            if self.keys_only:
                new_frame = next[0]
            else:
                if current:
                    new_frame = frame + round((next[0] - frame) / 2)
                elif previous:
                    new_frame = previous[-1] + round((next[0] - previous[-1]) / 2)
                if new_frame == frame:
                    new_frame = next[0]
        else:
            if self.keys_only:
                new_frame = previous[-1]
            else:
                if current:
                    new_frame = previous[-1] + round((frame - previous[-1]) / 2)
                elif next:
                    new_frame = previous[-1] + round((next[0] - previous[-1]) / 2)
                if new_frame == frame:
                    new_frame = previous[-1]

        scn.frame_current = new_frame
        scn.frame_subframe = 0

        return {'FINISHED'}

    next: BoolProperty(
        name="Next Marker",
        description="Go forward in timeline (right) or go backward (left)",
        default=False,
    )
    keys_only: BoolProperty(default=False, name='Only on Markers')


def register():
    # Jump to Markers
    args = dict(idname=MARKER_OT_frame_jump, name='Frames', value='PRESS', shift=True)
    km.add(**args, type='F13', ctrl=False, keys_only=True, next=False)
    km.add(**args, type='F13', ctrl=True, keys_only=False, next=False)
    km.add(**args, type='F14', ctrl=False, keys_only=True, next=True)
    km.add(**args, type='F14', ctrl=True, keys_only=False, next=True)


def unregister():
    km.remove()
