import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, FloatProperty, BoolProperty, StringProperty, IntProperty
from zpy import register_keymaps, Get, Is, utils, keyframe, cpp
km = register_keymaps()


transforms = ('location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'scale')


class tween:
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'GRAB_CURSOR'}
    keytype = 'BREAKDOWN'
    mode = 'Sliding-Tool'

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.mode in ('POSE', 'OBJECT')

    def invoke(self, context, event):
        self.has_additive = False
        self.fcurves = self.get_keys(context)
        # if self.fcurves is None:
        #     return {'PASS_THROUGH'}
        # elif self.fcurves is False:
        if not self.fcurves:
            return {'CANCELLED'}
        else:
            self.get_offset(context, event)

        context.window.cursor_set("SCROLL_X")
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    # def execute(self, context):
        # # self.fcurves = self.get_keys(context)
        # if not self.fcurves:
            # return {'CANCELLED'}
        # else:
            # self.run_offset()

        # return self.finish(context)
        # return {'FINISHED'}

    def modal(self, context, event):
        if event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}:
            return self.finish(context)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.cancel(context)
        elif event.type == 'MOUSEMOVE':
            self.get_offset(context, event)
        elif event.value == 'PRESS':
            nums = "01234567890@%^&*-+/{}()[]<>.|"
            if self.num or (event.ascii and event.ascii in nums):
                # Grab percentage from numeric input, and store this new value for redo
                # NOTE: users see ints, while internally we use a 0-1 float

                if event.type in ('NUMPAD_MINUS', 'MINUS'):
                    if self.num.startswith('-'):
                        self.num = self.num[1:]
                    else:
                        self.num = '-' + self.num
                elif event.type == 'BACK_SPACE':
                    self.num = self.num[:-1]
                elif event.ascii in nums:
                    self.num += event.ascii

                try:
                    value = eval(self.num)
                except:
                    value = self.percentage * 100.0

                self.percentage = value / 100.0
                # CLAMP(pso->percentage, 0.0f, 1.0f);
                # RNA_float_set(op->ptr, "percentage", pso->percentage);

                # # /* Update pose to reflect the new values (see below) */
                # do_pose_update = True
                self.get_offset(context, event)

            # Transform Channel Limits
            elif event.type == 'G':  # Location
                self.toggle_channels('LOC')
                self.get_offset(context, event)
            elif event.type == 'R':  # Rotation
                self.toggle_channels('ROT')
                self.get_offset(context, event)
            elif event.type == 'S':  # Scale
                self.toggle_channels('SIZE')
                self.get_offset(context, event)
            elif event.type == 'B':  # Bendy Bones
                self.toggle_channels('BBONE')
                self.get_offset(context, event)
            elif event.type == 'C':  # Custom Properties
                self.toggle_channels('CUSTOM')
                self.get_offset(context, event)

            # Axis Locks
            elif event.type == 'X':
                if self.toggle_axis_locks('X'):
                    self.get_offset(context, event)
            elif event.type == 'Y':
                if self.toggle_axis_locks('Y'):
                    self.get_offset(context, event)
            elif event.type == 'Z':
                if self.toggle_axis_locks('Z'):
                    self.get_offset(context, event)

            # Swap update
            elif event.type == 'TAB' and self.has_additive:
                tween.update = not tween.update
                self.cancel(context)
                self.fcurves = self.get_keys(context)
                self.get_offset(context, event)

            else:
                # unhandled event - maybe it was some view manip?
                # allow to pass through
                return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")
        if keyframe.use_auto(context):
            # keyframe.keyingset(context)
            for arg in self.fcurves:
                (left, current, right) = self.fcurves[arg]

                if (not current.key):  # or ((not current.found) and current.in_range):
                    # Set the new keyframe's type to Breakdown or Extreme
                    keytype = self.keytype
                else:
                    # Keep the current keyframe's type
                    keytype = current.key.type

                (fc, key) = keyframe.manual(
                    context, current.src, current.attr, index=current.index)
                if (fc and key):
                    key.type = keytype
                    fc.update()

        return {'FINISHED'}

    def cancel(self, context):
        context.area.header_text_set(None)
        context.window.cursor_set("DEFAULT")
        for arg in self.fcurves:
            (left, current, right) = self.fcurves[arg]
            current.apply(current, current.value)
            # current.prop[current.index] = current.value
        return {'CANCELLED'}

    def toggle_channels(self, channel):
        """handle an event to toggle channels mode"""

        # Turn channel on or off?
        if self.channels == channel:
            # Already limiting to transform only, so pressing this again turns it off
            self.channels = 'ALL'
        else:
            # Only this set of channels
            self.channels = channel

        # Reset axis limits too for good measure
        self.axislock = 'FREE'

    def toggle_axis_locks(self, axis):
        """handle an event to toggle axis locks - returns whether any change in state is needed"""

        # Axis can only be set when a transform is set - it doesn't make sense otherwise
        if self.channels in ('ALL', 'BBONE', 'CUSTOM'):
            return False

        # Turn on or off?
        if self.axislock == axis:
            # Already limiting on this axis, so turn off
            self.axislock = 'FREE'
        else:
            # Only this axis
            self.axislock = axis

        # Setting changed, so pose update is needed
        return True

    def get_offset(self, context, event):
        area = context.area

        if self.num:
            # self.percentage = 0.5
            pass
        else:
            center = area.width / 2 + area.x
            offset = (event.mouse_x - center) / area.width
            # self.center_x = int(area.width / 2)
            # self.center_y = int(area.height / 2)
            # self.mouse_x = event.mouse_x
            self.percentage = utils.scale_range(offset, -0.5, 0.5, 0, 1)
            self.percentage = utils.proportional(self.percentage, mode=context)

        self.set_text(area)
        self.run_offset()

    def run_offset(self):
        for arg in self.fcurves:
            if (self.channels != 'ALL') or (self.axislock != 'FREE'):
                current = self.fcurves[arg][1]
                attr = current.attr
                index = current.index
                reset = False

                if (self.channels == 'LOC'):
                    if (current.attr != 'location'):
                        reset = True
                    elif (self.axislock == 'FREE'):
                        pass
                    elif (['X', 'Y', 'Z'][index] != self.axislock):
                        reset = True
                elif (self.channels == 'ROT'):
                    if (attr == 'rotation_euler'):
                        if (self.axislock == 'FREE'):
                            pass
                        elif (['X', 'Y', 'Z'][index] != self.axislock):
                            reset = True
                    elif (attr == 'rotation_quaternion'):
                        if (self.axislock == 'FREE') or (index == 0):
                            pass
                        elif (['X', 'Y', 'Z'][index - 1] != self.axislock):
                            reset = True
                    elif attr == 'rotation_axis_angle':
                        if (self.axislock == 'FREE'):
                            pass
                        else:
                            reset = True
                    else:
                        reset = True
                elif (self.channels == 'SIZE'):
                    if (attr != 'scale'):
                        reset = True
                    elif (self.axislock == 'FREE'):
                        pass
                    elif (['X', 'Y', 'Z'][index] != self.axislock):
                        reset = True
                elif (self.channels == 'BBONE'):
                    if not attr.startswith('bbone'):
                        continue
                elif (self.channels == 'CUSTOM'):
                    if ('["' not in attr) or ('"]' not in attr):
                        continue

                if reset:
                    current.apply(current, current.value)
                    # current.prop[current.index] = current.value
                    continue

            self.tween(*self.fcurves[arg])

    def set_text(self, area):
        # TODO: setup axis limits like the regular tweener, currently nothing set
            # area.header_text_set("%s: %.f %%  |  %s"%(mode, offset*100, limit))

        mode_str = self.mode

        if self.axislock == 'X':
            axis_str = "[X]/Y/Z axis only (X to clear)"
        elif self.axislock == 'Y':
            axis_str = "X/[Y]/Z axis only (Y to clear)"
        elif self.axislock == 'Z':
            axis_str = "X/Y/[Z] axis only (Z to clear)"
        else:
            axis_str = "X/Y/Z = Axis Constraint"

        if self.channels == 'LOC':
            limits_str = "[G]/R/S/B/C - Location only (G to clear) | " + axis_str
        elif self.channels == 'ROT':
            limits_str = "G/[R]/S/B/C - Rotation only (R to clear) | " + axis_str
        elif self.channels == 'SIZE':
            limits_str = "G/R/[S]/B/C - Scale only (S to clear) | " + axis_str
        elif self.channels == 'BBONE':
            limits_str = "G/R/S/[B]/C - Bendy Bone properties only (B to clear)"
        elif self.channels == 'CUSTOM':
            limits_str = "G/R/S/B/[C] - Custom Properties only (C to clear)"
        else:
            limits_str = "G/R/S/B/C - Limit to Transform/Property Set"

        if self.num:
            try:
                # str_val = eval(self.num)
                str_offs = f"[{self.num}] = {round(self.percentage * 100.0)}%"
            except:
                # str_val = "N/A"
                str_offs = f"[{self.num}] = N/A"

            status_str = "%s: %s     |   %s" % (
                mode_str, str_offs, limits_str)
        else:
            status_str = "%s: %d %%     |   %s" % (
                mode_str, round(self.percentage * 100.0), limits_str)
            # status_str = f"{mode_str}: {int(self.percentage) * 100} %     |   {limits_str}"

        if self.has_additive:
            if tween.update:
                status_str += "    |   (Tab to Key-to-Key)"
            else:
                status_str += "    |   (Tab to Pose-to_Pose)"

        area.header_text_set(status_str)

    def get_keys(self, context):
        scn_frame = context.scene.frame_current_final
        fcurves = dict()
        quats = dict()
        updates = dict()

        break_sync = False
        if hasattr(context.scene, 'sync'):
            break_sync = context.scene.sync.sync_3d and context.scene.sync.sync_between_3d

        if context.mode == 'POSE':
            # objects = [o for o in Get.objects(context) if o.mode == 'POSE']
            objects = list()

            for ob in Get.objects(context):
                if ob.mode != 'POSE':
                    continue
                bones = tuple([f"pose.bones[\"{b.name}\"]"
                    for b in Get.selected_pose_bones(context, ob)])
                if bones:
                    objects.append((ob, bones))

            if not objects:
                for ob in Get.objects(context):
                    if ob.mode != 'POSE':
                        continue
                    bones = tuple([f"pose.bones[\"{b.name}\"]"
                        for b in ob.pose.bones if Is.visible(context, b)])
                    if bones:
                        objects.append((ob, bones))
        else:
            objects = [(o, list()) for o in Get.selected_objects(context)]

        for (ob, bones) in objects:
            for anim in Get.animation_datas(ob):
                action = anim.action
                if not action:
                    continue

                if anim.use_tweak_mode:
                    frame = Get.frame_to_strip(context, anim, scn_frame)
                    for s in Get.strips(anim.id_data):
                        if s.action == action:
                            strip = s
                            if s.active: break
                    blend = strip.blend_type
                else:
                    frame = scn_frame
                    blend = anim.action_blend_type

                offset = abs(frame - scn_frame)
                if (scn_frame < frame):
                    offset *= -1

                for fc in anim.action.fcurves:
                    path = fc.data_path
                    index = fc.array_index

                    if len(fc.keyframe_points) < 2:
                        continue
                    if bones:
                        src = None
                        for bone in bones:
                            if path.startswith(bone):
                                try:
                                    eval(repr(ob) + '.' + path)  # Validate path
                                    src = eval(repr(ob) + '.' + bone)
                                    attr = path.replace(bone, '', 1)
                                    if attr.startswith('.'):
                                        attr = attr.replace('.', '', 1)
                                        is_custom = False
                                    else:
                                        is_custom = True
                                except:
                                    # curve points to a removed bone or something
                                    src = None
                                break
                        else:
                            # Pose mode but bone not selected
                            continue
                        if src is None:
                            # Missing bone
                            continue
                    else:
                        attr = path
                        src = ob

                        if attr in transforms:
                            is_custom = False
                        elif attr.startswith('["'):
                            is_custom = True
                        else:
                            # if attr.startswith(('pose.bones', 'bones')):
                            continue

                    # Find the property to be able to manipulate, and its current value
                    if is_custom:
                        prop = src
                        split = attr.rsplit('"]["', 1)
                        if len(split) == 2:
                            prop = eval(repr(src) + split[0] + '"]')
                            attr = '["' + split[1]
                        prop_value = getattr(prop, attr)
                    elif hasattr(src, attr):
                        prop = getattr(src, attr)
                        if Is.iterable(prop):
                            # elif attr in transforms:
                                # prop = src.path_resolve(attr)
                            prop_value = prop[index]
                        else:
                            prop = src
                            prop_value = getattr(prop, attr)
                    else:
                        # maybe a constraint:
                            # pose.bones[bone.name].constraints[con.name].influence
                        continue

                    # Function to apply values to the bone/object, later
                    if Is.iterable(prop):
                        def apply(self, val):
                            "Function to apply values to (array) in bone/object, later"
                            self.prop[self.index] = val

                        prop = src.path_resolve(attr)
                        prop_value = prop[index]
                        is_array = True
                    else:
                        def apply(self, val):
                            setattr(self.prop, self.attr, val)
                        is_array = False

                    cache = dict(
                        attr=attr,
                        apply=apply,
                        index=index,
                        is_array=is_array,
                        key=None,
                        quat=None,
                        prop=prop,
                        src=src,
                        value=fc.evaluate(frame),
                    )
                    left = type('', (), cache)
                    current = type('', (), cache)
                    current.found = False
                    right = type('', (), cache)

                    pre_key = None

                    # Find the current keyframe, and keys left and right
                    if break_sync:
                        # types = context.scene.keyframe_navigation_types
                        types = ('KEYFRAME', 'MOVING_HOLD')
                        for key in fc.keyframe_points:
                            if key.co.x < frame:
                                if (left.key is None) or (key.type in types):
                                    left.key = key
                                    left.value = key.co.y
                                    right.key = key
                                    right.value = key.co.y
                            elif key.co.x == frame:
                                if left.key is None:
                                    left.key = key
                                    left.value = key.co.y
                                current.key = key
                                current.found = True
                                right.key = key
                                right.value = key.co.y
                            elif key.co.x > frame:
                                if left.key is None:
                                    left.key = key
                                    left.value = key.co.y
                                if (key.type in types) or key == fc.keyframe_points[-1]:
                                    right.key = key
                                    right.value = key.co.y
                                    break

                    if not (left.key and right.key):
                        for key in fc.keyframe_points:
                            if key.co.x < frame:
                                left.key = key
                                left.value = key.co.y
                                right.key = key
                                right.value = key.co.y
                            elif key.co.x == frame:
                                if left.key is None:
                                    left.key = key
                                    left.value = key.co.y
                                current.key = key
                                current.found = True
                                right.key = key
                                right.value = key.co.y
                            elif key.co.x > frame:
                                if left.key is None:
                                    left.key = key
                                    left.value = key.co.y
                                right.key = key
                                right.value = key.co.y
                                break

                    if not (left.key and right.key):
                        # Nothing to tween
                        continue

                    # Get info for current keyframe's defaults

                    sVal = left.key.co.x + offset
                    eVal = right.key.co.x + offset

                    current.w1 = frame - sVal
                    current.w2 = eVal - frame

                    left.frame = left.key.co.x
                    current.frame = frame
                    right.frame = right.key.co.x

                    current.in_range = False
                    if frame < left.frame:
                        left.value = prop_value
                    elif right.frame < frame:
                        right.value = prop_value
                    else:
                        current.in_range = True

                    if blend == 'REPLACE':
                        current.value = prop_value
                    else:
                        if not self.has_additive:
                            self.has_additive = True

                        if current.key:
                            value = current.key.co.y
                        else:
                            value = fc.evaluate(frame)

                        left.value = prop_value + (left.value - value)
                        current.value = prop_value  # + (value - value)
                        right.value = prop_value + (right.value - value)

                        if tween.update:
                            if sVal not in updates:
                                updates[sVal] = list()
                            if eVal not in updates:
                                updates[eVal] = list()
                            updates[sVal].append(left)
                            updates[eVal].append(right)

                    # Add classes to memory
                    fcurves[fc] = [left, current, right]

                    if attr == 'rotation_quaternion':
                        # Do math for quaternions
                        if (action, path) not in quats:
                            quats[(action, path)] = dict()

                        if (src.lock_rotations_4d or not src.lock_rotation_w) \
                            and True not in src.lock_rotation[:]:
                            quats[(action, path)][index] = (left, current, right)

        if updates:
            for frame in updates:
                context.scene.frame_set(frame)

                for (cls) in updates[frame]:
                    if Is.iterable(prop):
                        cls.value = cls.prop[cls.index]
                    else:
                        cls.value = getattr(cls.prop, cls.attr)

            context.scene.frame_set(scn_frame)

        for (action, path) in quats:
            if len(quats[action, path]) < 4:
                continue
            (w_left, w_current, w_right) = quats[action, path][0]
            (x_left, x_current, x_right) = quats[action, path][1]
            (y_left, y_current, y_right) = quats[action, path][2]
            (z_left, z_current, z_right) = quats[action, path][3]

            left_quat = [x.value for x in (w_left, x_left, y_left, z_left)]
            current_quat = [x.value for x in (w_current, x_current, y_current, z_current)]
            right_quat = [x.value for x in (w_right, x_right, y_right, z_right)]

            cpp.normalize_qt(left_quat)
            cpp.normalize_qt(current_quat)
            cpp.normalize_qt(right_quat)

            for x in (w_left, x_left, y_left, z_left):
                x.quat = left_quat
            for x in (w_current, x_current, y_current, z_current):
                x.quat = current_quat
            for x in (w_right, x_right, y_right, z_right):
                x.quat = right_quat

        return fcurves

    percentage: FloatProperty(
        default=0.5,
        name="Percentage",
        description="Weighting factor for which keyframe is favored more",
        # min=0.0,
        # max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        options={'HIDDEN'},
    )
    prev_frame: IntProperty(
        name="Previous Keyframe",
        description="Frame number of keyframe immediately before the current frame",
        soft_min=0,
        soft_max=50,
        options={'HIDDEN'},
    )
    next_frame: IntProperty(
        name="Next Keyframe",
        description="Frame number of keyframe immediately after the current frame",
        soft_min=0,
        soft_max=50,
        options={'HIDDEN'},
    )
    channels: EnumProperty(
        items=[
            ('ALL', "All Properties", "All properties, including transforms, bendy bone shape, and custom properties"),
            ('LOC', "Location", "Location only"),
            ('ROT', "Rotation", "Rotation only"),
            ('SIZE', "Scale", "Scale only"),
            ('BBONE', "Bendy Bone", "Bendy Bone shape properties"),
            ('CUSTOM', "Custom Properties", "Custom properties"),
        ],
        name="Channels",
        description="Set of properties that are affected",
        default='ALL',
        options={'ANIMATABLE', 'HIDDEN'},
        #   (set) – Enumerator  in ['HIDDEN', 'SKIP_SAVE', 'ANIMATABLE',
        #   'ENUM_FLAG', 'LIBRARY_EDITABLE'].
    )
    axislock: EnumProperty(
        items=[
            ('FREE', "Free", "All axes are affected"),
            ('X', "X", "Only X-axis transforms are affected"),
            ('Y', "Y", "Only Y-axis transforms are affected"),
            ('Z', "Z", "Only Z-axis transforms are affected"),
        ],
        name="Axis Lock",
        description="Transform axis to restrict effects to",
        default='FREE',
        options={'ANIMATABLE', 'HIDDEN'},
        #   (set) – Enumerator  in ['HIDDEN', 'SKIP_SAVE', 'ANIMATABLE',
        #   'ENUM_FLAG', 'LIBRARY_EDITABLE'].
    )

    # update: BoolProperty(
        # description="Refresh the frame, to get the absolute pose values when using additive layers (slow)",
        # # options={'SKIP_SAVE'},
    # )
    update = False

    num: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})


class TWEEN_OT_breakdown(Operator, tween):
    bl_description = "Create a suitable breakdown pose on the current frame"
    bl_idname = 'zpy.tween_breakdown'
    bl_label = "Pose Breakdowner"
    mode = 'Breakdown'

    def tween(self, left, current, right):
        sVal = left.value
        eVal = right.value

        if current.attr == 'rotation_quaternion' and current.quat:
            quat_final = [0, 0, 0, 0]
            quat_prev = left.quat.copy()
            quat_next = right.quat.copy()

            # Just perform the interpolation between quat_prev and
            # quat_next using pso->percentage as a guide.
            cpp.interp_qt_qtqt(quat_final, quat_prev, quat_next, self.percentage)

            val = quat_final[current.index]
        else:
            w1 = self.percentage
            w2 = 1 - w1

            val = ((sVal * w2) + (eVal * w1))

        current.apply(current, val)
        # current.prop[current.index] = val


class TWEEN_OT_relax(Operator, tween):
    bl_description = "Make the current pose more similar to its breakdown pose"
    bl_idname = 'zpy.tween_relax'
    bl_label = "Relax Pose to Breakdown"
    mode = 'Relax Pose'

    def tween(self, left, current, right):
        val = current.value
        sVal = left.value
        eVal = right.value

        # # This is the internal operator's "relax" tween for rotations
        # # Problem is, it (like the internal one) doesn't do a smooth blend
        if current.attr == 'rotation_quaternion' and current.quat:
            quat_final = [0, 0, 0, 0]

            quat_prev = left.quat.copy()
            quat_curr = current.quat.copy()
            quat_next = right.quat.copy()
            quat_interp = [0, 0, 0, 0]
            quat_final_prev = [0, 0, 0, 0]

            cpp.copy_qt_qt(quat_final, quat_curr)

            cframe = bpy.context.scene.frame_current_final
            if left.frame < right.frame:
                frame = (cframe - left.frame) / (right.frame - left.frame)
            else:
                frame = 0

            from math import ceil
            # /* TODO: maybe a sensitivity ctrl on top of this is needed */
            iters = int(ceil(10.0 * self.percentage))

            # /* perform this blending several times until a satisfactory result is reached */
            for iter in range(iters):
                # /* calculate the interpolation between the endpoints */
                cpp.interp_qt_qtqt(quat_interp, quat_prev, quat_next, frame)

                cpp.normalize_qt_qt(quat_final_prev, quat_final)

                # /* tricky interpolations - blending between original and new */
                cpp.interp_qt_qtqt(quat_final, quat_final_prev, quat_interp, 1.0 / 6.0)

                iters -= 1
            val = quat_final[current.index]
        else:
            w1 = current.w1
            w2 = current.w2

            wtot = w1 + w2
            if wtot:
                w1 = (w1 / wtot)
                w2 = (w2 / wtot)
            else:
                w1 = w2 = 0.5

            val += ((sVal * w2) + (eVal * w1) - (val)) * self.percentage

        current.apply(current, val)
        # current.prop[current.index] = val


class TWEEN_OT_push(Operator, tween):
    bl_description = "Exaggerate the current pose in regards to the breakdown pose"
    bl_idname = 'zpy.tween_push'
    bl_label = "Push Pose from Breakdown"
    mode = 'Push Pose'
    keytype = 'EXTREME'

    def tween(self, left, current, right):
        val = current.value
        sVal = left.value
        eVal = right.value

        if current.attr == 'rotation_quaternion' and current.quat:
            quat_final = current.quat.copy()
            quat_final[current.index] = val

            quat_diff = [0, 0, 0, 0]
            quat_curr = current.quat.copy()
            quat_prev = left.quat.copy()

            # calculate the delta transform from the previous to the current
            cpp.sub_qt_qtqt(quat_diff, quat_curr, quat_prev)

            # increase the original by the delta transform, by an amount determined by percentage
            cpp.add_qt_qtqt(quat_final, quat_curr, quat_diff, self.percentage)

            cpp.normalize_qt(quat_final)

            val = quat_final[current.index]
        else:
            w1 = current.w1
            w2 = current.w2

            wtot = w1 + w2
            if wtot:
                w1 = (w1 / wtot)
                w2 = (w2 / wtot)
            else:
                w1 = w2 = 0.5

            val -= ((sVal * w2) + (eVal * w1) - (val)) * self.percentage

        current.apply(current, val)
        # current.prop[current.index] = val


def register():
    for name in ('Object Mode', 'Pose'):
        args = dict(name=name, type='E')
        km.add(TWEEN_OT_breakdown, **args, value='PRESS', shift=True)
        km.add(TWEEN_OT_relax, **args, value='PRESS', alt=True)
        km.add(TWEEN_OT_push, **args, value='PRESS', ctrl=True)

    # args = dict(name='Pose', type='D', update=True)
    # km.add(TWEEN_OT_breakdown, **args, value='PRESS', shift=True)
    # km.add(TWEEN_OT_relax, **args, value='PRESS', alt=True)
    # km.add(TWEEN_OT_push, **args, value='PRESS', ctrl=True)


def unregister():
    km.remove()
