"""Blenderlabs Primitives - parametric base objects with clean quad topology.

Adds generators under View3D > Add > Mesh. Each one drops a finished mesh into
the scene with an F9 redo panel for its parameters: dial it in, then Tab into
edit mode and take over by hand. Parameters bake in at creation - the result is
an ordinary editable mesh, not a procedural object you have to fight.

Layering, deliberately:
    <name>.py   pure geometry, returns a mesh datablock, no context, no ops
    __init__.py operators - scene insertion, placement, menu registration
"""

bl_info = {
    "name": "Blenderlabs Primitives",
    "author": "Blenderlabs",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Add > Mesh",
    "description": "Parametric base objects with clean, edit-friendly quad topology",
    "category": "Add Mesh",
}

import math

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add

# reload submodules cleanly when developing straight from the repo
if "common" in locals():
    import importlib
    common = importlib.reload(common)        # noqa: F821
    pillow = importlib.reload(pillow)        # noqa: F821
else:
    from . import common, pillow


class MESH_OT_blenderlabs_pillow(bpy.types.Operator, AddObjectHelper):
    """Add a tufted pillow with clean quad topology"""

    bl_idname = "mesh.blenderlabs_pillow"
    bl_label = "Pillow"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(
        name="Width", default=0.60, min=0.01, soft_max=2.0, unit='LENGTH')
    depth: FloatProperty(
        name="Depth", default=0.60, min=0.01, soft_max=2.0, unit='LENGTH')
    half_thickness: FloatProperty(
        name="Puff", description="Height above the seam plane",
        default=0.105, min=0.001, soft_max=0.5, unit='LENGTH')

    resolution: IntProperty(
        name="Resolution",
        description="Grid divisions across the pillow. Forced odd so a centred "
                    "button lands on a vertex. Raise it if dimples look faceted",
        default=21, min=5, soft_max=81)

    squareness: FloatProperty(
        name="Squareness",
        description="2 = round cushion, 4 = rounded square, 8 = nearly sharp",
        default=4.0, min=1.0, soft_max=12.0)

    tuft: FloatProperty(
        name="Tuft Depth", description="Depth of the centre dimple",
        default=0.55, min=0.0, max=0.95)
    tuft_width: FloatProperty(
        name="Tuft Spread", description="How far the dimple reaches out",
        default=0.30, min=0.05, max=1.0)

    buttons: EnumProperty(
        name="Buttons",
        items=[
            ('1', "1 - Centre", "A single button at the centre"),
            ('3', "3 - Row", "Three buttons in a row along X"),
            ('5', "5 - Quincunx", "Centre plus four on the diagonals"),
        ],
        default='1')
    button_spread: FloatProperty(
        name="Button Spread",
        description="How far the outer buttons sit from the centre",
        default=0.45, min=0.0, max=0.95)

    button_radius: FloatProperty(
        name="Button Radius", default=0.055, min=0.001, soft_max=0.3, unit='LENGTH')
    button_segments: IntProperty(
        name="Button Segments", default=12, min=3, soft_max=48)
    button_height: FloatProperty(
        name="Button Height", default=0.011, min=0.0, soft_max=0.1, unit='LENGTH')
    button_taper: FloatProperty(
        name="Button Taper", description="Top radius as a fraction of the base",
        default=0.86, min=0.05, max=1.0)

    origin_mode: EnumProperty(
        name="Origin",
        items=[
            ('BOTTOM', "Bottom", "Origin at the lowest point - sits on a surface by setting z"),
            ('CENTER', "Center", "Origin on the seam plane, symmetric top to bottom"),
        ],
        default='BOTTOM')

    shade_smooth: BoolProperty(name="Shade Smooth", default=True)
    smooth_angle: FloatProperty(
        name="Smooth Angle", default=math.radians(50.0),
        min=0.0, max=math.radians(180.0), subtype='ANGLE')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "half_thickness")
        col.prop(self, "squareness")

        col = layout.column(align=True)
        col.prop(self, "resolution")

        col = layout.column(align=True)
        col.prop(self, "tuft")
        col.prop(self, "tuft_width")

        col = layout.column(align=True)
        col.prop(self, "buttons")
        sub = col.column()
        sub.active = self.buttons != '1'
        sub.prop(self, "button_spread")

        col = layout.column(align=True)
        col.prop(self, "button_radius")
        col.prop(self, "button_height")
        col.prop(self, "button_taper")
        col.prop(self, "button_segments")

        col = layout.column(align=True)
        col.prop(self, "origin_mode")
        col.prop(self, "shade_smooth")
        sub = col.column()
        sub.active = self.shade_smooth
        sub.prop(self, "smooth_angle")

        col = layout.column(align=True)
        col.prop(self, "align")
        col.prop(self, "location")
        col.prop(self, "rotation")

    def execute(self, context):
        me = pillow.build(
            name="Pillow",
            width=self.width,
            depth=self.depth,
            half_thickness=self.half_thickness,
            resolution=self.resolution,
            buttons=self.buttons,
            button_spread=self.button_spread,
            button_radius=self.button_radius,
            button_height=self.button_height,
            button_taper=self.button_taper,
            button_segments=self.button_segments,
            squareness=self.squareness,
            tuft=self.tuft,
            tuft_width=self.tuft_width,
            origin=self.origin_mode,
            smooth=self.shade_smooth,
            smooth_angle=self.smooth_angle,
        )
        object_data_add(context, me, operator=self)
        return {'FINISHED'}


# Note: no `scale` property on purpose. Width/Depth/Puff resize the mesh itself,
# which keeps the button circular and the object transform at identity. Object
# scale would squash the button into an ellipse and break modifier widths.

CLASSES = (
    MESH_OT_blenderlabs_pillow,
)


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(MESH_OT_blenderlabs_pillow.bl_idname,
                         text="Pillow", icon='MESH_CIRCLE')


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
