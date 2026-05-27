#!/usr/bin/env python3
"""Parametric STL insole generator - V1 simplified shell from geometry profile.

Produces a watertight binary STL of a solid insole shell.
Pure numpy + trimesh dependency only.
"""

import os
import numpy as np


def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _height_field(xy, profile, foot_length, foot_width):
    x, y, s = xy[:, 0], xy[:, 1], np.clip(xy[:, 1] / foot_length, 0, 1)
    hc, ac, ff, walls = profile["heel_cup"], profile["arch_curve"], profile["forefoot_flex"], profile["walls"]
    z = np.zeros(len(x))

    # Heel cup
    d = np.sqrt(x**2 + (y - foot_length * 0.05)**2)
    z += -hc["depth_mm"] * np.exp(-d**2 / (2 * hc["radius_mm"]**2)) * (1 - _smoothstep(0.15, 0.22, s))
    z += np.where(y < foot_length * 0.04, (1 - y / (foot_length * 0.04)) * hc["depth_mm"] * 0.5, 0) * np.clip(1 - s / 0.08, 0, 1)

    # Arch
    m = (s >= 0.20) & (s <= 0.40)
    if m.any():
        sl = (s[m] - 0.20) / 0.20
        mw = _smoothstep(-0.3, 1.0, np.clip(x[m] / (foot_width * 0.4), -1, 1))
        z[m] += ac["height_mm"] * np.sin(np.pi * sl) * mw

    m = (s >= 0.35) & (s <= 0.45)
    if m.any():
        fd = 1 - (s[m] - 0.35) / 0.10
        mw = _smoothstep(-0.3, 1.0, np.clip(x[m] / (foot_width * 0.4), -1, 1))
        z[m] += ac["height_mm"] * 0.5 * fd * mw

    # Flex grooves
    m = (s >= 0.55) & (s <= 0.80)
    if m.any():
        for ch in range(ff["channel_count"]):
            ch_c = 0.55 + (ch + 1) * 0.25 / (ff["channel_count"] + 1)
            z[m] += -ff["channel_depth_mm"] * np.exp(-(s[m] - ch_c)**2 / (2 * 0.03**2))

    # Toe rise
    m = s >= 0.80
    if m.any():
        z[m] += 3.0 * (s[m] - 0.80) / 0.20

    # Wall edges
    xn = np.clip(x / (foot_width * 0.5), -1, 1)
    ed = 1 - np.abs(xn)
    er = np.where(ed < 0.2, walls["height_mm"] * _smoothstep(0.2, 0, ed), 0)
    mt, lt = walls["medial"]["thickness_mm"], walls["lateral"]["thickness_mm"]
    if mt > lt:
        er[xn < 0] *= lt / mt
    z += er

    # Midfoot wave
    m = (s >= 0.40) & (s <= 0.55)
    if m.any():
        ws = (s[m] - 0.40) / 0.15
        z[m] += 1.5 * np.sin(np.pi * 2 * ws) * _smoothstep(0.1, 0.5, ws) * _smoothstep(0.5, 0.9, ws)

    return z


def generate_insole_stl(profile, output_path):
    """Build watertight insole STL via regular grid height field + trim to outline."""
    fl, fw, hw = 265.0, 80.0, 58.0

    # Regular grid covering the foot
    nx, ny = 60, 80
    x_vals = np.linspace(-fw * 0.65, fw * 0.65, nx)
    y_vals = np.linspace(-2, fl + 2, ny)
    xg, yg = np.meshgrid(x_vals, y_vals)
    grid_pts = np.column_stack([xg.ravel(), yg.ravel()])

    # Point-in-polygon test against foot outline
    def _outline_w(s):
        if s < 0.08: return hw * 0.45
        elif s < 0.20: return hw * 0.45 + (fw * 0.35 - hw * 0.45) * (s - 0.08) / 0.12
        elif s < 0.55: return fw * 0.35 + (fw * 0.42 - fw * 0.35) * (s - 0.20) / 0.35
        elif s < 0.70: return fw * 0.42 + (fw * 0.50 - fw * 0.42) * (s - 0.55) / 0.15
        elif s < 0.90: return fw * 0.50 - (fw * 0.15) * (s - 0.70) / 0.20
        return fw * 0.35 * (1 - (s - 0.90) / 0.10) + fw * 0.05

    mask = np.zeros(len(grid_pts), dtype=bool)
    for i, (px, py) in enumerate(grid_pts):
        s = py / fl
        if s < 0 or s > 1:
            continue
        cx = -fw * 0.02 if s < 0.55 else fw * 0.03
        half = _outline_w(s) + fw * 0.03
        if cx - half <= px <= cx + half:
            mask[i] = True

    pts = grid_pts[mask]
    n = len(pts)

    print(f"  Grid points inside outline: {n}")

    # Compute heights
    z_top = _height_field(pts, profile, fl, fw)
    z_lo = np.min(z_top) - 2.0  # Z for flat bottom, below lowest point
    z_bottom = np.full(n, z_lo)

    # Build vertices: top (0..n-1), bottom (n..2n-1)
    verts = np.vstack([
        np.column_stack([pts, z_top]),
        np.column_stack([pts, z_bottom]),
    ])

    # Delaunay triangulation of XY points for top/bottom faces
    from scipy.spatial import Delaunay
    tri = Delaunay(pts)
    faces_2d = tri.simplices

    # Top faces (keep winding = normals up after we export)
    top_f = faces_2d.copy()
    # Bottom faces (flipped for outward normals down)
    bot_f = (faces_2d + n)[:, [0, 2, 1]]

    # Find boundary edges
    boundary_edges = set()
    edge_to_face = {}
    for fi, face in enumerate(faces_2d):
        for j in range(3):
            a, b = sorted([face[j], face[(j + 1) % 3]])
            key = (a, b)
            if key in edge_to_face:
                edge_to_face.pop(key)  # shared edge, not boundary
            else:
                edge_to_face[key] = fi

    # Boundary edges are those appearing in only one face
    sorted_edges = sorted(edge_to_face.keys())
    boundary_verts = {}
    for a, b in sorted_edges:
        boundary_verts[a] = True
        boundary_verts[b] = True

    # Build side wall triangles from boundary vertices
    side_f = []
    bverts_ring = []
    # Reconstruct ring from edges
    remaining = set(range(len(sorted_edges)))
    ring = [sorted_edges[0][0], sorted_edges[0][1]]
    remaining.discard(0)

    while remaining:
        found = False
        last = ring[-1]
        for ei in list(remaining):
            a, b = sorted_edges[ei]
            if a == last:
                ring.append(b)
                remaining.discard(ei)
                found = True
                break
            elif b == last:
                ring.append(a)
                remaining.discard(ei)
                found = True
                break
        if not found:
            break

    # Build side faces
    if len(ring) >= 2:
        for i in range(len(ring)):
            a = i
            b = (i + 1) % len(ring)
            va, vb = ring[a], ring[b]
            side_f.append([va, va + n, vb + n])
            side_f.append([va, vb + n, vb])

    if side_f:
        all_faces = np.vstack([top_f, bot_f, np.array(side_f)])
    else:
        all_faces = np.vstack([top_f, bot_f])

    import trimesh
    mesh = trimesh.Trimesh(vertices=verts, faces=all_faces)
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())

    w = mesh.is_watertight
    print(f"  Watertight: {w}")
    if not w:
        mesh.fill_holes()

    mesh.export(output_path, file_type='stl')
    sz = os.path.getsize(output_path)
    bb = mesh.bounds
    d = bb[1] - bb[0]

    return {
        "path": output_path,
        "triangle_count": len(mesh.faces),
        "vertex_count": len(mesh.vertices),
        "watertight": bool(mesh.is_watertight),
        "bounding_box_mm": {
            "x": [round(bb[0][0], 1), round(bb[1][0], 1)],
            "y": [round(bb[0][1], 1), round(bb[1][1], 1)],
            "z": [round(bb[0][2], 1), round(bb[1][2], 1)],
        },
        "dimensions_mm": {
            "length": round(d[1], 1),
            "width": round(d[0], 1),
            "height": round(d[2], 1),
        },
        "file_size_bytes": sz,
        "file_size_kb": round(sz / 1024, 1),
    }
