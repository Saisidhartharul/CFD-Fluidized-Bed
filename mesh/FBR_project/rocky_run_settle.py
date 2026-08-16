"""
Re-run the settling simulation on an existing project with a working
target/licence combination, then report the settled-bed measurements.

TARGET / NCPUS are patched by the driver script.
"""
import traceback

PROJDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
PROJ = PROJDIR + r"\fbr_bed_settle.rocky"
LOG = PROJDIR + r"\rocky_run_settle.txt"

TARGET = "GPU"
NCPUS = 4

log = open(LOG, "w", buffering=1)


def w(*a):
    log.write(" ".join(str(x) for x in a) + "\n")


try:
    proj = app.OpenProject(PROJ)
    study = proj.GetStudy()
    solver = study.GetSolver()

    w("before: target=%s ncpus=%s gpu=%s gpus=%s duration=%s interval=%s" % (
        solver.GetSimulationTarget(), solver.GetNumberOfProcessors(),
        solver.GetTargetGpu(), solver.GetTargetGpus(),
        solver.GetSimulationDuration(), solver.GetTimeInterval()))
    w("valid targets: %s" % solver.GetValidSimulationTargetValues())

    solver.SetNumberOfProcessors(NCPUS)
    solver.SetSimulationTarget(TARGET)
    if TARGET in ("GPU", "MULTI_GPU"):
        try:
            solver.SetTargetGpu(0)
        except Exception as e:
            w("SetTargetGpu ! %s" % e)
        try:
            solver.SetTargetGpus([0])
        except Exception as e:
            w("SetTargetGpus ! %s" % e)

    w("after:  target=%s ncpus=%s gpu=%s gpus=%s" % (
        solver.GetSimulationTarget(), solver.GetNumberOfProcessors(),
        solver.GetTargetGpu(), solver.GetTargetGpus()))

    proj.SaveProject(PROJ)

    w("\n=== starting settling run (target=%s, ncpus=%d) ===" % (TARGET, NCPUS))
    started = study.StartSimulation(skip_summary=True, delete_results=True,
                                    non_blocking=False)
    w("StartSimulation returned %s" % started)

    vals = []
    try:
        vals = list(study.GetTimeSet().GetValues())
    except Exception as e:
        w("timeset ! %s" % e)
    w("output times: %d, last = %s s" % (len(vals), vals[-1] if vals else None))

    if vals and vals[-1] > 0:
        proj.SaveProject(PROJ)
        w("saved project with results")
    else:
        w("!! simulation did not advance -- see rocky_simulation.rocky20.log")

except Exception:
    w("\nFATAL:\n" + traceback.format_exc())

w("\n__RUN_DONE__")
log.close()

try:
    app.Exit()
except Exception:
    import os
    os._exit(0)
