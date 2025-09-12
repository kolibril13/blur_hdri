import bpy
from bpy.props import FloatProperty
from bpy.types import Operator
from PIL import Image, ImageFilter
import os

class NODE_OT_blur_env_image(bpy.types.Operator):
    bl_idname = "node.blur_env_image"
    bl_label = "Blur Image Node"
    bl_options = {'REGISTER', 'UNDO'}

    radius: FloatProperty(
        name="Blur Radius",
        description="Radius for Gaussian Blur",
        default=5.0,
        min=0.1,
        max=100.0
    )

    def execute(self, context):
        # Try to get the active node tree (material or world)
        node_tree = None
        nodes = None
        selected_nodes = None

        # Check if we're in the Shader Editor and if a material node tree is active
        space = context.space_data
        if space and hasattr(space, "node_tree") and space.node_tree:
            node_tree = space.node_tree
        elif context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        elif context.scene.world and context.scene.world.node_tree:
            node_tree = context.scene.world.node_tree

        if not node_tree:
            self.report({'ERROR'}, "No node tree found (material or world).")
            return {'CANCELLED'}

        nodes = node_tree.nodes
        selected_nodes = [n for n in nodes if n.select]

        if not selected_nodes:
            self.report({'ERROR'}, "No node selected.")
            return {'CANCELLED'}

        node = selected_nodes[0]
        # Accept both ShaderNodeTexImage and ShaderNodeTexEnvironment
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

            # Create a new image node of the same type as the original
            if node.bl_idname == 'ShaderNodeTexImage':
                new_node = nodes.new(type='ShaderNodeTexImage')
            elif node.bl_idname == 'ShaderNodeTexEnvironment':
                new_node = nodes.new(type='ShaderNodeTexEnvironment')
            else:
                self.report({'ERROR'}, "Selected node is not a supported image node.")
                return {'CANCELLED'}

            new_node.location = (node.location[0], node.location[1] - 300)
            new_node.image = bpy.data.images.load(blurred_path)

            # Optionally, copy color space and other settings
            if hasattr(node, "color_space") and hasattr(new_node, "color_space"):
                new_node.color_space = node.color_space

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
