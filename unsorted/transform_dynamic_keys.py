import bpy
from bpy.types import Operator, Menu
from zpy import utils


class GRAPH_MT_transform_dynamic(Menu):
    bl_description = ""
    # bl_idname = 'GRAPH_MT_transform_dynamic'
    bl_label = "Transform (Dynamic)"

    # @classmethod
    # def poll(cls, context):
        # return context.editable_fcurves

    def draw(self, context):
        layout = self.layout
        layout.separator()
        layout.operator('graph.elastic_amplitude')
        layout.operator('graph.elastic_period')
        layout.operator('graph.back_back')


class ops:
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'GRAB_CURSOR'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.editable_fcurves

    def invoke(self, context, event):
        utils.update_keyframe_points(context)

        self.initial_x = event.mouse_x
        self.keys = set()

        for fc in context.editable_fcurves:
            for key in fc.keyframe_points:
                if key.select_control_point:
                    self.keys.add((key, getattr(key, self.attr)))

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (event.type == 'MOUSEMOVE'):
            # Update
            offset = (event.mouse_x - self.initial_x) * [0.01, 0.0001][event.shift]

            for (key, default) in self.keys:
                if event.ctrl:
                    setattr(key, self.attr, round(default + offset))
                else:
                    setattr(key, self.attr, (default + offset))

            text = f"{self.attr.title()}: {offset:.2f}"
            context.area.header_text_set(text)
        elif (event.type in {'LEFTMOUSE'}):
            context.area.header_text_set(None)
            return {'FINISHED'}
        elif (event.type in {'RIGHTMOUSE', 'ESC'}):
            for (key, default) in self.keys:
                setattr(key, self.attr, default)
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class GRAPH_OT_transform_dynamic_amplitude(Operator, ops):
    bl_description = "Adjust influence of elastic keyframes (default = 0.8)"
    bl_idname = 'graph.elastic_amplitude'
    bl_label = "Elastic Amplitude"
    attr = 'amplitude'
    default = 0.8


class GRAPH_OT_transform_dynamic_period(Operator, ops):
    bl_description = "Adjust amount of bounces in elastic keyframes (default = 4.1)"
    bl_idname = 'graph.elastic_period'
    bl_label = "Elastic Period"
    attr = 'period'
    default = 4.1


class GRAPH_OT_transform_dynamic_back(Operator, ops):
    bl_description = "Adjust influence of back keyframes (default = 1.70158)"
    bl_idname = 'graph.back_back'
    bl_label = "Back Back"
    attr = 'back'
    default = 1.70158


def register():
    bpy.types.DOPESHEET_MT_key_transform.append(GRAPH_MT_transform_dynamic.draw)
    bpy.types.GRAPH_MT_key_transform.append(GRAPH_MT_transform_dynamic.draw)
    # bpy.types.GRAPH_MT_key.append(GRAPH_MT_transform_dynamic.draw)


def unregister():
    bpy.types.DOPESHEET_MT_key_transform.remove(GRAPH_MT_transform_dynamic.draw)
    bpy.types.GRAPH_MT_key_transform.remove(GRAPH_MT_transform_dynamic.draw)
    # bpy.types.GRAPH_MT_key.remove(GRAPH_MT_transform_dynamic.draw)
