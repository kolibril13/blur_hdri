import bpy
from bpy.props import FloatProperty
from bpy.types import Operator
from PIL import Image, ImageFilter
import os

class NODE_OT_blur_env_image(bpy.types.Operator):
    bl_idname = "node.blur_env_image"
    bl_label = "Blur Environment Image"
    bl_options = {'REGISTER', 'UNDO'}

    radius: FloatProperty(
        name="Blur Radius",
        description="Radius for Gaussian Blur",
        default=5.0,
        min=0.1,
        max=100.0
    )

    def execute(self, context):
        world = context.scene.world
        if not (world and world.node_tree):
            self.report({'ERROR'}, "No world node tree found.")
            return {'CANCELLED'}
        nodes = world.node_tree.nodes
        selected_nodes = [n for n in nodes if n.select]
        if not selected_nodes:
            self.report({'ERROR'}, "No node selected.")
            return {'CANCELLED'}
        node = selected_nodes[0]
        if not (hasattr(node, "image") and node.image and node.image.filepath):
            self.report({'ERROR'}, "Selected node is not an image node or has no image.")
            return {'CANCELLED'}
        img_path = bpy.path.abspath(node.image.filepath)
        try:
            img = Image.open(img_path)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=self.radius))
            base, ext = os.path.splitext(img_path)
            blurred_path = base + "_blurred" + ext
            blurred.save(blurred_path)
            env_node = nodes.new(type='ShaderNodeTexEnvironment')
            env_node.location = (node.location[0], node.location[1] - 300)
            env_node.image = bpy.data.images.load(blurred_path)
        except Exception as e:
            self.report({'ERROR'}, f"Error processing image: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def register():
    bpy.utils.register_class(NODE_OT_blur_env_image)

def unregister():
    bpy.utils.unregister_class(NODE_OT_blur_env_image)
