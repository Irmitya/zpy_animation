import bpy
from bpy.types import GRAPH_MT_snap_pie, Menu, Operator


class GRAPH_OT_snap(Operator):
    bl_description = "Place the cursor on the midpoint of selected keyframes"
    bl_idname = 'graph.snap_cursor_only'
    bl_label = "Cursor to Selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return bpy.ops.graph.frame_jump.poll(context.copy())

    def execute(self, context):
        sc = context.scene
        sp = context.space_data
        # x = sp.cursor_position_x
        x = (sc.frame_current, sc.frame_subframe)
        y = sp.cursor_position_y

        bpy.ops.graph.frame_jump()

        if self.type == 'value':
            # sp.cursor_position_x = x
            (sc.frame_current, sc.frame_subframe) = x
        elif self.type == 'frame':
            sp.cursor_position_y = y

        return {'FINISHED'}

    type: bpy.props.EnumProperty(
        items=[
            ('value', "Value", "Up/Down"),
            ('frame', "Frame", "Left/Right"),
            ('both', "Frame + Value", "Default"),
        ],
        name="Type",
        description="",
        default='both',
        options={'SKIP_SAVE'},
    )


# class GRAPH_MT_snap_pie(Menu):
    # bl_label = "Snap (Cursor)"

    # @classmethod
    # def poll(cls, context):
        # return True

    # def draw(self, context):
def GRAPH_MT_snap_pie_cursor(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator('graph.snap_cursor_only', text="Cursor to Selected Frame").type = 'frame'
        pie.operator('graph.snap_cursor_only', text="Cursor to Selected Value").type = 'value'


def register():
    GRAPH_MT_snap_pie.append(GRAPH_MT_snap_pie_cursor)


def unregister():
    GRAPH_MT_snap_pie.remove(GRAPH_MT_snap_pie_cursor)
