import bpy


def draw_header(self, context):
    layout = self.layout
    steps = context.scene.step_frames

    row = layout.row(align=True)
    row.emboss = 'PULLDOWN_MENU'

    row.active = steps.on_steps
    row.prop(steps, 'on_steps', icon='IPO_CONSTANT', icon_only=True)

    sub = row.row(align=True)
    sub.scale_x = 0.75
    sub.prop(steps, 'frame_step', icon_only=True)


editors = (
    # 'DOPESHEET_MT_editor_menus',
    # 'GRAPH_MT_editor_menus',
    # 'TIME_MT_editor_menus',
    # 'NLA_MT_editor_menus',
    # 'VIEW3D_MT_editor_menus',
    'TOPBAR_MT_editor_menus',
    # 'TOPBAR_HT_upper_bar',
)


def register():
    for e in editors:
        eval('bpy.types.' + e).append(draw_header)


def unregister():
    for e in editors:
        eval('bpy.types.' + e).remove(draw_header)
