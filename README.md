# Blenderlabs

Parametric generators for base objects in Blender. Each one drops a finished
mesh into the scene with clean quad topology, tuned through an F9 redo panel,
then you Tab in and edit it by hand. The script is a factory for good starting
geometry - not a procedural object you have to keep fighting.

Built against **Blender 5.2 LTS**.

## Layout

```
addons/
  blenderlabs_primitives/
    __init__.py     operators, redo panel, Add > Mesh registration
    common.py       shared conventions (superellipse, origin, shading, reports)
    pillow.py       tufted pillow generator
```

## Install

Blender loads the add-on **directly from this repo** - there is no copy step, so
what you edit is what runs.

1. Edit ▸ Preferences ▸ File Paths ▸ **Scripts Directories** ▸ `+`
2. Point it at this repo's root (the folder containing `addons/`)
3. Edit ▸ Preferences ▸ Add-ons ▸ enable **Blenderlabs Primitives**
4. Save Preferences

Then: `Add ▸ Mesh ▸ Pillow`, and press **F9** to open the parameters.

After changing a generator, re-run `script.reload` (F3 ▸ "Reload Scripts") to
pick up the edit.

## Generators

### Pillow

A quad grid mapped onto a superellipse footprint. The grid's boundary loop is
shared between the top and bottom halves, so the mesh is closed, manifold, and
the seam is **planar** - trim or piping added later follows a flat ring instead
of cutting through at an angle.

Supports **1, 3 or 5 buttons**: centre, a row along X, or a quincunx.

Tufting is a height field - a puff profile falling to zero at the seam,
multiplied by a Gaussian dimple per button. Dimples combine as a smooth union
(`1 - prod(1 - g)`) rather than by nearest-button distance; nearest-distance is
non-differentiable where two buttons are equidistant and leaves visible Voronoi
ridges between them.

A grid is used rather than concentric rings because rings can only resolve a
dimple at the centre - an off-centre button falls between loops and reads as a
lumpy dent.

Buttons are separate closed islands inside the same mesh object, seated in
their dimples. That keeps them circular at any grid resolution and
independently selectable (hover, press <kbd>L</kbd>).

A button's face is placed relative to the **highest surrounding surface point**,
not to the dimple's low point. Off-centre buttons sit in a *tilted* dimple - the
puff profile is higher toward the pillow's centre than toward the seam, giving a
rim spread of ~18 mm against the centre button's 0.6 mm - so seating them on the
anchor buried them unevenly and they read as partly swallowed from directly
above. Measuring from the rim makes every button sit identically.

Button anchors are **snapped onto grid vertices**. A dimple centred between grid
lines is sampled off its peak, so the dip lands shallow and skewed and the
button sits crooked in it. Snapping is what lets the default grid stay coarse -
without it the same quality needs roughly double the polygons.

At default settings:

| Buttons | Verts | Faces | Quads | Tris | Islands |
|---|---|---|---|---|---|
| 1 | 434 | 416 | 412 | 0 | 3 |
| 3 | 514 | 464 | 452 | 0 | 7 |
| 5 | 594 | 512 | 492 | 0 | 11 |

Zero non-manifold edges in every case. Islands are the body plus two buttons
per anchor (top and bottom); n-gons are the button caps only.

Grid cost is `2 x (Resolution - 1)^2`, which dominates the total. For a leaner
mesh, Resolution 11 with Button Segments 8 gives 300 faces for 5 buttons -
buttons start reading as visibly octagonal below about 10 segments.

| Parameter | Default | Notes |
|---|---|---|
| Width / Depth | 0.60 | Footprint; make them unequal for a rectangle |
| Puff | 0.105 | Height above the seam plane |
| Squareness | 4.0 | 2 = round cushion, 4 = rounded square, 8+ = nearly sharp |
| Resolution | 15 | Grid divisions; forced odd so a centred button lands on a vertex |
| Tuft Depth / Spread | 0.55 / 0.30 | Dimple depth and reach |
| Buttons | 1 | `1` centre, `3` row along X, `5` quincunx |
| Button Spread | 0.45 | How far outer buttons sit from centre (ignored when Buttons = 1) |
| Button Radius / Height / Taper | 0.055 / 0.011 / 0.86 | |
| Button Segments | 10 | Raise for rounder buttons; below ~10 they read as octagonal |
| Origin | Bottom | `Bottom` sits on a surface by setting z; `Center` is symmetric |

## Conventions for new generators

Worth holding to - they are why these stay composable:

- **Geometry modules never touch `bpy.ops`, `bpy.context`, or the scene.**
  `build(...)` returns an unlinked mesh datablock. The operator layer owns
  scene insertion and placement. This keeps generators importable from a scene
  script and testable headlessly.
- **Object transforms stay at identity.** Size is baked into the mesh via
  parameters, never object scale. There is deliberately no `scale` property on
  the pillow operator: object scale would squash the button into an ellipse and
  break modifier widths, whereas Width/Depth regenerate proper geometry with the
  button still circular. `location`/`rotation` live on the operator because a
  primitive needs to know where to spawn - that is the right layer for them.
- **Quads, manifold, no stray triangles.** Check with `common.mesh_report()`.
- **Shading via bmesh edge flags**, not the `shade_auto_smooth` operator, so
  generators need no context and leave no modifier on the result.

Adding a generator: write `mything.py` exposing `build(...) -> Mesh`, add an
operator to `__init__.py`, list it in `CLASSES`, and add a line to `menu_func`.

## Note

`addon.py` at the repo root is a vendored copy of the
[blender-mcp](https://github.com/ahujasid/blender-mcp) add-on. It is **not** the
copy Blender runs - installing it copied it to Blender's own `scripts/addons/`
directory, so editing the file here has no effect.
