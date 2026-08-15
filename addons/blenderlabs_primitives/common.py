"""Shared conventions for Blenderlabs primitive generators.

Every generator in this package follows the same rules:

  * build into a bmesh and return a plain mesh datablock
  * never touch bpy.ops, bpy.context or the scene - that is the operator's job
  * leave object transforms at identity; size is baked into the mesh
  * quads wherever possible, manifold, with edge loops that survive hand editing

Keeping generators free of context means they are importable from a scene
script, testable headlessly, and safe to call more than once.
"""

import math

import bmesh
import bpy


def superellipse_r(theta, a, b, n):
    """Radius of a superellipse at angle `theta`.

    n = 2 gives an ellipse, 4 a rounded square, 8+ nearly sharp corners.
    """
    return (abs(math.cos(theta) / a) ** n + abs(math.sin(theta) / b) ** n) ** (-1.0 / n)


def shift_origin(bm, mode):
    """Move geometry so the object origin lands where `mode` asks.

    'CENTER' leaves it alone, 'BOTTOM' drops the lowest point onto z=0 so the
    object can be placed by setting z to a surface height. Returns the offset.
    """
    if mode == 'CENTER':
        return 0.0
    if mode != 'BOTTOM':
        raise ValueError("origin mode must be 'CENTER' or 'BOTTOM', got %r" % mode)
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
    return -zmin


def apply_shading(bm, smooth, angle):
    """Smooth the faces and crease edges sharper than `angle` (radians).

    Done on the bmesh with plain edge flags rather than the shade_auto_smooth
    operator, so it needs no context and no modifier on the result.
    """
    for f in bm.faces:
        f.smooth = smooth
    if not smooth:
        return
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle() < angle
        else:
            e.smooth = False


def ring(bm, segments, radius_fn, z):
    """Create one closed loop of verts. `radius_fn(theta)` gives the radius."""
    verts = []
    for i in range(segments):
        th = i / segments * 2.0 * math.pi
        r = radius_fn(th)
        verts.append(bm.verts.new((math.cos(th) * r, math.sin(th) * r, z)))
    return verts


def bridge(bm, lo, hi, flip=False):
    """Quad band between two equal-length vertex loops."""
    n = len(lo)
    for i in range(n):
        k = (i + 1) % n
        f = [lo[i], lo[k], hi[k], hi[i]]
        bm.faces.new(f[::-1] if flip else f)


def to_mesh(bm, name):
    """Finalise a bmesh into a mesh datablock. Frees the bmesh."""
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def mesh_report(me):
    """Topology summary, for sanity checks and tests."""
    counts = [len(p.vertices) for p in me.polygons]
    return {
        "verts": len(me.vertices),
        "faces": len(me.polygons),
        "tris": sum(1 for c in counts if c == 3),
        "quads": sum(1 for c in counts if c == 4),
        "ngons": sum(1 for c in counts if c > 4),
    }
