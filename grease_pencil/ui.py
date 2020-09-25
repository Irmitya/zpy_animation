import bpy
from zpy import Is


def get_active(gpd):
    layers = gpd.layers
    if layers.active:
        layers = [layers.active]

    for layer in layers:
        for frame in layer.frames:
            for stroke in frame.strokes:
                return stroke.display_mode
    return "None"


def draw(self, context, space):
    layout = self.layout  # .column(align=True)

    layout.context_pointer_set('space', space)

    r1 = r2 = None
    if space.grease_pencil or Is.gpencil(context.object):
        row = layout.column(align=True)

        if space.grease_pencil:
            r1 = row.split(align=True, factor=0.60)
        if Is.gpencil(context.object):
            r2 = row.split(align=True, factor=0.60)

    if r1:
        gpd = space.grease_pencil
        r1.context_pointer_set('gpencil', gpd)
        r1.operator('zpy.gp_from_annotation', text="To Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')
        r1.operator_menu_enum('zpy.toggle_gp_space', 'space',
            text=get_active(gpd), icon='OUTLINER_DATA_GREASEPENCIL')

    if r2:
        gpd = context.object.data
        text = get_active(gpd)
        r2.context_pointer_set('gpencil', gpd)
        r2.operator('zpy.annotation_from_gp', text="From Grease Pencil", icon='OUTLINER_DATA_GREASEPENCIL')
        r2.operator_menu_enum('zpy.toggle_gp_space', 'space',
            text=get_active(gpd), icon='OBJECT_DATA')


def draw_scene(self, context):
    draw(self, context, context.scene)


def draw_space_data(self, context):
    draw(self, context, context.space_data)


def register():
    bpy.types.VIEW3D_PT_grease_pencil.append(draw_scene)
    bpy.types.SEQUENCER_PT_annotation.append(draw_space_data)


def unregister():
    bpy.types.SEQUENCER_PT_annotation.remove(draw_space_data)
    bpy.types.VIEW3D_PT_grease_pencil.remove(draw_scene)
