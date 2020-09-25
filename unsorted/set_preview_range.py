from zpy import register_keymaps, Get, utils
import bpy
km = register_keymaps()


class OPERATOR_OT_set_preview_range(bpy.types.Operator):
    bl_description = "Interactively define frame range used for playback"
    bl_idname = 'zpy.set_preview_range'
    bl_label = "Set Preview Range"

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):

        if context.scene.use_preview_range:
            return bpy.ops.anim.previewrange_clear()
        else:
            sp = context.space_data

            if sp.type == 'DOPESHEET_EDITOR':
                return bpy.ops.action.previewrange_set()
            elif sp.type == 'GRAPH_EDITOR':
                return bpy.ops.graph.previewrange_set()
            elif sp.type == 'NLA_EDITOR':
                return self.preview_nla(context)
            elif sp.type == 'SEQUENCE_EDITOR':
                return bpy.ops.sequencer.set_range_to_strips(preview=True)
            else:
                self.report({'INFO'}, "Couldn't find space to set preview")
                return {'CANCELLED'}

    def preview_nla(self, context):
        scn = context.scene
        start = end = None

        # Set preview range using snapping (from frame_step operator)
        prefs = scn.step_frames
        stepped = prefs.on_steps
        frame_step = prefs.frame_step

        strips_nla = Get.strips_nla(context)

        for (obj, strips) in strips_nla:
            for item in strips:
                strip = item.strip

            # Scale update start value
                frame_start = int(strip.frame_start)
                if stepped:
                    while (frame_start % frame_step):
                        frame_start -= 1
                if (start is None) or (frame_start < start):
                    start = frame_start

            # Get used frame range from repeat
                # if (strip.repeat != 1.0):
                #     fs = strip.frame_start
                #     fe = strip.frame_end
                #     fe2 = scale_range(fe, fs, fe, 0, abs(fs - fe))
                #     frame_end = int((1 / strip.repeat) * fe2 + fs)
                # else:
                #     frame_end = int(strip.frame_end)
                if self.repeat:
                    afe = strip.action_frame_end
                    frame_end = Get.frame_from_strip(context, strip, afe)
                else:
                    frame_end = strip.frame_end
                frame_end = round(frame_end, 4)

            # Update end value
                if stepped:
                    while (frame_end % frame_step):
                        frame_end += 1
                if (strip.repeat > 1.0) and self.repeat:
                    # Don't let loops end on the first frame
                    frame_end -= 1
                if (end is None) or (end < frame_end):
                    end = frame_end

        if (None not in {start, end}):
            scn.use_preview_range = True
            scn.frame_preview_end = end
            scn.frame_preview_start = start
            return {'FINISHED'}
        else:
            if strips_nla:
                self.report({'WARNING'}, "Couldn't set preview; using default")
            return bpy.ops.nla.previewrange_set()

    repeat: bpy.props.BoolProperty(
        name="Use Loops",
        description="Evaluate automated loops for the frame range",
        default=False,
        options={'SKIP_SAVE'},
    )


def register():
    # Preview Range (toggle)
    op = OPERATOR_OT_set_preview_range
    args = dict(idname=op, type='F15', value='PRESS', repeat=False)
    km.add(name='Dopesheet', **args)
    km.add(name='Graph Editor', **args)
    km.add(name='NLA Editor', **args)
    km.add(name='Sequencer', **args)

    args = dict(idname=op, type='F15', value='PRESS', any=True, repeat=True)
    km.add(name='Dopesheet', **args)
    km.add(name='Graph Editor', **args)
    km.add(name='NLA Editor', **args)
    km.add(name='Sequencer', **args)


def unregister():
    km.remove()
