"""
Measure the settled bed (workflow doc Rev.2, section 5.5.1 verification table):
particle count, settled bed height H, actual alpha_p, and whether the bed is
at rest.  These are reportable results, not just checks -- sub-task (i) asks
for the values actually used.
"""
import traceback
import numpy as np

PROJDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
PROJ = PROJDIR + r"\fbr_bed_settle.rocky"
LOG = PROJDIR + r"\bed_measurements.txt"

W, D = 0.28, 0.04       # column width, depth [m]
D_P = 0.004
RHO_P = 1500.0
V_SOLID_TARGET = W * D * 0.40 * 0.60      # 0.002688 m3
M_TARGET = V_SOLID_TARGET * RHO_P         # 4.032 kg

log = open(LOG, "w", buffering=1)


def w(*a):
    log.write(" ".join(str(x) for x in a) + "\n")


def arr(parts, name, ts):
    """Fetch a particle grid function as a numpy array at time step ts."""
    gf = parts.GetGridFunction(name)
    gf.SetCurrentTimeStep(ts)
    return np.asarray(gf.GetArray())


try:
    proj = app.OpenProject(PROJ)
    study = proj.GetStudy()
    parts = study.GetParticles()

    times = list(study.GetTimeSet().GetValues())
    last = len(times) - 1
    w("output times : %d   t = %.3f .. %.3f s" % (len(times), times[0], times[-1]))

    w("\navailable particle grid functions:")
    try:
        for n in parts.GetGridFunctionNames():
            w("   %s" % n)
    except Exception as e:
        w("   (unavailable: %s)" % e)

    n_part = parts.GetNumberOfParticles(last)
    w("\n=== PARTICLE COUNT ===")
    w("  simulated      : %d" % n_part)
    w("  doc prediction : ~80,200")

    # ---- positions -----------------------------------------------------
    z = None
    for cand in ("Coordinate : Z", "Coordinate : Nodal : Z", "Position : Z"):
        try:
            z = arr(parts, cand, last)
            w("\nz from grid function '%s'  (n=%d)" % (cand, len(z)))
            break
        except Exception:
            continue
    if z is None:
        try:
            geom = parts.GetGeometry(last)
            pts = np.asarray(geom.GetPoints())
            z = pts[:, 2]
            w("\nz from GetGeometry().GetPoints()  (n=%d)" % len(z))
        except Exception as e:
            w("\ncould not obtain particle z coordinates: %s" % e)

    if z is not None and len(z):
        m_actual = n_part * (np.pi * D_P ** 3 / 6.0) * RHO_P
        v_solid = n_part * (np.pi * D_P ** 3 / 6.0)
        w("\n=== BED INVENTORY ===")
        w("  target mass          : %.4f kg" % M_TARGET)
        w("  actual mass          : %.4f kg  (%d x %.3e m3 x %.0f)" %
          (m_actual, n_part, np.pi * D_P ** 3 / 6.0, RHO_P))
        w("  actual solids volume : %.6f m3  (target %.6f)" % (v_solid, V_SOLID_TARGET))

        w("\n=== SETTLED BED HEIGHT ===")
        w("  max particle z       : %.4f m" % z.max())
        for pct in (99.9, 99.5, 99.0, 98.0, 95.0):
            w("  z at %5.1f percentile : %.4f m" % (pct, np.percentile(z, pct)))

        # H taken at the 99th percentile: robust against the handful of
        # particles perched on the surface, which is what the eye reads as
        # "the top of the bed" in the 3D View.
        H = float(np.percentile(z, 99.0))
        alpha = v_solid / (W * D * H)
        w("\n  H (99th pct)         : %.4f m      (doc expects 0.38 - 0.42)" % H)
        w("  alpha_p = V_s/(W*D*H): %.4f        (doc expects 0.60 - 0.63)" % alpha)

        H999 = float(np.percentile(z, 99.9))
        w("  H (99.9th pct)       : %.4f m  ->  alpha_p = %.4f" %
          (H999, v_solid / (W * D * H999)))

        # Pressure-drop plateau depends on bed weight, not on alpha_p.
        dp = (RHO_P - 1.2) * (v_solid / (W * D)) * 9.81
        w("\n  dp_plateau from actual inventory : %.1f Pa   (doc reference 3529 Pa)" % dp)

    # ---- is the bed at rest? -------------------------------------------
    w("\n=== BED AT REST? ===")
    got = False
    for cand in ("Velocity : Translational : Absolute",
                 "Translational Velocity : Absolute",
                 "Velocity : Absolute"):
        try:
            v = arr(parts, cand, last)
            w("  '%s': mean %.5f  max %.5f m/s" % (cand, float(np.mean(v)), float(np.max(v))))
            got = True
            break
        except Exception:
            continue
    if not got:
        w("  (no absolute-velocity grid function found; checked component set below)")
        for cand in ("Velocity : Translational : X", "Velocity : Translational : Y",
                     "Velocity : Translational : Z"):
            try:
                v = arr(parts, cand, last)
                w("  %s: mean %.5f  max %.5f" % (cand, float(np.mean(np.abs(v))), float(np.max(np.abs(v)))))
            except Exception as e:
                w("  %s unavailable (%s)" % (cand, e))

except Exception:
    w("\nFATAL:\n" + traceback.format_exc())

w("\n__MEASURE_DONE__")
log.close()

try:
    app.Exit()
except Exception:
    import os
    os._exit(0)
