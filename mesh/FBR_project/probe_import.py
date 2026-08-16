"""Find the working way to import wall geometries from a Fluent .cas.h5."""
import traceback

PROJDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
LOG = PROJDIR + r"\probe_import_out.txt"
MINE = PROJDIR + r"\fbr_Re500.cas.h5"
TUT = r"E:\CFD_Project_Fluidized_Bed\mesh\dem_tut14_files\mesh\fluidized_bed.cas.h5"
MSH = PROJDIR + r"\fbr_column.msh"

out = open(LOG, "w", buffering=1)


def w(*a):
    out.write(" ".join(str(x) for x in a) + "\n")


def attempt(label, fn):
    proj = app.CreateProject()
    study = proj.GetStudy() or proj.CreateStudy("t")
    w("\n########## %s" % label)
    try:
        r = fn(study)
        names = [g.GetName() for g in study.GetGeometryCollection()]
        w("  returned: %r" % (r,))
        w("  geometries: %s" % names)
    except Exception:
        w("  EXCEPTION:\n" + traceback.format_exc())
    try:
        app.CloseProject(check_save_state=False)
    except Exception as e:
        w("  (close: %s)" % e)


# Does the tutorial's own .cas import?  That separates "my file" from "my call".
attempt("TUTORIAL cas, ImportWall(f)", lambda s: s.ImportWall(TUT))
attempt("MY cas, ImportWall(f)", lambda s: s.ImportWall(MINE))
attempt("MY cas, ImportWall(f, 1.0)", lambda s: s.ImportWall(MINE, 1.0))
attempt("MY cas, ImportGeometries(f)", lambda s: s.ImportGeometries(MINE))
attempt("MY msh, ImportWall(f)", lambda s: s.ImportWall(MSH))
attempt("MY cas, GetWallFromFilename", lambda s: s.GetWallFromFilename(MINE))

w("\nDONE")
out.close()
try:
    app.Exit()
except Exception:
    import os
    os._exit(0)
