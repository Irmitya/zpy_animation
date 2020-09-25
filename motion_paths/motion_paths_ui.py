import bpy
from zpy import Get, Is, utils


def draw_header(self, context):
    layout = self.layout

    prefs = utils.prefs(__package__).motion

    if context.mode == 'POSE':
        src = context.active_pose_bone
    else:
        src = context.object

    if not src:
        return

    layout.separator()
    sub = layout.row()
    sub.emboss = ('PULLDOWN_MENU', 'NORMAL')[prefs.show_panel]
    sub.active = prefs.show_panel
    sub.prop(prefs, 'show_panel', text="", icon='CURVE_DATA')

    if not prefs.show_panel:
        return

    if Is.posebone(src):
        mp = src.id_data.pose.animation_visualization.motion_path
    else:
        mp = src.animation_visualization.motion_path

    if mp.type == 'CURRENT_FRAME':
        mp_text = "Around Frame"
        mp_icon = 'PREVIEW_RANGE'
        mp_start = 'frame_before'
        mp_end = 'frame_after'
        mp_type = 'RANGE'  # value to toggle to
    else:  # mp.type == 'RANGE':
        mp_icon = 'TIME'
        mp_text = "      In Range   "
        mp_start = 'frame_start'
        mp_end = 'frame_end'
        mp_type = 'CURRENT_FRAME'  # value to toggle to

    row = layout.row(align=True)
    row.context_pointer_set('src', src)
    row.context_pointer_set('mp', mp)

    row.menu('MOTIONP_MT_subpanel', text="", icon='THREE_DOTS')

    sub = row.row(align=True)
    sub.scale_x = 0.6
    sub.prop(mp, mp_start, text="")
    row.operator('zpy.motion_path_toggle_type', text=mp_text, icon=mp_icon,
    depress=False).type = mp_type

    sub = row.row()
    sub.scale_x = 0.6
    sub.prop(mp, mp_end, text="")

    # prefs.operator(row, 'toggle mp relative range', text="",
        #            icon=('TIME', 'PREVIEW_RANGE')
        #            [prefs.prefs().motion.use_relative_range],
        #            emboss=True, depress=False, code='''
        # mot = prefs.prefs().motion
        # mot.use_relative_range = not mot.use_relative_range
    sub = row.row()
    sub.emboss = 'PULLDOWN_MENU'

    if prefs.use_relative_range:
        text = "Around"
        icon = 'PREVIEW_RANGE'
    else:
        text = "Range"
        icon = 'TIME'
    sub.prop(prefs, 'use_relative_range', text=text, icon=icon, icon_only=True)

    mpath = src.motion_path
    if mpath:
        sub = row.row(align=True)
        # sub.scale_x = 0.5
        if mpath.use_custom_color:
            sub.prop(mpath, 'color', icon_only=True)
        else:
            sub.active = False
            sub.prop(mpath, 'use_custom_color', icon_only=True,
                        icon='COLORSET_20_VEC')
        sub = row.row(align=True)
        sub.scale_x = 0.5
        sub.prop(mpath, 'line_thickness', icon_only=True, slider=True)

    if mp.has_motion_paths:
        if context.mode == 'POSE':
            clear = 'pose.paths_clear'
        else:
            clear = 'object.paths_clear'

        row.operator(clear, text="", icon='PANEL_CLOSE')


class MOTIONP_MT_subpanel(bpy.types.Menu):
    bl_description = ""
    bl_label = ""

    @classmethod
    def poll(self, context):
        return hasattr(context, 'src') and hasattr(context, 'mp')

    def draw(self, context):
        layout = self.layout
        src = context.src
        mp = context.mp
        mpath = src.motion_path

        layout.prop(mp, 'show_frame_numbers')  # , text="Frame Numbers")
        layout.prop(mp, 'show_keyframe_highlight')  # , text="Keyframes")
        if mp.show_keyframe_highlight:
            if Is.posebone(src):
                layout.prop(mp, 'show_keyframe_action_all',
                            text="+ Non-Grouped Keyframes")
            layout.prop(mp, 'show_keyframe_numbers', text="Keyframe Numbers")

        layout.separator()
        if Is.posebone(src):
            layout.label(text=src.name, icon='BONE_DATA')
        else:
            layout.label(text=src.name, icon='OBJECT_DATA')
        if mpath:
            layout.prop(mpath, 'lines')  # , text="Lines")
            layout.prop(mpath, 'use_custom_color')  # , text="Custom Color")
        else:
            op = 'zpy.update_motion_paths'
            layout.label(text="Add Motion Paths")
            layout.operator(op, text="At Heads").use_tails = False
            layout.operator(op, text="At Tails").use_tails = True

        layout.separator()
        mot = utils.prefs(__package__).motion
        layout.prop(mot, 'frame_before')
        layout.prop(mot, 'frame_after')


def register():
    bpy.types.TOPBAR_MT_editor_menus.append(draw_header)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_header)
