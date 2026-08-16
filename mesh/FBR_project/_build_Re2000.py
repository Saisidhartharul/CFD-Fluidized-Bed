"""
Build the Task C Fluent case (workflow doc Rev.2, section 5.4).

Single-phase transient air case that Rocky attaches to for 2-way DEM-CFD
coupling.  Nothing is solved here -- the output is a .cas.h5 only.

Case is selected by the CASE variable below (patched by the driver script):
    Re = 500   ->  U0 = 1.875 m/s,  dt = 5e-4 s
    Re = 2000  ->  U0 = 7.500 m/s,  dt = 2e-4 s

Run:  fluent 3ddp -g -t4 -py -i build_case.py
"""
import traceback

# ---- case parameters (driver rewrites this block) -----------------------
CASE_NAME = "Re2000"
U0 = 7.500
DT = 4.0e-4
# ------------------------------------------------------------------------

MESH = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\fbr_column.msh"
OUTDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
CAS = OUTDIR + "\\fbr_" + CASE_NAME + ".cas.h5"
LOG = OUTDIR + "\\build_" + CASE_NAME + ".txt"

RHO_AIR = 1.2
MU_AIR = 1.8e-5
T_IN = 293.15
TURB_INTENSITY = 5.0
HYD_DIAM = 0.07
WALLS = ["wall-left", "wall-right", "wall-front", "wall-back"]

log = open(LOG, "w", buffering=1)
ok, bad = [], []


def w(*a):
    log.write(" ".join(str(x) for x in a) + "\n")


def setv(expr, value, required=True):
    """Assign `value` to the settings path `expr`; record what happened."""
    try:
        obj = eval(expr, globals())
    except Exception as e:
        (bad if required else ok).append("%s -> no such path (%s)" % (expr, e))
        return False
    try:
        obj.set_state(value)
    except Exception as e:
        (bad if required else ok).append("%s = %r FAILED: %s" % (expr, value, e))
        return False
    ok.append("%s = %r" % (expr, value))
    return True


def setany(exprs, value, label):
    """Try several candidate paths; the first that assigns wins."""
    for e in exprs:
        if setv(e, value, required=False):
            ok.append("  [%s] via %s" % (label, e))
            return True
    bad.append("%s: none of %s accepted %r" % (label, exprs, value))
    return False


def state(expr):
    try:
        w("\n--- %s" % expr)
        w(repr(eval(expr + ".get_state()", globals())))
    except Exception as e:
        w("  (state unavailable: %s)" % e)


try:
    S = solver.settings

    w("=== reading mesh ===")
    S.file.read_case(file_name=MESH)

    # ---- General (section 5.4) -----------------------------------------
    setv("S.setup.general.solver.type", "pressure-based")
    setv("S.setup.general.solver.time", "unsteady-1st-order")
    setv("S.setup.general.solver.velocity_formulation", "absolute")
    setv("S.setup.general.operating_conditions.gravity.enable", True)
    setany(["S.setup.general.operating_conditions.gravity.components"],
           [0.0, 0.0, -9.81], "gravity vector")

    # ---- Models --------------------------------------------------------
    setv("S.setup.models.energy.enabled", True)
    setv("S.setup.models.viscous.model", "k-epsilon")
    setany(["S.setup.models.viscous.k_epsilon_model"], "standard", "k-e variant")
    setany(["S.setup.models.viscous.near_wall_treatment.wall_treatment"],
           "scalable-wall-functions", "near-wall treatment")

    # ---- Materials: air at the task's fixed properties ------------------
    setany(["S.setup.materials.fluid['air'].density.value",
            "S.setup.materials.fluid['air'].density.constant"],
           RHO_AIR, "air density")
    setany(["S.setup.materials.fluid['air'].viscosity.value",
            "S.setup.materials.fluid['air'].viscosity.constant"],
           MU_AIR, "air viscosity")

    # ---- Boundary conditions -------------------------------------------
    vi = "S.setup.boundary_conditions.velocity_inlet['inlet']"
    setany([vi + ".momentum.velocity_magnitude.value",
            vi + ".momentum.velocity.value",
            vi + ".momentum.velocity_magnitude",
            vi + ".momentum.velocity"], U0, "inlet velocity")
    setany([vi + ".turbulence.turbulent_specification",
            vi + ".turbulence.turb_intensity_and_hydraulic_diameter"],
           "Intensity and Hydraulic Diameter", "inlet turb spec")
    setany([vi + ".turbulence.turbulent_intensity.value",
            vi + ".turbulence.turbulent_intensity"], TURB_INTENSITY / 100.0,
           "inlet turb intensity")
    setany([vi + ".turbulence.hydraulic_diameter.value",
            vi + ".turbulence.hydraulic_diameter"], HYD_DIAM,
           "inlet hydraulic diameter")
    setany([vi + ".thermal.temperature.value", vi + ".thermal.t.value",
            vi + ".thermal.temperature", vi + ".thermal.t"], T_IN,
           "inlet temperature")

    po = "S.setup.boundary_conditions.pressure_outlet['outlet']"
    setany([po + ".momentum.gauge_pressure.value",
            po + ".momentum.gauge_pressure",
            po + ".momentum.p.value"], 0.0, "outlet gauge pressure")
    setany([po + ".thermal.backflow_total_temperature.value",
            po + ".thermal.t0.value",
            po + ".thermal.backflow_total_temperature",
            po + ".thermal.t0"], T_IN, "outlet backflow total temperature")
    setany([po + ".turbulence.turbulence_specification"],
           "Intensity and Hydraulic Diameter", "outlet turb spec")
    setany([po + ".turbulence.backflow_turbulent_intensity"],
           TURB_INTENSITY / 100.0, "outlet backflow turb intensity")
    setany([po + ".turbulence.backflow_hydraulic_diameter"], HYD_DIAM,
           "outlet backflow hydraulic diameter")

    # Walls: default no-slip stationary adiabatic is already correct.
    try:
        present = list(S.setup.boundary_conditions.wall.keys())
        w("\nwall zones present: %s" % present)
        missing = [x for x in WALLS if x not in present]
        if missing:
            bad.append("wall zones missing from mesh: %s" % missing)
    except Exception as e:
        bad.append("could not list wall zones: %s" % e)

    # ---- Methods (section 5.4: SIMPLE + First Order Implicit) -----------
    setv("S.solution.methods.p_v_coupling.flow_scheme", "SIMPLE")
    # First Order Implicit is mandatory for 2-way coupling (doc section 4.2.2).
    setany(["S.solution.methods.transient_formulation"],
           "unsteady-1st-order", "transient formulation")

    # ---- Initialization -------------------------------------------------
    setv("S.solution.initialization.initialization_type", "standard")
    try:
        S.solution.initialization.compute_defaults.all_zones()
        ok.append("compute_defaults.all_zones()")
    except Exception as e:
        ok.append("compute_defaults.all_zones() unavailable: %s" % e)
    try:
        S.solution.initialization.standard_initialize()
        ok.append("standard_initialize()")
    except Exception as e:
        bad.append("standard_initialize() FAILED: %s" % e)

    # ---- Time advancement: fixed step, mandatory for coupling -----------
    setany(["S.solution.run_calculation.transient_controls.time_step_size",
            "S.solution.run_calculation.transient_controls.time_step_size.value"],
           DT, "time step size")
    # Fixed advancement is mandatory: adaptive stepping breaks lock-step with
    # Rocky's own time integration (doc section 4.2.2).
    setany(["S.solution.run_calculation.transient_controls.type"],
           "Fixed", "time advancement type")

    # ---- Report the resulting state -------------------------------------
    for e in ["S.setup.general.solver", "S.setup.general.operating_conditions.gravity",
              "S.setup.models.energy", "S.setup.models.viscous.model",
              "S.setup.models.viscous.k_epsilon_model",
              "S.setup.models.viscous.near_wall_treatment.wall_treatment",
              "S.setup.materials.fluid['air']", vi, po,
              "S.solution.methods.p_v_coupling", "S.solution.methods.transient_formulation",
              "S.solution.run_calculation.transient_controls"]:
        state(e)

    # ---- Write the case (do NOT solve) ----------------------------------
    w("\n=== writing case ===")
    S.file.write_case(file_name=CAS)
    w("wrote %s" % CAS)

except Exception:
    w("\nFATAL:\n" + traceback.format_exc())

w("\n=== APPLIED (%d) ===" % len(ok))
for s in ok:
    w("  " + s)
w("\n=== PROBLEMS (%d) ===" % len(bad))
for s in bad:
    w("  " + s)
w("\n__BUILD_DONE__")
log.close()

try:
    solver.exit()
except Exception:
    pass
