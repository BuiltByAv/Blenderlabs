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

Concentric quad rings from the centre button out to the seam. The seam loop is
shared between the top and bottom halves, so the mesh is closed, manifold, and
the seam is **planar** - trim or piping added later follows a flat ring instead
of cutting through at an angle.

The button is part of the same mesh: the innermost ring extruded up and
tapered, capped with one n-gon. One object, no loose parts.

At defaults: 312 verts, 290 faces - **288 quads, 0 triangles, 0 non-manifold
edges**, and the only 2 n-gons are the button caps.

| Parameter | Default | Notes |
|---|---|---|
| Width / Depth | 0.60 | Footprint; make them unequal for a rectangle |
| Puff | 0.105 | Height above the seam plane |
| Squareness | 4.0 | 2 = round cushion, 4 = rounded square, 8+ = nearly sharp |
| Segments / Rings | 24 / 5 | Angular and radial resolution |
| Tuft Depth / Spread | 0.55 / 0.30 | Centre dimple |
| Button Radius / Height / Taper | 0.055 / 0.011 / 0.86 | |
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
