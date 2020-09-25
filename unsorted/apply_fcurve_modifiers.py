from bpy.types import Panel, Operator
from bpy.props import BoolProperty, EnumProperty
from zpy import utils, register_keymaps
km = register_keymaps()


class default:
    mod = 'APPLY'


class GRAPH_OT_apply_modifiers(Operator):
    bl_description = "Apply FCurve Modifiers to selected keyframes"
    bl_idname = 'zpy.apply_fcurve_modifiers'
    bl_label = "Apply Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        if not context.editable_fcurves:
            return
        for fc in context.editable_fcurves:
            for mod in fc.modifiers:
                if mod.type != 'CYCLES':
                    return True

    def invoke(self, context, event):
        utils.update_keyframe_points(context)

        if event.alt:
            self.all_fcurves = True

        return self.execute(context)

    def execute(self, context):
        if self.all_fcurves:
            fcurves = context.editable_fcurves
        else:
            fcurves = [context.active_editable_fcurve]

        for fc in fcurves:
            if not [mod for mod in fc.modifiers if (mod.type != 'CYCLES')]:
                continue

            keyframes = (key for key in fc.keyframe_points if key.select_control_point)

            if not keyframes:
                if self.all_fcurves:
                    # No keys in the fcurve selected, so ignore it
                    continue
                else:
                    # Apply to all keys on active fcurve
                    keyframes = fc.keyframe_points
            if not keyframes:
                continue

            for key in keyframes:
                evalue = fc.evaluate(key.co.x)
                kvalue = key.co.y
                ovalue = abs(evalue - kvalue)
                if (evalue < kvalue):
                    ovalue *= -1

                key.co.y += ovalue
                key.handle_left.y += ovalue
                key.handle_right.y += ovalue

            if (self.mod != 'APPLY'):
                for mod in fc.modifiers:
                    if (mod.type != 'CYCLES'):
                        if (self.mod == 'MUTE'):
                            mod.mute = True
                        elif (self.mod == 'REMOVE'):
                            fc.modifiers.remove(mod)
            fc.update()

        default.mod = self.mod

        return {'FINISHED'}

    all_fcurves: BoolProperty(
        name="All Fcurves",
        description="Apply values to all selected keyframes, not just from the active fcurve",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    mod: EnumProperty(
        items=[
            ('APPLY', "Apply", "Keep Modifiers", 'MODIFIER', 1),
            ('MUTE', "Mute", "Mute Modifiers", 'CHECKBOX_HLT', 2),
            ('REMOVE', "Remove", "Remove Modifiers", 'X', 3),
        ],
        name="Modifier",
        description="What to do with modifiers after applying to keyframes",
        default='APPLY',
        options={'ANIMATABLE'},
    )


# class NLA_PT_apply_modifiers(Panel):
    # bl_parent_id = NLA_PT_modifiers
    # bl_space_type = 'NLA_EDITOR'
class GRAPH_PT_apply_modifiers(Panel):
    bl_category = "Modifiers"
    bl_parent_id = 'GRAPH_PT_modifiers'
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    bl_region_type = 'UI'
    bl_space_type = 'GRAPH_EDITOR'

    # @classmethod
    # def poll(cls, context):
        # fc = context.active_editable_fcurve
        # return (fc and fc.modifiers)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        def op(mod, **kargs):
            but = row.row()
            if (default.mod == mod):
                kargs['text'] = mod.title() + " Modifiers"
            else:
                kargs['text'] = ""
            but.operator('zpy.apply_fcurve_modifiers', **kargs).mod = mod

        op('APPLY', icon='MODIFIER')
        op('MUTE', icon='CHECKBOX_HLT')
        op('REMOVE', icon='X')


def register():
    km.add(GRAPH_OT_apply_modifiers, name='Graph Editor', type='A', value='PRESS', ctrl=True, all_fcurves=True)


def unregister():
    km.remove()
