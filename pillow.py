"""
Low-poly tufted pillow generator.

Pure procedural quad mesh - no cloth sim, no modifiers, fully deterministic.
Re-run to rebuild from scratch with new parameters.

Topology:
  - concentric quad rings from the centre button out to the seam
  - seam loop is shared between top and bottom -> closed, manifold, and planar
    (at z=0 when ORIGIN='CENTER', lifted by the shift when ORIGIN='BOTTOM')
  - only 2 n-gons in the whole mesh (the centre caps), both hidden under the buttons

Run inside Blender:  blender --python pillow.py
or paste into the Scripting tab.
"""

import bpy
import bmesh
import math

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
WIDTH, DEPTH = 0.60, 0.60   # footprint in metres
HALF_THICK   = 0.105        # puff height above the seam
SEGMENTS     = 24           # angular resolution (raise for smoother silhouette)
RINGS        = 5            # radial loops from button to seam
BUTTON_R     = 0.055        # tuft radius
SQUARENESS   = 4.0          # 2 = ellipse, 4 = rounded square, 8 = nearly square
TUFT         = 0.55         # centre dimple depth, 0 = flat, 1 = pinched to seam
TUFT_WIDTH   = 0.30         # how far the dimple spreads (in normalised radius)
BUTTON_SEG   = 12           # button facet count
SMOOTH_ANGLE = 50.0         # auto-smooth angle in degrees
ORIGIN       = 'BOTTOM'     # 'CENTER' = origin on the seam plane (mid-height)
                            # 'BOTTOM' = origin at the lowest point, so setting
                            #            z to a surface height just works

SEAT_Z = HALF_THICK * (1.0 - TUFT)   # z of the centre cap the button sits in

A, B = WIDTH / 2.0, DEPTH / 2.0


def boundary_r(th):
    """Superellipse radius at angle th -> the rounded-square outline."""
    n = SQUARENESS
    return (abs(math.cos(th) / A) ** n + abs(math.sin(th) / B) ** n) ** (-1.0 / n)


def height(s):
    """Surface height for normalised radius s (0 = centre, 1 = seam)."""
    puff = math.cos(s * math.pi / 2.0) ** 0.75
    dimple = 1.0 - TUFT * math.exp(-(s / TUFT_WIDTH) ** 2)
    return HALF_THICK * puff * dimple


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def build_pillow():
    bm = bmesh.new()
    rings = {}

    for side in (1, -1):
        for j in range(RINGS + 1):
            if j == RINGS and side == -1:
                rings[(side, j)] = rings[(1, RINGS)]      # share the seam loop
                continue
            s = j / RINGS
            row = []
            for i in range(SEGMENTS):
                th = i / SEGMENTS * 2 * math.pi
                r = BUTTON_R * (1 - s) + boundary_r(th) * s
                z = 0.0 if j == RINGS else side * height(s)
                row.append(bm.verts.new((math.cos(th) * r, math.sin(th) * r, z)))
            rings[(side, j)] = row

    bm.verts.ensure_lookup_table()

    for side in (1, -1):
        for j in range(RINGS):
            lo, hi = rings[(side, j)], rings[(side, j + 1)]
            for i in range(SEGMENTS):
                k = (i + 1) % SEGMENTS
                f = [lo[i], lo[k], hi[k], hi[i]]
                bm.faces.new(f if side == 1 else f[::-1])
        cap = rings[(side, 0)]
        bm.faces.new(cap if side == 1 else cap[::-1])

    bm.normal_update()
    me = bpy.data.meshes.new("Pillow")
    bm.to_mesh(me)
    bm.free()

    ob = bpy.data.objects.new("Pillow", me)
    bpy.context.collection.objects.link(ob)
    return ob


def build_button(name, side, parent):
    bm = bmesh.new()
    r_lo, r_hi = BUTTON_R * 1.02, BUTTON_R * 0.86
    h = 0.011
    z0 = side * (SEAT_Z - 0.007)
    z1 = side * (SEAT_Z - 0.007 + h)

    lo, hi = [], []
    for i in range(BUTTON_SEG):
        th = i / BUTTON_SEG * 2 * math.pi
        lo.append(bm.verts.new((math.cos(th) * r_lo, math.sin(th) * r_lo, z0)))
        hi.append(bm.verts.new((math.cos(th) * r_hi, math.sin(th) * r_hi, z1)))
    for i in range(BUTTON_SEG):
        k = (i + 1) % BUTTON_SEG
        f = [lo[i], lo[k], hi[k], hi[i]]
        bm.faces.new(f if side == 1 else f[::-1])
    bm.faces.new(hi if side == 1 else hi[::-1])
    bm.faces.new(lo[::-1] if side == 1 else lo)

    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()

    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.parent = parent
    return ob


def set_origin(parts):
    """Shift mesh data so the object origin lands where ORIGIN asks.

    All parts are shifted by the SAME offset - the buttons are parented to the
    pillow, so moving only the pillow's vertices would leave them behind.
    Object transforms stay at identity; this is a mesh-space edit.
    """
    if ORIGIN == 'CENTER':
        return 0.0
    if ORIGIN != 'BOTTOM':
        raise ValueError("ORIGIN must be 'CENTER' or 'BOTTOM', got %r" % ORIGIN)

    zmin = min(v.co.z for ob in parts for v in ob.data.vertices)
    for ob in parts:
        for v in ob.data.vertices:
            v.co.z -= zmin
        ob.data.update()
    return -zmin


def shade(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_auto_smooth(angle=math.radians(SMOOTH_ANGLE))


def main():
    clear_scene()
    pillow = build_pillow()
    parts = [pillow,
             build_button("Button_Top", 1, pillow),
             build_button("Button_Bot", -1, pillow)]
    offset = set_origin(parts)
    for ob in parts:
        shade(ob)

    me = pillow.data
    print(f"Origin mode {ORIGIN!r} (mesh shifted {offset:+.4f} in z); "
          f"seam plane now at z={offset:.4f}")
    quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
    ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
    tris = sum(1 for p in me.polygons if len(p.vertices) == 3)
    print(f"Pillow: {len(me.vertices)} verts, {len(me.polygons)} faces "
          f"({quads} quads, {tris} tris, {ngons} ngons)")
    print(f"Total scene faces: {sum(len(o.data.polygons) for o in parts)}")


if __name__ == "__main__":
    main()
