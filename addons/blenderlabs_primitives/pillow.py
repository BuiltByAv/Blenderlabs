"""Tufted pillow generator.

Concentric quad rings run from the centre button out to the seam. The seam loop
is shared between the top and bottom halves, so the result is one closed
manifold surface with a planar seam - which means trim or piping added later
follows a flat ring instead of cutting through at an angle.

The button is part of the same mesh rather than a separate object: it is the
innermost ring extruded up and tapered, capped with a single n-gon. That keeps
the primitive to one editable object with no loose parts.
"""

import math

try:
    from . import common
except ImportError:          # allow running this file directly for quick tests
    import common


DEFAULTS = {
    "width": 0.60,
    "depth": 0.60,
    "half_thickness": 0.105,
    "segments": 24,
    "rings": 5,
    "button_radius": 0.055,
    "button_height": 0.011,
    "button_taper": 0.86,
    "squareness": 4.0,
    "tuft": 0.55,
    "tuft_width": 0.30,
}


def build(name="Pillow",
          width=0.60,
          depth=0.60,
          half_thickness=0.105,
          segments=24,
          rings=5,
          button_radius=0.055,
          button_height=0.011,
          button_taper=0.86,
          squareness=4.0,
          tuft=0.55,
          tuft_width=0.30,
          origin='BOTTOM',
          smooth=True,
          smooth_angle=math.radians(50.0)):
    """Build a tufted pillow and return an unlinked mesh datablock."""
    import bmesh

    a, b = width / 2.0, depth / 2.0
    seat_z = half_thickness * (1.0 - tuft)      # height of the button seat

    def outline(th):
        return common.superellipse_r(th, a, b, squareness)

    def height(s):
        """Surface height at normalised radius s: 0 at centre, 1 at the seam."""
        puff = math.cos(s * math.pi / 2.0) ** 0.75
        dimple = 1.0 - tuft * math.exp(-(s / tuft_width) ** 2)
        return half_thickness * puff * dimple

    bm = bmesh.new()
    seam = None                                  # shared between both halves

    for side in (1, -1):
        flip = side == -1

        # --- surface loops, button seat outwards to the seam ---
        loops = []
        for j in range(rings + 1):
            if j == rings:
                if seam is None:
                    seam = common.ring(bm, segments, outline, 0.0)
                loops.append(seam)
                continue
            s = j / rings
            z = side * height(s)
            loops.append(common.ring(
                bm, segments,
                lambda th, s=s: button_radius * (1.0 - s) + outline(th) * s,
                z))

        for j in range(rings):
            common.bridge(bm, loops[j], loops[j + 1], flip)

        # --- button: innermost loop extruded up and tapered, then capped ---
        top = common.ring(bm, segments,
                          lambda th: button_radius * button_taper,
                          side * (seat_z + button_height))
        common.bridge(bm, loops[0], top, flip)
        bm.faces.new(top[::-1] if flip else top)

    common.shift_origin(bm, origin)
    common.apply_shading(bm, smooth, smooth_angle)
    return common.to_mesh(bm, name)
