"""Tufted pillow generator.

Topology is a quad grid mapped onto a superellipse footprint. The grid's
boundary loop is shared between the top and bottom halves, so the mesh is
closed, manifold, and the seam stays planar - trim or piping added later
follows a flat ring instead of cutting through at an angle.

Tufting is a height field: a puff profile that falls to zero at the seam,
multiplied by a Gaussian dimple at each button. A grid is used rather than
concentric rings because rings can only resolve a dimple at the centre - an
off-centre button would fall between loops and read as a lumpy dent.

Buttons are separate closed islands inside the same mesh object, sunk into
their dimples. That keeps them circular and independently selectable (hover
and press L) at any grid resolution.
"""

import math

try:
    from . import common
except ImportError:          # allow running this file directly for quick tests
    import common


# Button positions in normalised domain space, scaled by `button_spread`.
LAYOUTS = {
    '1': [(0.0, 0.0)],
    '3': [(-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)],
    '5': [(0.0, 0.0), (-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)],
}


def build(name="Pillow",
          width=0.60,
          depth=0.60,
          half_thickness=0.105,
          resolution=15,
          squareness=4.0,
          tuft=0.55,
          tuft_width=0.30,
          buttons='1',
          button_spread=0.45,
          button_radius=0.055,
          button_height=0.011,
          button_taper=0.86,
          button_segments=10,
          origin='BOTTOM',
          smooth=True,
          smooth_angle=math.radians(50.0)):
    """Build a tufted pillow and return an unlinked mesh datablock."""
    import bmesh

    a, b = width / 2.0, depth / 2.0
    n = squareness

    # odd resolution guarantees a vertex exactly at the centre, which keeps a
    # centred dimple symmetric instead of straddling a quad
    res = int(resolution)
    if res % 2 == 0:
        res += 1
    res = max(res, 5)

    # --- button anchor points, in world XY, with their surface parameter ---
    # Snap anchors onto grid vertices in domain space. A dimple centred between
    # grid lines gets sampled off its peak, so the dip lands shallow and skewed
    # and the button sits crooked in it - the artefact that otherwise forces a
    # high resolution. Snapping lets a much coarser grid hold up.
    step = 2.0 / (res - 1)

    def snap(c):
        return round(c / step) * step

    anchors = []
    for nu, nv in LAYOUTS.get(str(buttons), LAYOUTS['1']):
        bx, by, bt = common.square_to_superellipse(
            snap(nu * button_spread), snap(nv * button_spread), a, b, n)
        anchors.append((bx, by, bt))

    sigma = max(tuft_width * min(a, b), 1e-6)

    inv_s2 = 1.0 / (sigma * sigma)

    def height(x, y, t):
        """Surface height: puff profile, pulled down by every button.

        The dimples combine as a smooth union - 1 - prod(1 - g_i) - rather than
        by nearest-button distance. Taking the nearest button makes the field
        non-differentiable wherever two are equidistant, which shows up as
        visible Voronoi ridges between them. This form is smooth everywhere and
        still bounded to [0, 1] however many buttons overlap.
        """
        puff = half_thickness * math.cos(t * math.pi / 2.0) ** 0.75
        if tuft <= 0.0 or not anchors:
            return puff
        keep = 1.0
        for bx, by, _ in anchors:
            g = math.exp(-((x - bx) ** 2 + (y - by) ** 2) * inv_s2)
            keep *= (1.0 - g)
        return puff * (1.0 - tuft * (1.0 - keep))

    bm = bmesh.new()

    # --- the two grid surfaces, sharing their boundary loop ---
    grids = {}
    for side in (1, -1):
        g = [[None] * res for _ in range(res)]
        for i in range(res):
            u = -1.0 + 2.0 * i / (res - 1)
            for j in range(res):
                v = -1.0 + 2.0 * j / (res - 1)
                on_edge = i in (0, res - 1) or j in (0, res - 1)
                if side == -1 and on_edge:
                    g[i][j] = grids[1][i][j]          # share the seam
                    continue
                x, y, t = common.square_to_superellipse(u, v, a, b, n)
                z = 0.0 if on_edge else side * height(x, y, t)
                g[i][j] = bm.verts.new((x, y, z))
        grids[side] = g

    for side in (1, -1):
        g = grids[side]
        for i in range(res - 1):
            for j in range(res - 1):
                f = [g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]]
                bm.faces.new(f[::-1] if side == -1 else f)

    # --- buttons: closed discs sunk into each dimple ---
    for bx, by, bt in anchors:
        z_seat = height(bx, by, bt)
        for side in (1, -1):
            flip = side == -1
            base = common.ring(bm, button_segments, lambda th: button_radius,
                               side * (z_seat - 0.004), center=(bx, by))
            top = common.ring(bm, button_segments,
                              lambda th: button_radius * button_taper,
                              side * (z_seat - 0.004 + button_height),
                              center=(bx, by))
            common.bridge(bm, base, top, flip)
            bm.faces.new(top[::-1] if flip else top)
            bm.faces.new(base if flip else base[::-1])

    common.shift_origin(bm, origin)
    common.apply_shading(bm, smooth, smooth_angle)
    return common.to_mesh(bm, name)
