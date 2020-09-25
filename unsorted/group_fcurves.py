import bpy


class CHANNELS_OT_send_to_group(bpy.types.Operator):
    bl_description = ""
    bl_idname = 'zpy.group_fcurves'
    bl_label = "Group Curves"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return bpy.ops.anim.channels_group.poll(context.copy())

    def execute(self, context):
        for fc in context.visible_fcurves:
            if fc.group:
                continue

            if fc.data_path.startswith(('pose.bones', 'bones')):
                name = fc.data_path.split('["', 1)[1].split('"]', 1)[0]
            else:
                name = "Object Transforms"

            groups = fc.id_data.groups
            if name in groups:
                fc.group = groups[name]
            else:
                fc.group = groups.new(name)

        return {'FINISHED'}


def draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator('zpy.group_fcurves')


def register():
    bpy.types.GRAPH_MT_channel.append(draw)


def unregister():
    bpy.types.GRAPH_MT_channel.remove(draw)
