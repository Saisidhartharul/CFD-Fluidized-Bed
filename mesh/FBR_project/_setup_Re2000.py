"""
Create a restart project from the settled bed and enable 2-way Fluent coupling.
Workflow doc Rev.2, sections 5.5.2, 5.5.3 and 5.6.

Both cases restart from the SAME settled bed, so any difference measured
between Re = 500 and Re = 2000 is not contaminated by a different random
packing (doc section 5.5.2).

CASE / U0 / DURATION are patched by the driver.
"""
import traceback

PROJDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
BED = PROJDIR + r"\fbr_bed_settle.rocky"

# ---- case parameters (driver rewrites this block) ----------------------
CASE = "Re2000"
DURATION = 4.0
DT = 4.0e-4
# ------------------------------------------------------------------------

CAS = PROJDIR + "\\fbr_" + CASE + ".cas.h5"
PROJ = PROJDIR + "\\fbr_" + CASE + ".rocky"
LOG = PROJDIR + "\\setup_" + CASE + ".txt"

OUTPUT_INTERVAL = 0.02     # s, doc section 5.6 -- 400 / 300 output times
FLUENT_PROCS = 4           # academic licence: 4-way parallel

log = open(LOG, "w", buffering=1)
notes, problems = [], []


def w(*a):
    log.write(" ".join(str(x) for x in a) + "\n")


def do(label, fn, required=True):
    try:
        r = fn()
        notes.append("OK   %s" % label)
        return r
    except Exception as e:
        (problems if required else notes).append("FAIL %s : %s" % (label, e))
        return None


def try_values(label, setter, getter, candidates):
    """Set the first candidate the API accepts; report what stuck."""
    for c in candidates:
        try:
            setter(c)
            notes.append("OK   %s = %r (now %r)" % (label, c, getter()))
            return c
        except Exception:
            continue
    problems.append("%s: none of %s accepted (current %r)" %
                    (label, candidates, getter()))
    return None


def dump(obj, title):
    w("\n----- %s" % title)
    for m in sorted(dir(obj)):
        if not (m.startswith("Get") or m.startswith("Is")):
            continue
        if m in ("GetWrappedClass", "GetClassName"):
            continue
        try:
            v = getattr(obj, m)()
            if callable(v):
                continue
            s = repr(v)
            w("   %-46s = %s" % (m, s[:160]))
        except Exception:
            pass


try:
    w("Rocky %s   building case %s" % (app.GetVersion(), CASE))

    # ---- restart from the settled bed ----------------------------------
    proj = app.OpenProject(BED)
    study = proj.GetStudy()
    times = list(study.GetTimeSet().GetValues())
    last = len(times) - 1
    w("settled bed: %d outputs, last t = %.3f s" % (len(times), times[-1]))

    do("save for restart -> %s" % PROJ,
       lambda: proj.SaveProjectForRestart(PROJ, last))
    app.CloseProject(check_save_state=False)

    # ---- reopen the restart project ------------------------------------
    proj = app.OpenProject(PROJ)
    study = proj.GetStudy()
    w("reopened %s" % proj.GetProjectFilename())
    try:
        t2 = list(study.GetTimeSet().GetValues())
        w("restart clock: %d outputs, t = %s" % (len(t2), t2))
    except Exception as e:
        w("restart timeset ! %s" % e)

    # ---- enable 2-way Fluent coupling (doc section 5.5.3) --------------
    cfd = study.GetCFDCoupling()
    cp = do("enable 2-Way Fluent against %s" % CAS,
            lambda: cfd.SetupTwoWayFluent(CAS))
    if cp is None:
        cp = cfd.GetCouplingProcess()
    w("coupling mode now: %s" % cfd.GetCouplingMode())
    w("coupling process : %s" % type(cp).__name__)

    if cp is not None:
        dump(cp, "coupling process state as created")

        # The Interactions sub-tab is per particle group: the laws live on the
        # CFD parameters list, not on the coupling process itself.
        params = cp.GetCFDParametersList()
        w("\nCFD per-particle parameter rows: %d" % len(params))
        for i, pp in enumerate(params):
            w("  row %d: valid convective heat transfer laws = %s"
              % (i, pp.GetValidConvectiveHeatTransferLawValues()))
            w("          valid drag laws = %s" % pp.GetValidDragLawValues())

            # Without a convective law the thermal model has nothing to do and
            # the particle-temperature deliverable (sub-task f) comes out flat.
            valid = [v for v in pp.GetValidConvectiveHeatTransferLawValues()
                     if v not in ("none", "custom")]
            preferred = [v for v in valid
                         if "ranz" in v.lower() or "marshall" in v.lower()] or valid
            if preferred:
                try_values("row %d convective heat transfer law" % i,
                           pp.SetConvectiveHeatTransferLaw,
                           pp.GetConvectiveHeatTransferLaw,
                           preferred)
            else:
                problems.append("row %d: no usable convective heat transfer law" % i)

            # Drag law is a modelling choice on the same footing as Gidaspow in
            # the Eulerian route -- sub-task (i) asks for it, so record it.
            w("          drag law in use  = %r" % pp.GetDragLaw())
            w("          lift law         = %r" % pp.GetLiftLaw())
            w("          torque law       = %r" % pp.GetTorqueLaw())

        do("Fluent solver processes = %d" % FLUENT_PROCS,
           lambda: cp.SetFluentSolverProcesses(FLUENT_PROCS), required=False)
        try:
            w("fluent releases available: %s" % cp.GetFluentReleases())
            w("fluent version currently : %s" % cp.GetFluentVersion())
        except Exception as e:
            w("fluent version query ! %s" % e)

        # Keep the Fluent .dat files: they are what make the gas field
        # post-processable in Fluent afterwards (doc section 4.3.5 note).
        do("coupling files kept = 0 (keep all)",
           lambda: cp.SetCouplingFilesKept(0), required=False)
        w("coupling files kept now: %r" % cp.GetCouplingFilesKept())

    # ---- solver settings (doc section 5.6) ------------------------------
    solver = study.GetSolver()
    do("duration %.1f s" % DURATION,
       lambda: solver.SetSimulationDuration(DURATION))
    # On a 2-way coupled case Rocky refuses a directly-set output time
    # interval ("Use Outputs multiplier instead..."), because its output
    # cadence is locked to the Fluent time step.  Ask for the doc's 0.02 s
    # indirectly, as a multiple of dt.
    mult = int(round(OUTPUT_INTERVAL / DT))
    do("Fluent outputs multiplier = %d  (%.4f s / %.1e s = %.2f s output)"
       % (mult, OUTPUT_INTERVAL, DT, mult * DT),
       lambda: solver.SetFluentOutputsMultiplier(mult))
    do("target GPU", lambda: solver.SetSimulationTarget("GPU"))
    do("gpu 0", lambda: solver.SetTargetGpu(0), required=False)
    do("processors 4", lambda: solver.SetNumberOfProcessors(4))

    w("\nsolver: duration=%s interval=%s multiplier=%s target=%s ncpus=%s" % (
        solver.GetSimulationDuration(), solver.GetTimeInterval(),
        solver.GetFluentOutputsMultiplier(),
        solver.GetSimulationTarget(), solver.GetNumberOfProcessors()))

    proj.SaveProject(PROJ)
    w("\nsaved %s" % PROJ)

except Exception:
    w("\nFATAL:\n" + traceback.format_exc())

w("\n=== NOTES (%d) ===" % len(notes))
for s in notes:
    w("  " + s)
w("\n=== PROBLEMS (%d) ===" % len(problems))
for s in problems:
    w("  " + s)
w("\n__SETUP_DONE__")
log.close()

try:
    app.Exit()
except Exception:
    import os
    os._exit(0)
