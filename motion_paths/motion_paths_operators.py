import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator
from zpy import register_keymaps, Get, Set, Is, utils
km = register_keymaps()


class MOTION_OT_make_paths(Operator):
    bl_description = "Calculate/Update motion paths for the selected"
    bl_idname = 'zpy.update_motion_paths'
    bl_label = "Recalculate Motion Paths"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.mode == 'POSE':
            return Get.selected_pose_bones(context)
        if context.mode == 'OBJECT':
            return Get.selected_objects(context)

    def execute(self, context):
        scn = context.scene
        active = Get.active(context)
        selected = Get.selected(context)
        is_pose = bool(context.mode == 'POSE')

        if not is_pose:
            self.use_tails = False
        mode = ('HEADS', 'TAILS')[self.use_tails]

        # Use the line thickness of the active item, across the selection
        if getattr(active, 'motion_path', None):
            line = active.motion_path.line_thickness
        else:
            line = 1

        colors = dict()
        types = dict()
        for src in Get.selected(context):
            mp = src.motion_path
            if not mp:
                continue

            if mp.use_custom_color:
                colors[src] = mp.color

            if Is.posebone(src):
                display = src.id_data.pose.animation_visualization.motion_path
            else:
                display = src.animation_visualization.motion_path

            types[src] = display.type

        # Get the frame range to bake motion paths in
        motion = utils.prefs(__package__).motion

        if self.use_start_end:
            start = self.start_frame
            end = self.end_frame
        elif (motion.use_relative_range) or (scn.use_preview_range):
            start = scn.frame_preview_start
            end = scn.frame_preview_end
            fc = scn.frame_current
            fb = motion.frame_before
            fa = motion.frame_after

            if not (scn.use_preview_range) or (
            abs(end - start) > 100 > (fb + fa)):
                # If the preview range is too high, just default to nearby
                start = fc - fb
                end = fc + fa
        else:
            # if (active):
                # # Use the active object's motion path's in_range distance
                # if (Is.posebone(active)):
                #     mp = active.id_data.pose.animation_visualization.motion_path
                # else:
                #     mp = active.animation_visualization.motion_path
                # fb = mp.frame_before
                # fa = mp.frame_after
                # if (fb < 25): fb = 25
                # if (fa < 25): fa = 25

                # start = scn.frame_current - fb
                # end = scn.frame_current + fa
            start = scn.frame_start
            end = scn.frame_end
            fc = scn.frame_current
            if 150 < abs(end - start):
                start = fc - 50
                end = fc + 50

        # Create the motion paths
        args = dict(start_frame=start, end_frame=end + 1)
        if is_pose:
            op = bpy.ops.pose
            args['bake_location'] = mode

            # Operator only runs on active rig, so repeat for all in pose mode
            obs = {b.id_data for b in selected}

            for ob in obs:
                Set.active(context, ob)
                op.paths_clear(only_selected=True)
                op.paths_calculate(**args)
            else:
                Set.active(context, active)
        else:
            op = bpy.ops.object
            op.paths_clear(only_selected=True)
            op.paths_calculate(**args)

        for src in selected:
            mp = src.motion_path
            if not mp: continue

            mp.line_thickness = line
            color = colors.get(src)
            if color:
                mp.color = color

            if Is.posebone(src):
                display = src.id_data.pose.animation_visualization.motion_path
            else:
                display = src.animation_visualization.motion_path
            display.type = types.get(src, 'CURRENT_FRAME')

        # Set to use the frame hider instead of ever displaying all points
            # if is_pose:
            #     src.id_data.pose.animation_visualization. \
            #         motion_path.type = 'CURRENT_FRAME'
            # else:
            #     src.animation_visualization. \
            #         motion_path.type = 'CURRENT_FRAME'
        # scn.frame_set(scn.frame_current)

        return {'FINISHED'}

    use_tails: BoolProperty(
        name='Use Tails',
        description="Calculate bone paths from tails",
    )
    use_start_end: BoolProperty(
        name='Use Start/End',
        description="Use manually set start and end frame numbers",
        options={'SKIP_SAVE'},
    )
    start_frame: IntProperty(
        name="Start",
        description="Frame Start",
        default=1,
        soft_min=0,
    )
    end_frame: IntProperty(
        name="End",
        description="Frame End",
        default=250,
        soft_min=0,
    )


class MOTION_OT_clear_paths(Operator):
    bl_description = "Remove motion paths for the selected"
    bl_idname = 'zpy.clear_motion_paths'
    bl_label = "Clear Motion Paths"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.mode in {'POSE', 'OBJECT'}

    def execute(self, context):
        active = Get.active(context)
        active_select = Is.selected(active)
        selected = Get.selected(context)
        is_pose = bool(context.mode == 'POSE')
        arg = dict(only_selected=bool(selected))

        if is_pose:
            clear = bpy.ops.pose.paths_clear

            # Operator only runs on active rig, so repeat for all in pose mode
            if selected:
                obs = {b.id_data for b in selected}
            else:
                obs = {ob for ob in Get.objects(context) if ob.mode == 'POSE'}

            for ob in obs:
                Set.active(context, ob)
                clear(**arg)
            else:
                Set.active(context, active)
                Set.select(active, active_select)
        elif bpy.ops.object.paths_clear.poll(context.copy()):
            bpy.ops.object.paths_clear(**arg)

        return {'FINISHED'}


class MOTION_OT_toggle(Operator):
    bl_description = ""
    bl_idname = 'zpy.motion_path_toggle_type'
    bl_label = ""

    def execute(self, context):
        selection = Get.selected(context)

        if not selection:
            selection = [Get.active(context)]

        for src in selection:
            if Is.posebone(src):
                mp = src.id_data.pose.animation_visualization.motion_path
            else:
                mp = src.animation_visualization.motion_path
            mp.type = self.type

        return {'FINISHED'}

    type: EnumProperty(
        items=[
            ('RANGE', "Range", ""),
            ('CURRENT_FRAME', "Current Frame", ""),
        ],
        name="",
        description="",
    )


def register():
    args = dict(name='3D View', value='PRESS')
    km.add(MOTION_OT_make_paths, **args, type='F16', use_tails=False)
    km.add(MOTION_OT_make_paths, **args, type='F17', use_tails=True)
    km.add(MOTION_OT_clear_paths, **args, type='F15')


def unregister():
    km.remove()
