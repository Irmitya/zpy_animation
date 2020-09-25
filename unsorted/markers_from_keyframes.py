import bpy
from zpy import utils


class MARKER_OT_from_selected_keyframes(bpy.types.Operator):
    bl_description = "Insert new markers on the frames on the selected keyframes"
    bl_idname = 'zpy.markers_from_selected_keyframes'
    bl_label = "Markers from Selected Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    def execute(self, context):
        utils.update_keyframe_points(context)

        frames = set()
        markers = context.scene.timeline_markers

        for fc in context.editable_fcurves:
            for key in fc.keyframe_points:
                if key.select_control_point:
                    frames.add(int(key.co[0]))
        # TODO: calculate from tweak strips

        for mark in markers:
            if mark.frame in frames:
                frames.remove(mark.frame)
                mark.select = True

        for frame in frames:
            markers.new(str(frame), frame=frame)

        return {'FINISHED'}


def draw(self, context):
    layout = self.layout
    layout.operator('zpy.markers_from_selected_keyframes')


menues = (
    bpy.types.GRAPH_MT_marker,
    bpy.types.DOPESHEET_MT_marker,
    bpy.types.TIME_MT_marker,
)


def register():
    for mt in menues:
        mt.append(draw)


def unregister():
    for mt in menues:
        mt.remove(draw)
