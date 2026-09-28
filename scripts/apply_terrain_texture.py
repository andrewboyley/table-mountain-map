#!/usr/bin/env python3
"""Apply the aerial texture to the 5 m terrain mesh, inside Blender.

Run it from Blender's Text Editor (Alt-P) with the cursor in the script, or
headless with `blender -b -P scripts/apply_terrain_texture.py`. It takes no
command-line options, so unlike the other scripts here it does not use
argparse -- Blender owns sys.argv in both entry paths.

What it builds
--------------
  texuv            FLOAT2 point attribute carrying base-texture UVs
  terrain_aerial   Principled BSDF over a two-texture blend
  TEX_BASE         3.2 m, full land extent         (cache/blender/tex_base_3p2.tif)
  TEX_MASSIF       1 m, massif window + blend mask (cache/blender/tex_massif_1m.tif)

The massif's own alpha band is the mix factor, so the 1 m detail crossfades
into the coarse base over the feathered window border with no extra nodes.

Why the base is 3.2 m
---------------------
At 2 m the base was a 996 MB texture; with 1 m detail on top, the pair needs
~1.7 GB of VRAM once mips are counted, against ~1.9 GB free on an RX 6500, and
EEVEE dies allocating it. 3.2 m is the finest size whose height still clears
the 16384 px GPU texture limit. The 1 m massif -- the part the camera flies
over -- is unchanged. build_texture_rasters.py documents the arithmetic.

Why a point attribute and not a UV layer
----------------------------------------
A UV layer is stored per loop. 21,538,938 verts make 86,015,412 loops, so the
UV data alone would be 688 MB of float pairs. A POINT-domain FLOAT2 attribute
is 172 MB and the Attribute node reads it identically. The texture resolution
is far below the 5 m vertex spacing, so nothing is lost.

Idempotent. Each stage saves the .blend, so an interrupted run never costs
more than the stage it died in -- which is what saved the first attempt when
EEVEE took Blender down mid-verification.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from osgeo import gdal

gdal.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "blender/table_mountain_pov.blend"
CACHE = ROOT / "cache/blender"
BASE_TIF = CACHE / "tex_base_3p2.tif"
MASSIF_TIF = CACHE / "tex_massif_1m.tif"

TERRAIN = "terrain_table_mountain"
MATERIAL = "terrain_aerial"
GEOSCENE = "BlenderGIS-2215.geoscene"
EXPECTED_VERTS = 21_538_938

# Ground positions the massif UV mapping must round-trip, as a self-check.
LANDMARKS = (
    (262137, 6238538),  # Maclear's Beacon
    (263287, 6242097),  # Lion's Head
    (258941, 6234773),  # Kloof
    (259068, 6229781),  # Sea Point
    (262017, 6233741),  # Devil's Peak
)


def socket(collection, identifier: str):
    """Look a socket up by identifier, not name.

    ShaderNodeMix exposes four inputs all named 'A' (A_Float, A_Vector,
    A_Color, A_Rotation), so inputs['A_Color'] raises KeyError.
    """
    for item in collection:
        if item.identifier == identifier:
            return item
    raise KeyError(f"{identifier} not in {[i.identifier for i in collection]}")


def banner(title: str) -> None:
    print(f"\n{'=' * 66}\n{title}\n{'=' * 66}", flush=True)


def save() -> None:
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
    print(f"   saved: {BLEND.stat().st_size / 1e6:.1f} MB", flush=True)


def rss_mb() -> float:
    return (
        int(open("/proc/self/statm").read().split()[1])
        * os.sysconf("SC_PAGE_SIZE")
        / 1e6
    )


def grid_of(path: Path):
    """Return (west, width, south, height) of a north-up raster, in metres."""
    ds = gdal.Open(str(path))
    gt = ds.GetGeoTransform()
    return (
        gt[0],
        gt[1] * ds.RasterXSize,
        gt[3] + gt[5] * ds.RasterYSize,
        -gt[5] * ds.RasterYSize,
    )


def stage_uv() -> None:
    banner("STAGE 1  texuv point attribute")
    mesh = bpy.data.objects[TERRAIN].data
    gs = sys.modules[GEOSCENE].GeoScene(bpy.context.scene)
    origin_x, origin_y = gs.getOriginPrj()
    bx, bw, by, bh = grid_of(BASE_TIF)
    print(f"   base grid  E {bx:.0f}..{bx + bw:.0f}  N {by:.0f}..{by + bh:.0f}")

    if "texuv" in mesh.attributes:
        mesh.attributes.remove(mesh.attributes["texuv"])
    attribute = mesh.attributes.new("texuv", "FLOAT2", "POINT")

    started = time.time()
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(count, 3)
    uv = np.empty(count * 2, dtype=np.float32)
    uv[0::2] = ((co[:, 0] + origin_x) - bx) / bw
    uv[1::2] = ((co[:, 1] + origin_y) - by) / bh
    del co
    u, v = uv[0::2].copy(), uv[1::2].copy()
    attribute.data.foreach_set("vector", uv)
    del uv
    mesh.update()

    back = np.empty(count * 2, dtype=np.float32)
    attribute.data.foreach_get("vector", back)
    error = max(np.abs(back[0::2] - u).max(), np.abs(back[1::2] - v).max())
    del back
    print(
        f"   {len(attribute.data):,} elements  u {u.min():.6f}..{u.max():.6f}"
        f"  v {v.min():.6f}..{v.max():.6f}"
    )
    print(
        f"   outside [0,1]: u {int(((u < 0) | (u > 1)).sum())}"
        f"  v {int(((v < 0) | (v > 1)).sum())}"
        f"   readback error {error:.3e}   {time.time() - started:.1f} s"
    )
    if error:
        raise RuntimeError(f"texuv readback mismatch: {error}")


def stage_images():
    banner("STAGE 2  load the texture rasters")
    loaded = []
    for path, tag in ((MASSIF_TIF, "TEX_MASSIF"), (BASE_TIF, "TEX_BASE")):
        existing = bpy.data.images.get(tag)
        if existing:
            bpy.data.images.remove(existing)
        image = bpy.data.images.load(str(path))
        image.name = tag
        image.colorspace_settings.name = "sRGB"
        image.alpha_mode = "STRAIGHT" if image.channels == 4 else "NONE"
        print(
            f"   {tag:<11} {image.size[0]}x{image.size[1]}  "
            f"channels={image.channels} depth={image.depth} alpha={image.alpha_mode}"
        )
        loaded.append(image)
    return tuple(loaded)


def stage_material(base_image, massif_image):
    banner("STAGE 3  shader: 3.2 m base, 1 m massif blended by the massif's alpha")
    bx, bw, by, bh = grid_of(BASE_TIF)
    mx, mw, my, mh = grid_of(MASSIF_TIF)
    print(f"   base    E {bx:.0f}..{bx + bw:.0f}  N {by:.0f}..{by + bh:.0f}")
    print(f"   massif  E {mx:.0f}..{mx + mw:.0f}  N {my:.0f}..{my + mh:.0f}")

    scale_u, loc_u = bw / mw, (bx - mx) / mw
    scale_v, loc_v = bh / mh, (by - my) / mh
    error = 0.0
    for east, north in LANDMARKS:
        u, v = (east - bx) / bw, (north - by) / bh
        error = max(
            error,
            abs((u * scale_u + loc_u) * mw + mx - east),
            abs((v * scale_v + loc_v) * mh + my - north),
        )
    print(
        f"   Mapping  Scale=({scale_u:.6f}, {scale_v:.6f}, 1)"
        f"  Location=({loc_u:.6f}, {loc_v:.6f}, 0)"
    )
    print(f"   round-trip error {error:.6f} m over {len(LANDMARKS)} landmarks")
    if error > 1e-6:
        raise RuntimeError(f"massif UV mapping does not round-trip: {error} m")

    material = bpy.data.materials.get(MATERIAL) or bpy.data.materials.new(MATERIAL)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()

    def node(node_type, name, x, y):
        made = tree.nodes.new(node_type)
        made.name = made.label = name
        made.location = (x, y)
        return made

    attribute = node("ShaderNodeAttribute", "texuv", -1100, 0)
    attribute.attribute_type = "GEOMETRY"
    attribute.attribute_name = "texuv"

    base = node("ShaderNodeTexImage", "base_3p2", -800, 250)
    base.image, base.interpolation, base.extension = base_image, "Smart", "EXTEND"
    base.label = "base 3.2 m - full land extent"

    mapping = node("ShaderNodeMapping", "to_massif_uv", -800, -150)
    mapping.vector_type = "POINT"
    mapping.inputs["Scale"].default_value = (scale_u, scale_v, 1.0)
    mapping.inputs["Location"].default_value = (loc_u, loc_v, 0.0)

    detail = node("ShaderNodeTexImage", "massif_1m", -520, -150)
    detail.image, detail.interpolation, detail.extension = (
        massif_image,
        "Smart",
        "EXTEND",
    )
    detail.label = "detail 1 m - massif window"

    blend = node("ShaderNodeMix", "blend_by_detail_alpha", -200, 100)
    blend.data_type, blend.blend_type, blend.clamp_factor = "RGBA", "MIX", True
    blend.label = "fac = massif alpha"

    bsdf = node("ShaderNodeBsdfPrincipled", "surface", 120, 100)
    output = node("ShaderNodeOutputMaterial", "out", 480, 100)

    link = tree.links.new
    link(attribute.outputs["Vector"], base.inputs["Vector"])
    link(attribute.outputs["Vector"], mapping.inputs["Vector"])
    link(mapping.outputs["Vector"], detail.inputs["Vector"])
    link(base.outputs["Color"], socket(blend.inputs, "A_Color"))
    link(detail.outputs["Color"], socket(blend.inputs, "B_Color"))
    link(detail.outputs["Alpha"], socket(blend.inputs, "Factor_Float"))
    link(socket(blend.outputs, "Result_Color"), bsdf.inputs["Base Color"])
    link(bsdf.outputs["BSDF"], output.inputs["Surface"])
    for key, value in (("Roughness", 0.85), ("Metallic", 0.0)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.2

    obj = bpy.data.objects[TERRAIN]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    print(
        f"   {len(tree.nodes)} nodes, {len(tree.links)} links -> assigned to {obj.name}"
    )
    return material


def stage_verify(material) -> bool:
    """Analytic checks only. Rendering to verify is what crashed Blender the
    first time, and a render proves less about wiring than these do anyway."""
    banner("STAGE 4  verify")
    obj = bpy.data.objects[TERRAIN]
    mesh = obj.data
    tree = material.node_tree
    failures = []

    def check(label, condition, detail=""):
        if not condition:
            failures.append(label)
        print(f"   [{'PASS' if condition else 'FAIL'}] {label:<44} {detail}")

    check(
        "terrain vertex count",
        len(mesh.vertices) == EXPECTED_VERTS,
        f"{len(mesh.vertices):,}",
    )
    check(
        "texuv attribute present",
        "texuv" in mesh.attributes,
        f"{mesh.attributes['texuv'].data_type}/{mesh.attributes['texuv'].domain}"
        if "texuv" in mesh.attributes
        else "",
    )
    check("no modifier stack (real geometry)", len(obj.modifiers) == 0)
    check(
        "material assigned",
        len(mesh.materials) == 1 and mesh.materials[0] == material,
        material.name,
    )
    for tag in ("TEX_BASE", "TEX_MASSIF"):
        image = bpy.data.images.get(tag)
        check(
            f"image {tag} loaded",
            image is not None and image.has_data,
            f"{image.size[0]}x{image.size[1]}" if image else "MISSING",
        )
    check("8 links, all connected", len(tree.links) == 8, str(len(tree.links)))
    linked = {(link.from_node.name, link.to_node.name) for link in tree.links}
    for pair in (
        ("texuv", "base_3p2"),
        ("texuv", "to_massif_uv"),
        ("to_massif_uv", "massif_1m"),
        ("base_3p2", "blend_by_detail_alpha"),
        ("massif_1m", "blend_by_detail_alpha"),
        ("blend_by_detail_alpha", "surface"),
        ("surface", "out"),
    ):
        check(f"link {' -> '.join(pair)}", pair in linked)
    base_colour = tree.nodes["surface"].inputs["Base Color"]
    check(
        "base colour driven by the blend",
        bool(base_colour.links)
        and base_colour.links[0].from_node.name == "blend_by_detail_alpha",
    )

    print(
        "\n   "
        + (
            "ALL CHECKS PASSED"
            if not failures
            else f"{len(failures)} FAILED: {', '.join(failures)}"
        )
    )
    return not failures


def main() -> int:
    banner("environment")
    print(f"   blender {bpy.app.version_string}")
    print(f"   RSS {rss_mb():.0f} MB")
    try:
        import gpu

        print(
            f"   GPU {gpu.platform.renderer_get()} via {gpu.platform.backend_type_get()}"
        )
    except Exception as error:  # noqa: BLE001 - diagnostics only
        print(f"   GPU info unavailable: {error}")
    for path in (BLEND.parent, BASE_TIF, MASSIF_TIF):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing; run build_texture_rasters.py first"
            )

    stage_uv()
    save()
    base_image, massif_image = stage_images()
    save()
    material = stage_material(base_image, massif_image)
    save()
    ok = stage_verify(material)
    save()

    banner("done -- " + ("texture applied" if ok else "SEE FAILURES ABOVE"))
    print("   Both textures now clear the 16384 px GPU limit, so EEVEE binds them")
    print("   in ~1 GB of VRAM. Cycles CPU stays the fallback.")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
