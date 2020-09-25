import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.types import Operator, Scene
from zpy import Get, Is, register_keymaps
km = register_keymaps()


class NAV_OT_keyframes(Operator):
    bl_description = "Jump to previous/next keyframe"
    bl_idname = 'zpy.keyframe_jump'
    bl_label = "Jump to Keyframe"
    bl_options = {'UNDO_GROUPED'}
    bl_undo_group = "Frame Change"

    # @classmethod
    # def poll(self, context):
        # return bpy.data.actions or bpy.data.grease_pencils

    def execute(self, context):
        # # Try to use the default keyframe jumper before running manual jump.
        # bpy.ops.screen.keyframe_jump(next=self.next)
        # if (scn.frame_current_final != frame):
        #     return {'FINISHED'}

        scn = context.scene
        sub = scn.show_subframe
        selected = Get.selected(context)

        frames = list()
        if context.area.type == 'SEQUENCE_EDITOR':
            frames = scan_sequence(context)
            frames = scan_annotations(context, frames, 'SEQUENCE_EDITOR')
        if not frames:
            frames = scan_actions(context, sub, selected)
            if not frames:
                frames = scan_strips(context, sub, selected)
            frames = scan_annotations(context, frames)

        # Go through list of frames insert numbers between the available frames
        if self.mid:
            pre = None
            mid_points = frames.copy()
            for f in mid_points:
                if pre is not None:
                    f_mid = pre + (f - pre) / 2
                    if not sub:
                        f_mid = round(f_mid)

                    if abs(f - f_mid) >= 1.0:
                        frames.append(f_mid)
                pre = f
            frames = sorted(set(frames))

        margin = 0.01
            # skip subframe if the difference between it
            # and the next frame is less than this margin of error

        # Find the next frame in line after the current frame
        fc = (int(scn.frame_current_final), scn.frame_current_final)[sub]
        if self.next:
            for fn in frames:
                if (fc < fn) and (abs(fc - fn) > margin) and (sub or (round(fn) != fc)):
                    break
            else:
                fn = None
        else:
            for fn in reversed(frames):
                if (fn < fc) and (abs(fn - fc) > margin) and (sub or (round(fn) != fc)):
                    break
            else:
                fn = None

        if fn is None:
            self.report({'INFO'}, "No more keyframes to jump to in this direction")
            return {'CANCELLED'}
            # return {'PASS_THROUGH'}

        fn = Get.frame_mapped(context, fn)
        frame = round(fn)
        subframe = abs(fn - frame)
        if (frame < 0 and subframe):
            # Negative numbers have to offset a little for frame_set
            frame -= 1
            subframe = 1 - subframe
        if not sub:
            subframe = 0

        # context.scene.frame_set(fn, subframe=subframe)
        context.scene.frame_current = fn
        context.scene.frame_subframe = subframe

        return {'FINISHED'}

    next: BoolProperty(
        name="Next Keyframe",
        default=True,
        options={'HIDDEN'},
    )
    mid: BoolProperty(
        name="Mid Points",
        default=False,
        options={'SKIP_SAVE'},
    )


def pose(context):
    return context.mode == 'POSE'


def smooth(num):
    return round(num, 3)


def scan_actions(context, sub, selected):
    scn = context.scene
    fc = (int(scn.frame_current_final), scn.frame_current_final)[sub]
    frames = list()

    for obj in selected:
        if Is.gpencil(obj):
            for layer in obj.data.layers:
                for frame in layer.frames:
                    frames.append(frame.frame_number)

    for obj in Get.objects_nla(context):
        # Poll object
        if pose(context):
            if not pose(obj):
                continue
            elif selected:
                bones = [f'pose.bones[\"{b.name}\"]'
                    for b in Get.selected_pose_bones(context, src=obj)]
                if not bones:
                    continue
            else:
                bones = list()
        else:
            if (selected and obj not in selected):
                continue
            else:
                bones = list()

        for anim in Get.animation_datas(obj):
            if (not anim.action):
                continue
            if anim.use_tweak_mode:
                for s in Get.strips(anim.id_data):
                    if s.action == anim.action:
                        strip = s
                        if s.active: break

                # Get loop ends
                cycle = list()
                afe = strip.action_frame_end
                fel = fer = Get.frame_from_strip(context, strip, afe)
                while fel < strip.frame_end:
                    offset = (fer - strip.frame_start)
                    cycle.append(offset)
                    fel += abs(offset)
                    # If offset becomes negative, it "should" create an infinite loop
                    # abs() forces positive, which "should" prevent loop
            else:
                strip = None

            for fcurve in anim.action.fcurves:
                path = fcurve.data_path
                if bones:
                    # Bones are selected, so verify this fcurve if for one of them
                    for bpath in bones:
                        if path.startswith(bpath):
                            break
                    else:
                        continue
                elif path.startswith('pose.bones[\"'):
                    try:
                        eval(repr(obj) + '.' + path)  # Validate path
                        bpath = path.split('\"]', 1)[0] + '\"]'
                        bone = eval(repr(obj) + '.' + bpath)
                        if not Is.visible(context, bone):
                            continue
                    except:
                        # curve points to a removed bone or something
                        continue

                scan_fcurve(context, sub, fcurve, frames, strip=strip)

    return sorted(set(frames))


def scan_annotations(context, frames, area_type=None):
    types = context.scene.keyframe_navigation_types

    if area_type == 'SEQUENCE_EDITOR':
        gp = context.space_data.grease_pencil
    else:
        # Assume View_3D
        gp = context.scene.grease_pencil

    if gp:
        for layer in gp.layers:
            if layer.annotation_hide and ('HIDDEN' not in types):
                continue
            for frame in layer.frames:
                if (frame.keyframe_type not in types):
                    continue
                frames.append(frame.frame_number)

    return sorted(set(frames))


def scan_sequence(context):
    frames = list()

    selected = [seq for seq in context.sequences if seq.select]
    anim = context.scene.animation_data
    if anim and anim.action:
        for fc in anim.action.fcurves:
            if fc.data_path.startswith('sequence_editor.sequences_all'):
                name = fc.data_path.split('["', 1)[1].split('"]', 1)[0]
                seq = context.scene.sequence_editor.sequences_all.get(name)
                if not seq:
                    continue

                if (not selected) or (seq in selected):
                    for key in fc.keyframe_points:
                        frames.append(key.co.x)

    if not frames:
        for seq in context.sequences:
            if selected:
                if seq not in selected:
                    continue
            elif seq.mute:
                continue

            frames.append(seq.frame_final_start)
            frames.append(seq.frame_final_end - 1)

    return sorted(set(frames))


def scan_strips(context, sub, selected):
    frames = list()
    for obj in Get.objects_nla(context):
        data = getattr(obj, 'data', None)
        shapes = getattr(data, 'shape_keys', None)

        # Poll object
        if pose(context):
            if not pose(obj):
                continue
            elif selected:
                if not Get.selected_pose_bones(context, src=obj):
                    continue
        else:
            if (selected and obj not in selected):
                continue

        for src in (obj, data, shapes):
            frames_fcurve = list()
            frames_strip = list()
            for item in Get.strip_tracks(src, selected=False):
                strip = item.strip

                if strip.mute and not strip.select:
                    continue

                for fc in strip.fcurves:
                    if fc.hide:
                        continue
                    scan_fcurve(context, sub, fc, frames_fcurve)

                if frames_fcurve:
                    # Don't scan strip boxes if have animation keyframes
                    continue

                (fs, fe) = (strip.frame_start, strip.frame_end)
                if not sub:
                    (fs, fe) = (smooth(fs), smooth(fe))
                frames_strip.append(fs)
                frames_strip.append(fe)

                # Get loop ends
                if (strip.action) and (strip.repeat != 1.0):
                    afe = strip.action_frame_end
                    fel = fer = Get.frame_from_strip(context, strip, afe)
                    while fel < strip.frame_end:
                        frames_strip.append([smooth(fel), fel][sub])
                        fel += (fer - strip.frame_start)

            if frames_fcurve:
                frames.extend(frames_fcurve)
            else:
                frames.extend(frames_strip)

    return sorted(set(frames))


def scan_fcurve(context, sub, fcurve, frames=list(), strip=None):
    scn = context.scene
    fc = (int(scn.frame_current_final), scn.frame_current_final)[sub]
    if not fcurve.keyframe_points:
        return frames

    types = scn.keyframe_navigation_types
    (first_key, last_key) = (fcurve.keyframe_points[0], fcurve.keyframe_points[-1])

    if ('HIDDEN' not in types) and fcurve.hide:
        return frames

    keyframes = list()
    for key in fcurve.keyframe_points:
        if (key.type not in types):  # and key not in (first_key, last_key):
            continue
        co = key.co[0]
        # cycos = list()
        if strip:
            co = Get.frame_from_strip(context, strip, frame=co)
            # for (x, loco) in enumerate(cycle):
            #     cyco = co + x * loco
            #     cycos.append(cyco)
            # if cycle and (strip.repeat % 1):  # has decimal
            #     cycos.append(cyco + loco)

        keyframes.append(co)

        # for cyco in cycos:
        #     if not sub: cyco = smooth(cyco)
        #     frames.append(cyco)

    for co in keyframes:
        if not sub: co = smooth(co)
        frames.append(co)

    use_cycles = scn.tool_settings.use_keyframe_cycle_aware
    for mod in fcurve.modifiers:
        if (mod.type == 'CYCLES') and use_cycles:
            (fs, fe) = (keyframes[0], keyframes[-1])
            if abs(fs - fe) < 1:
                continue
            cycos = list()

            offset = (fe - fs)

            loops = list()
            if fe <= fc:
                fel = fe
                while fel <= fc:
                    loops.append(1)
                    fel += offset
            elif fc <= fs:
                fsl = fs
                while fc <= fsl:
                    loops.append(-1)
                    fsl -= offset

            for (x, fl) in enumerate(loops):
                for co in keyframes:
                    co += ((x + 1) * (offset * fl))

                    if not sub: co = smooth(co)
                    frames.append(co)

    return frames


keyframe_navigation_types = EnumProperty(
    items=[
        ('KEYFRAME', "Keyframe", "Normal keyframe - e.g. for key poses", 'KEYTYPE_KEYFRAME_VEC', 2),
        ('BREAKDOWN', "Breakdown", "A breakdown pose - e.g. for transitions between key poses", 'KEYTYPE_BREAKDOWN_VEC', 4),
        ('MOVING_HOLD', "Moving Hold", "A keyframe that is part of a moving hold", 'KEYTYPE_MOVING_HOLD_VEC', 8),
        ('EXTREME', "Extreme", "An 'extreme' pose, or some other purpose as needed", 'KEYTYPE_EXTREME_VEC', 16),
        ('JITTER', "Jitter", "A filler or baked keyframe for keying on ones, or some other purpose as needed", 'KEYTYPE_JITTER_VEC', 32),
        ('HIDDEN', "Hidden", "Consider hidden fcurves for keyframe navigation", 'HIDE_OFF', 64),
    ],
    name="Type",
    description="Which key types to consider when jumping to keyframes",
    options={'ENUM_FLAG'},
    default={'KEYFRAME', 'BREAKDOWN', 'MOVING_HOLD', 'EXTREME', 'JITTER'},
)


def draw(self, context):
    layout = self.layout.column(align=True)

    row = layout.row(align=True)
    row.alignment = 'LEFT'
    op = row.operator('zpy.keyframe_jump', text="", icon='PREV_KEYFRAME')
    op.next = False
    op.mid = True
    row.label(text="Keyframe Navigation Types:")
    op = row.operator('zpy.keyframe_jump', text="", icon='NEXT_KEYFRAME')
    op.next = True
    op.mid = True

    row = layout.grid_flow(align=True)
    row.operator('zpy.keyframe_jump', text="", icon='REW').next = False
    row.prop(context.scene, 'keyframe_navigation_types', text="")
    row.operator('zpy.keyframe_jump', text="", icon='FF').next = True


# editors = (
#     'DOPESHEET_MT_editor_menus',
#     'GRAPH_MT_editor_menus',
#     'TIME_MT_editor_menus',
# )


# timer = 50
# use_breakdown = False


# @bpy.app.handlers.persistent
# def add_to_breakdown(scn=None):
    # global timer, use_breakdown

    # timer -= 1
    # if not hasattr(bpy.types, 'BREAK_PT_props'):
    #     if timer >= 0:
    #         return 0.0  # loop
    #     else:
    #         for menu in editors:
    #             eval('bpy.types.' + menu).append(draw)
    # else:
    #     if not use_breakdown:
    #         bpy.types.BREAK_PT_props.prepend(draw)
    #     use_breakdown = True

    # return  # exit


def register():
    # bpy.app.timers.register(add_to_breakdown, persistent=True)
    Scene.keyframe_navigation_types = keyframe_navigation_types

    # Keyframes
    op = NAV_OT_keyframes
    args = dict(idname=NAV_OT_keyframes, name='Frames', value='PRESS', shift=True)
    km.add(type='BUTTON5MOUSE', **args, next=True)
    km.add(type='BUTTON4MOUSE', **args, next=False)

    args['ctrl'], args['mid'] = True, True
    km.add(type='BUTTON5MOUSE', **args, next=True)
    km.add(type='BUTTON4MOUSE', **args, next=False)


def unregister():
    # if use_breakdown:
    #     bpy.types.BREAK_PT_props.remove(draw)
    # else:
    #     for menu in editors:
    #         eval('bpy.types.' + menu).remove(draw)

    km.remove()
    del Scene.keyframe_navigation_types
