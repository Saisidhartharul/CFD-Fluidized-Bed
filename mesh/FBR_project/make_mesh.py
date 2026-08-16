"""
Generate a structured hexahedral Fluent .msh for the Task C fluidized bed column.

Geometry (workflow doc Rev.2, section 5.1 / 5.2):
    x : -0.14 .. +0.14 m   WIDTH  0.28 m
    y : -0.02 .. +0.02 m   DEPTH  0.04 m  (quasi-2D slab, 10 d_p)
    z :  0.00 ..  1.00 m   HEIGHT 1.00 m  (vertical, gravity -Z)

Mesh (section 5.3): 10 mm cells -> 28 x 4 x 100 = 11,200 hex cells,
dx/dp = 2.5, cell volume / particle volume = 30. Comfortably above the
unresolved DEM-CFD coupling limit.

Named selections (section 5.2.3):
    inlet       z = 0     velocity-inlet
    outlet      z = 1.0   pressure-outlet
    wall-left   x = -0.14
    wall-right  x = +0.14
    wall-front  y = -0.02
    wall-back   y = +0.02

Usage:  python make_mesh.py [--orient A|B] [-o out.msh]

--orient selects which of the two possible (c0, c1) orderings is written for
each face.  Fluent's mesh check settles which one is right; see verify step.
"""
import argparse

NX, NY, NZ = 28, 4, 100
X0, X1 = -0.14, 0.14
Y0, Y1 = -0.02, 0.02
Z0, Z1 = 0.00, 1.00

# zone ids
Z_CELL = 1
Z_INTERIOR = 2
Z_INLET = 3
Z_OUTLET = 4
Z_WALL_LEFT = 5
Z_WALL_RIGHT = 6
Z_WALL_FRONT = 7
Z_WALL_BACK = 8
Z_NODE = 9

BC_INTERIOR = 2
BC_WALL = 3
BC_PRESSURE_OUTLET = 5
BC_VELOCITY_INLET = 10

FT_QUAD = 4


def node_id(i, j, k):
    """1-based node index."""
    return 1 + i + j * (NX + 1) + k * (NX + 1) * (NY + 1)


def cell_id(i, j, k):
    """1-based cell index; 0 means 'outside the domain'."""
    return 1 + i + j * NX + k * NX * NY


def build_faces():
    """Return {zone_id: [(n0,n1,n2,n3,c_neg,c_pos), ...]}.

    Every face is generated with its right-hand-rule normal pointing along the
    positive axis direction.  c_pos is the cell on the +side of that normal,
    c_neg the cell on the -side; 0 where there is no cell.
    """
    zones = {z: [] for z in (Z_INTERIOR, Z_INLET, Z_OUTLET,
                             Z_WALL_LEFT, Z_WALL_RIGHT, Z_WALL_FRONT, Z_WALL_BACK)}

    # X-normal faces: node loop y then z  ->  normal = y_hat x z_hat = +x
    for i in range(NX + 1):
        for j in range(NY):
            for k in range(NZ):
                n = (node_id(i, j, k), node_id(i, j + 1, k),
                     node_id(i, j + 1, k + 1), node_id(i, j, k + 1))
                c_neg = cell_id(i - 1, j, k) if i > 0 else 0
                c_pos = cell_id(i, j, k) if i < NX else 0
                if i == 0:
                    zones[Z_WALL_LEFT].append(n + (c_neg, c_pos))
                elif i == NX:
                    zones[Z_WALL_RIGHT].append(n + (c_neg, c_pos))
                else:
                    zones[Z_INTERIOR].append(n + (c_neg, c_pos))

    # Y-normal faces: node loop z then x  ->  normal = z_hat x x_hat = +y
    for j in range(NY + 1):
        for i in range(NX):
            for k in range(NZ):
                n = (node_id(i, j, k), node_id(i, j, k + 1),
                     node_id(i + 1, j, k + 1), node_id(i + 1, j, k))
                c_neg = cell_id(i, j - 1, k) if j > 0 else 0
                c_pos = cell_id(i, j, k) if j < NY else 0
                if j == 0:
                    zones[Z_WALL_FRONT].append(n + (c_neg, c_pos))
                elif j == NY:
                    zones[Z_WALL_BACK].append(n + (c_neg, c_pos))
                else:
                    zones[Z_INTERIOR].append(n + (c_neg, c_pos))

    # Z-normal faces: node loop x then y  ->  normal = x_hat x y_hat = +z
    for k in range(NZ + 1):
        for i in range(NX):
            for j in range(NY):
                n = (node_id(i, j, k), node_id(i + 1, j, k),
                     node_id(i + 1, j + 1, k), node_id(i, j + 1, k))
                c_neg = cell_id(i, j, k - 1) if k > 0 else 0
                c_pos = cell_id(i, j, k) if k < NZ else 0
                if k == 0:
                    zones[Z_INLET].append(n + (c_neg, c_pos))
                elif k == NZ:
                    zones[Z_OUTLET].append(n + (c_neg, c_pos))
                else:
                    zones[Z_INTERIOR].append(n + (c_neg, c_pos))

    return zones


def write_mesh(path, orient):
    n_nodes = (NX + 1) * (NY + 1) * (NZ + 1)
    n_cells = NX * NY * NZ
    zones = build_faces()
    n_faces = sum(len(v) for v in zones.values())

    dx = (X1 - X0) / NX
    dy = (Y1 - Y0) / NY
    dz = (Z1 - Z0) / NZ

    out = []
    w = out.append

    w('(0 "Task C fluidized bed column - 0.28 x 0.04 x 1.00 m, %d x %d x %d hex")'
      % (NX, NY, NZ))
    w('(0 "Generated for CFD SS2026 Task C, workflow Rev.2 section 5.3")')
    w('(2 3)')

    # ---- nodes -------------------------------------------------------
    w('(0 "Nodes")')
    w('(10 (0 1 %x 0 3))' % n_nodes)
    w('(10 (%x 1 %x 1 3)(' % (Z_NODE, n_nodes))
    for k in range(NZ + 1):
        z = Z0 + k * dz
        for j in range(NY + 1):
            y = Y0 + j * dy
            for i in range(NX + 1):
                x = X0 + i * dx
                w('%.10e %.10e %.10e' % (x, y, z))
    w('))')

    # ---- cells -------------------------------------------------------
    w('(0 "Cells")')
    w('(12 (0 1 %x 0))' % n_cells)
    w('(12 (%x 1 %x 1 4))' % (Z_CELL, n_cells))

    # ---- faces -------------------------------------------------------
    w('(0 "Faces")')
    w('(13 (0 1 %x 0))' % n_faces)

    order = [(Z_INTERIOR, BC_INTERIOR), (Z_INLET, BC_VELOCITY_INLET),
             (Z_OUTLET, BC_PRESSURE_OUTLET), (Z_WALL_LEFT, BC_WALL),
             (Z_WALL_RIGHT, BC_WALL), (Z_WALL_FRONT, BC_WALL),
             (Z_WALL_BACK, BC_WALL)]

    first = 1
    for zid, bc in order:
        faces = zones[zid]
        last = first + len(faces) - 1
        w('(13 (%x %x %x %x %x)(' % (zid, first, last, bc, FT_QUAD))
        # Every face is written with c0 on the +normal side.  On the outlet,
        # wall-right and wall-back zones that puts the 0 ("outside") entry
        # first, so Fluent reports "Reversing N faces" for those three zones on
        # read and flips them itself.  That warning is expected and harmless --
        # mesh check afterwards reports correct extents, volumes and quality.
        # Do NOT "fix" it by listing the real cell first: Fluent then aborts
        # with a critical error while building the grid.
        for n0, n1, n2, n3, c_neg, c_pos in faces:
            if orient == 'A':
                c0, c1 = c_pos, c_neg
            else:
                c0, c1 = c_neg, c_pos
            w('%x %x %x %x %x %x' % (n0, n1, n2, n3, c0, c1))
        w('))')
        first = last + 1

    # ---- zone names --------------------------------------------------
    w('(0 "Zone names")')
    w('(45 (%d fluid fluid)())' % Z_CELL)
    w('(45 (%d interior interior-fluid)())' % Z_INTERIOR)
    w('(45 (%d velocity-inlet inlet)())' % Z_INLET)
    w('(45 (%d pressure-outlet outlet)())' % Z_OUTLET)
    w('(45 (%d wall wall-left)())' % Z_WALL_LEFT)
    w('(45 (%d wall wall-right)())' % Z_WALL_RIGHT)
    w('(45 (%d wall wall-front)())' % Z_WALL_FRONT)
    w('(45 (%d wall wall-back)())' % Z_WALL_BACK)

    with open(path, 'w', newline='\n') as fh:
        fh.write('\n'.join(out) + '\n')

    print('wrote %s' % path)
    print('  orientation convention : %s' % orient)
    print('  nodes                  : %d' % n_nodes)
    print('  cells                  : %d  (%d x %d x %d)' % (n_cells, NX, NY, NZ))
    print('  faces                  : %d' % n_faces)
    for zid, _ in order:
        print('    zone %d : %6d faces' % (zid, len(zones[zid])))
    print('  cell size              : %.4f x %.4f x %.4f m' % (dx, dy, dz))
    print('  dx / d_p               : %.2f  (d_p = 4 mm)' % (dx / 0.004))
    print('  cell vol / particle vol: %.1f' %
          ((dx * dy * dz) / (3.14159265358979 * 0.004 ** 3 / 6)))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--orient', choices=['A', 'B'], default='A')
    ap.add_argument('-o', '--out', default='fbr_column.msh')
    a = ap.parse_args()
    write_mesh(a.out, a.orient)
