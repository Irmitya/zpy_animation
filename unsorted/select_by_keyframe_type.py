import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator
from zpy import popup, register_keymaps, utils
km = register_keymaps()


rna_enum_beztriple_keyframe_type_items = [
    ("SELECTED", "Selected", "Any keyframe type with keys already selected", 'DECORATE_KEYFRAME', 5),
    ("KEYFRAME", "Keyframe", "Normal keyframe - e.g. for key poses", 'KEYTYPE_KEYFRAME_VEC', 0),
    ("BREAKDOWN", "Breakdown", "A breakdown pose - e.g. for transitions between key poses", 'KEYTYPE_BREAKDOWN_VEC', 1),
    ("MOVING_HOLD", "Moving Hold", "A keyframe that is part of a moving hold", 'KEYTYPE_MOVING_HOLD_VEC', 2),
    ("EXTREME", "Extreme", "An 'extreme' pose, or some other purpose as needed", 'KEYTYPE_EXTREME_VEC', 3),
    ("JITTER", "Jitter", "A filler or baked keyframe for keying on ones, or some other purpose as needed", 'KEYTYPE_JITTER_VEC', 4),
]


class GRAPH_OT_select_by(Operator):
    bl_description = "Menu to select all visible keyframes, based on factors"
    bl_idname = 'graph.select_by'
    bl_label = "Select Keyframes by ..."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    # @classmethod
    # def poll(cls, context):
        # return context.space_data.type == 'GRAPH_EDITOR'

    def draw_menu(cls, self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        for (id, name, desc, icon, index) in rna_enum_beztriple_keyframe_type_items:
            layout.operator('graph.select_by_type', text=name, icon=icon).type = id
        layout.separator(factor=1.0)
        layout.operator('graph.select_peaks', text="Peaks", icon='IPO_ELASTIC')
        layout.operator('graph.select_between', text="Between", icon='KEYFRAME')
        layout.operator('graph.select_random', text="Random", icon='MOD_NOISE')

    def execute(self, context):
        return popup.menu(context, self.draw_menu, title="Select by type")


class GRAPH_OT_select_by_type(Operator):
    bl_description = "Select all visible keyframes, matching the specified type"
    bl_idname = 'graph.select_by_type'
    bl_label = "Select Keyframes by Type"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.editable_fcurves

    def invoke(self, context, event):
        self.extend = event.shift

        return self.execute(context)

    def execute(self, context):
        types = set()

        if (self.type == 'SELECTED'):
            for fc in context.editable_fcurves:
                for key in fc.keyframe_points:
                    if key.select_control_point:
                        types.add(key.type)
        else:
            types = {self.type}

        for fc in context.editable_fcurves:
            for key in fc.keyframe_points:
                value = (key.type in types)
                if value or not self.extend:
                    # (Select if found) or (deselect if isolate and not found)
                    key.select_control_point = value

                if not value:
                    if key.select_left_handle:
                        key.select_left_handle = False
                    if key.select_right_handle:
                        key.select_right_handle = False

        return {'FINISHED'}

    type: EnumProperty(
        items=rna_enum_beztriple_keyframe_type_items,
        name="Type",
        description="",
        options={'SKIP_SAVE'},
    )
    extend: BoolProperty(
        name="Extend Selection",
        description="Don't deselect keyframes if their type doesn't match the filter",
        default=True,
        # options={'SKIP_SAVE'},
    )


class GRAPH_OT_select_peaks(Operator):
    bl_description = "Select extemes from all visible keyframes"
    bl_idname = 'graph.select_peaks'
    bl_label = "Select Keyframes by Peak"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.editable_fcurves

    def invoke(self, context, event):
        self.extend = event.shift

        return self.execute(context)

    def execute(self, context):
        for fc in context.editable_fcurves:
            if len(fc.keyframe_points) < 2:
                continue

            for (index, key) in enumerate(fc.keyframe_points):
                if index in (0, len(fc.keyframe_points) - 1):
                    key.select_control_point = True
                    continue

                val = key.co[1]
                last_key = fc.keyframe_points[index - 1]
                next_key = fc.keyframe_points[index + 1]
                last_val = last_key.co[1]
                next_val = next_key.co[1]

                if (last_val < val >= next_val) or (last_val > val <= next_val):
                    key.select_control_point = True
                elif not self.extend:
                    key.select_control_point = False
                    if key.select_left_handle:
                        key.select_left_handle = False
                    if key.select_right_handle:
                        key.select_right_handle = False

        return {'FINISHED'}

    extend: BoolProperty(
        name="Extend Selection",
        description="Don't deselect keyframes if they're not an extreme",
        default=True,
        # options={'SKIP_SAVE'},
    )


class GRAPH_OT_select_between(Operator):
    bl_description = "Select keys between selected keyframes" \
        ".\n (Note: Does not account for distance. Sample keyframes first)"
    bl_idname = 'graph.select_between'
    bl_label = "Select Between Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.editable_fcurves

    def execute(self, context):
        utils.update_keyframe_points(context)

        for fc in context.editable_fcurves:
            if len(fc.keyframe_points) < 2:
                continue

            keys = list()

            for key in fc.keyframe_points:
                if keys:
                    if key.select_control_point:
                        keys = keys[1:]

                        if self.count >= len(keys):
                            for between in keys:
                                between.select_control_point = True
                        else:
                            fac = (len(keys) + 1) / (self.count + 1)
                            count = 1
                            index = round(fac) - 1
                            while index < len(keys):
                                keys[index].select_control_point = True
                                count += 1
                                index = round(fac * count) - 1
                        keys = [key]
                    else:
                        keys.append(key)
                elif key.select_control_point:
                    keys.append(key)

        return {'FINISHED'}

    count: IntProperty(
        name="Count",
        description="Number of keys between keyframes to select",
        default=1,
        min=1,
    )


class GRAPH_OT_select_random(Operator):
    bl_description = "Select keys at random"
    bl_idname = 'graph.select_random'
    bl_label = "Select Random Keyframes. \nCtrl + Click to only deselect keys"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.editable_fcurves

    def invoke(self, context, event):
        self.extend = event.shift
        if event.ctrl:
            self.deselect = True

        return self.execute(context)

    def execute(self, context):
        from random import choice

        utils.update_keyframe_points(context)

        for fc in context.editable_fcurves:
            for key in fc.keyframe_points:
                if (self.deselect and not key.select_control_point) or \
                    (key.select_control_point and self.extend):
                    continue

                key.select_control_point = choice((True, False))

        return {'FINISHED'}

    deselect: BoolProperty(
        name="Only Deselect",
        description="Only deselect keys",
        default=False,
        options={'SKIP_SAVE'},
    )

    extend: BoolProperty(
        name="Extend Selection",
        description="Maintain current keyframe selection",
        default=True,
        # options={'SKIP_SAVE'},
    )


def register():
    for name in ('Dopesheet', 'Graph Editor'):
        km.add(GRAPH_OT_select_by, name=name, type='G', value='PRESS', shift=True)


def unregister():
    km.remove()
