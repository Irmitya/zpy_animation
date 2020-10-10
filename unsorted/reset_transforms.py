import bpy
from bpy.props import EnumProperty, FloatProperty
from bpy.types import Operator
from inspect import getmembers
from mathutils import Euler, Quaternion, Vector, Matrix
from zpy import Get, Is, register_keymaps, keyframe, utils
km = register_keymaps()


def get_base(src):
    if hasattr(src, 'base_src') and src.base_src.is_duplicate:
        base = src.base_transforms
    else:
        base = default_transforms
        # base = utils.matrix_to_transforms(Matrix())

    return base


class default_transforms:
    location = Vector((0, 0, 0))
    rotation_euler = Euler((0, 0, 0))
    rotation_axis_angle = ((0, 0, 1, 0))
    rotation_quaternion = Quaternion((1, 0, 0, 0))
    scale = Vector((1, 1, 1))


mode = EnumProperty(
    items=[
        ('loc', "Location", "", 'CON_LOCLIKE', 1),
        ('rot', "Rotation", "", 'CON_ROTLIKE', 2),
        ('scale', "Scale", "", 'CON_SIZELIKE', 4),
    ],
    name="Transforms",
    description="",
    default={'loc', 'rot', 'scale'},
    options={'ENUM_FLAG'},
)


class RESET_OT_base_transforms(Operator):
    bl_description = "Reset an item's transforms back to default"
    bl_idname = 'zpy.reset_transforms'
    bl_label = "Reset Transforms"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        if not hasattr(bpy.types.PoseBone, 'base_src'):
            return False
        for src in Get.selected(context):
            if src.get('base_src') and src.base_src.is_duplicate:
                return True

    def execute(self, context):
        do_all = (self.mode == {'loc', 'rot', 'scale'})

        for src in Get.selected(context):
            base = get_base(src)

            if 'loc' in self.mode:
                src.location = base.location
            if 'rot' in self.mode:
                if src.rotation_mode == 'QUATERNION':
                    src.rotation_quaternion = base.rotation_quaternion
                elif src.rotation_mode == 'AXIS_ANGLE':
                    src.rotation_axis_angle = base.rotation_axis_angle
                else:
                    src.rotation_euler = base.rotation_euler
                if Is.posebone(src):
                    src.bbone_curveinx = src.bbone_curveoutx = src.bbone_curveiny = src.bbone_curveouty = src.bbone_rollin = src.bbone_rollout = 0
            if 'scale' in self.mode:
                src.scale = base.scale
                if Is.posebone(src):
                    src.bbone_scaleinx = src.bbone_scaleinx = src.bbone_scaleiny = src.bbone_scaleoutx = src.bbone_scaleouty = 1
                    src.bbone_easein = src.bbone_easeout = 0

            utils.clean_custom(src)

        keyframe.keyingset(context, selected=Get.selected(context))

        return {'FINISHED'}

    mode: mode


class RESET_OT_all_transforms(Operator):
    bl_description = "Reset an item's transforms back to default"
    bl_idname = 'zpy.reset_transforms_all'
    bl_label = "Reset Transforms"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return Get.selected(context)

    execute = RESET_OT_base_transforms.execute
    mode = {'loc', 'rot', 'scale'}


class ZERO_OT_layered_pose(Operator):
    bl_description = "Transition between the current pose and the lower layer"
    bl_idname = 'zpy.zero_layer_pose'
    bl_label = "Zero Layered Pose"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'GRAB_CURSOR'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        if (context.mode != 'PAINT_WEIGHT'):
            return Get.selected(context)

    def __init__(self):
        global pose

        pose = type('', (), dict(
            base=dict(),
            reset=dict(),
        ))

    def invoke(self, context, event):
        # Get current pose
        for src in Get.selected(context):
            pose.base[repr(src)] = Get.matrix(src, basis=True)

        # Disable animation and get pose from lower layers
        base_anim = dict()
        for src in Get.selected(context):
            obj = src.id_data
            anim = obj.animation_data

            if (anim) and (obj not in base_anim):
                tracks = list()

                if anim.use_tweak_mode:
                    # Find the strip to disable

                    for track in reversed(anim.nla_tracks):
                        for _strip in track.strips:
                            if _strip.active:
                                strip = _strip
                                break
                            elif _strip.action == anim.action:
                                # backup in case strip isn't "active"
                                strip = _strip
                        else:
                            tracks.append((track, track.mute))
                            # track.mute = True
                            continue
                        break

                    base_anim[obj] = [strip, strip.mute, tracks]
                    strip.mute = True
                    # anim.use_tweak_mode = False
                else:
                    base_anim[obj] = [None, anim.action_influence, tracks]
                    anim.action_influence = 0
                utils.update(context)

            pose.reset[repr(src)] = Get.matrix(src, basis=True)

        # Re-enable animation
        for obj in base_anim:
            anim = obj.animation_data
            (strip, value, tracks) = base_anim[obj]
            if strip:
                # for (track, track_mute) in tracks:
                    # track.mute = track_mute
                strip.mute = value
                # anim.use_tweak_mode = True
            else:
                anim.action_influence = value
            utils.update(context)

        # context.window_manager.modal_handler_add(self)
        # return {'RUNNING_MODAL'}
        return self.execute(context)

    "Idea for modal, is after invoke, start dragging for the pose, then click to apply"
    # def modal(self, context, event):

        # if event.type == 'LEFTMOUSE':
        #     return {'FINISHED'}

        # if event.type in {'RIGHTMOUSE', 'ESC'}:
        #     return {'CANCELLED'}

        # return {'PASS_THROUGH'}
        # return {'RUNNING_MODAL'}

    def execute(self, context):
        fac = (self.factor / 100)

        for src in Get.selected(context):
            base = pose.base[repr(src)]
            reset = pose.reset[repr(src)]

            if src.rotation_mode in ('QUATERNION', 'AXIS_ANGLE'):
                euler = 'XYZ'
            else:
                euler = src.rotation_mode

            if Is.matrix(reset):
                matrix = utils.lerp(base, reset, fac)
                matrix = utils.matrix_to_transforms(matrix, euler=euler)
            else:
                location = base.to_translation()
                rotation_quaternion = base.to_quaternion()
                axis = base.to_quaternion().to_axis_angle()
                rotation_axis_angle = (*axis[0], axis[1])
                rotation_euler = base.to_euler(euler)
                scale = base.to_scale()

                matrix = type('matrix and transforms', (), dict(
                    location=utils.lerp(location, reset.location, fac),
                    rotation_quaternion=utils.lerp(rotation_quaternion, reset.rotation_quaternion, fac),
                    rotation_axis_angle=utils.lerp(rotation_axis_angle, reset.rotation_axis_angle, fac),
                    rotation_euler=utils.lerp(rotation_euler, reset.rotation_euler, fac),
                    scale=utils.lerp(scale, reset.scale, fac),
                ))

            if 'loc' in self.mode:
                src.location = matrix.location
            if 'rot' in self.mode:
                src.rotation_quaternion = matrix.rotation_quaternion
                src.rotation_axis_angle = matrix.rotation_axis_angle
                src.rotation_euler = matrix.rotation_euler
            if 'scale' in self.mode:
                src.scale = matrix.scale

        keyframe.keyingset(context, selected=Get.selected(context))

        return {'FINISHED'}

    mode: mode
    factor: FloatProperty(
        name="Factor",
        description="",
        default=100.0,
        soft_min=-200,
        soft_max=200,
        # options={'SKIP_SAVE'},
        subtype='PERCENTAGE',
    )


# def zero_layered_pose(context, src):


def register():
    for name in ('Object Mode', 'Pose'):
        args = dict(idname=RESET_OT_base_transforms, name=name, alt=True)
        km.add(**args, type='G', mode={'loc'})
        km.add(**args, type='R', mode={'rot'})
        km.add(**args, type='S', mode={'scale'})

        args = dict(name=name, type='Q')
        km.add(RESET_OT_all_transforms, alt=True, **args)
        km.add(ZERO_OT_layered_pose, shift=True, **args)


def unregister():
    km.remove()
