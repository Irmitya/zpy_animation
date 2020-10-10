import bpy
from bpy.types import Operator
from zpy import New, Is


class GP_annotate_to_object(Operator):
    bl_description = "Send active Annotation to a Grease Pencil object"
    bl_idname = 'zpy.gp_from_annotation'
    bl_label = "Annotation to Grease Pencil"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        space = getattr(context, 'space', None)

        if space and space.grease_pencil:
            if Is.gpencil(context.object) and context.object.data == space.grease_pencil:
                return False

            return True

    def execute(self, context):
        an = context.space.grease_pencil
        # context.space.grease_pencil =

        ob = New.object(context, name=an.name, data=an)
        ob.location.z = 0.5
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler.x = 1.5707963705062866  # Face front
        ob.scale = (0.001,) * 3
        an.stroke_thickness_space = 'SCREENSPACE'

        # Send the color from annotations to the grease pencil object
        for layer in an.layers:
            layer.tint_color = layer.channel_color
            layer.tint_factor = 1
        """
        In addition to not "currently" knowing where individual stroke colors are
        Setting them will take longer and override any manual colors I may use.
        Setting the tint color (which annotations can only used) is faster and easier
        """

        return {'FINISHED'}

    def execute_new(self, context):
        """
        Either made this originally then scrapped for the simpler version
        above, or was making this then got distracted and never came back to it
        """
        def sync(owner, target, *attribs):
            for attrib in attribs:
                try:
                    setattr(target, attrib, getattr(owner, attrib))
                except:
                    print("Can't write", attrib, "in", target)

        gp = bpy.data.grease_pencils.new(name=an.name)
        New.object(context, name=an.name, data=gp)

        for alayer in an.layers:
            glayer = gp.layers.new(alayer.info)

            for aframe in alayer.frames:
                gframe = glayer.frames.new(aframe.frame_number)

                for astroke in aframe.strokes:
                    gstroke = gframe.strokes.new()

                    gstroke.points.add(len(astroke.points))
                    for (index, gpoint) in enumerate(gstroke.points):
                        apoint = astroke.points[index]

                        sync(apoint, gpoint,
                            'co', 'pressure', 'select', 'strength',
                            'uv_factor', 'uv_rotation')

                    sync(astroke, gstroke,
                        'draw_cyclic', 'end_cap_mode',
                        'gradient_factor', 'gradient_shape',
                        'line_width', 'material_index', 'select',
                        'start_cap_mode',
                        # 'groups', 'triangles'
                        )
                    gstroke.display_mode = '3DSPACE'

                sync(aframe, gframe, 'frame_number', 'select')

            sync(alayer, glayer,
                # 'active_frame',
                'annotation_hide',
                'annotation_onion_after_color', 'annotation_onion_before_color',
                'annotation_onion_after_range', 'annotation_onion_before_range',
                'blend_mode', 'channel_color', 'color', 'hide',
                'line_change', 'lock', 'lock_frame', 'lock_material',
                'mask_layer', 'matrix_inverse', 'opacity',
                'parent', 'parent_bone', 'parent_type', 'pass_index',
                'select', 'show_in_front', 'show_points', 'thickness',
                'tint_color', 'tint_factor',
                'use_annotation_onion_skinning', 'use_onion_skinning',
                'use_solo_mode', 'viewlayer_render'
                )

        return {'FINISHED'}


class GP_annotate_from_object(Operator):
    bl_description = "Send active Grease Pencil object to Annotation"
    bl_idname = 'zpy.annotation_from_gp'
    bl_label = "Annotation from Grease Pencil"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        space = getattr(context, 'space', None)

        if Is.gpencil(context.object):
            if space and space.grease_pencil == context.object.data:
                return False

            return True

    def execute(self, context):
        gp = context.object.data
        context.space.grease_pencil = gp

        return {'FINISHED'}
