import bpy
from bpy.props import BoolProperty, IntProperty
from bpy.types import Operator
from zpy import utils, register_keymaps
km = register_keymaps()


class duplicate:
    bl_description = "Make a copy of all selected keyframes and move them"
    bl_label = "Duplicate Loop"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    # @classmethod
    # def poll(cls, context):
        # return cls.op.poll(context.copy())

    def invoke(self, context, event):
        utils.update_keyframe_points(context)
        return self.execute(context)

    def execute(self, context):
        for fc in context.editable_fcurves:
            keyframes = fc.keyframe_points
            keys = list()
            remove = list()

            start = end = None

            for (index, key) in enumerate(keyframes):
                if key.select_control_point:
                    keys.append(index)
                    if start is None:
                        start = key.co.x
                    end = key.co.x
                elif self.remove:
                    remove.append(index)

            if (start == end):
                continue

            dist = (end - start)

            # Remove keyframes in range of the loop (override them)
            for index in reversed(remove):
                key = keyframes[index]
                for mul in range(self.repeat + 1):
                    if (end < key.co.x <= (end + (dist * mul))):
                        keyframes.remove(key)
                        break

            # Duplicate selected keyframes and offset them
            for index in keys:
                if (index != keys[0]):
                    # Don't overwrite last key with the first
                    for mul in range(self.repeat + 1):
                        key = fc.keyframe_points[index]
                        key2 = fc.keyframe_points.insert(key.co.x + (dist * mul), key.co.y)
                        key = fc.keyframe_points[index]  # Re-get key incase it's lost after insertion
                        for prop in ('amplitude', 'back', 'easing',
                            'handle_left', 'handle_left_type',
                            'handle_right', 'handle_right_type',
                            'interpolation', 'period', 'type',
                            'select_left_handle', 'select_right_handle'):
                            setattr(key2, prop, getattr(key, prop))
                        key2.handle_left.x += (dist * mul)
                        key2.handle_right.x += (dist * mul)

                if (index != keys[-1]):
                    # Don't deselect last key
                    key = keyframes[index]
                    key.select_control_point = False
                    key.select_left_handle = False
                    key.select_right_handle = False

        return {'FINISHED'}

    repeat: IntProperty(
        name="Repeat",
        description="Number of times to duplicate loop",
        default=1,
        min=1,
    )

    remove: BoolProperty(
        name="Overwrite Existing",
        description="Remove unselected keyframes in the range0 of the next loop",
        default=True,
    )


class DOPESHEET_OT_duplicate_loop(Operator, duplicate):
    bl_idname = 'action.duplicate_loop'
    op = bpy.ops.action.duplicate_move


class GRAPH_OT_duplicate_loop(Operator, duplicate):
    bl_idname = 'graph.duplicate_loop'
    op = bpy.ops.graph.duplicate_move


def register():
    args = dict(type='D', value='PRESS', alt=True)
    km.add('action.duplicate_loop', name='Dopesheet', **args)
    km.add('graph.duplicate_loop', name='Graph Editor', **args)

    # args = dict(type='D', value='PRESS', ctrl=True)
    # km.add('action.duplicate_loop', name='Dopesheet', **args)
    # km.add('graph.duplicate_loop', name='Graph Editor', **args)


def unregister():
    km.remove()
