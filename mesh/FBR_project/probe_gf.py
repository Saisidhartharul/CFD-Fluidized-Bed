import traceback
out=open(r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\probe_gf_out.txt","w",buffering=1)
def w(*a): out.write(" ".join(str(x) for x in a)+"\n")
try:
    proj=app.OpenProject(r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\fbr_bed_settle.rocky")
    study=proj.GetStudy(); parts=study.GetParticles()
    gf=parts.GetGridFunction("Coordinate : Z")
    w("gf type: %s"%type(gf))
    w("gf members: %s"%[m for m in dir(gf) if not m.startswith("_")])
    g=parts.GetGeometry(10)
    w("\ngeom type: %s"%type(g))
    w("geom members: %s"%[m for m in dir(g) if not m.startswith("_")])
except Exception:
    w(traceback.format_exc())
w("DONE"); out.close()
try: app.Exit()
except Exception:
    import os; os._exit(0)
