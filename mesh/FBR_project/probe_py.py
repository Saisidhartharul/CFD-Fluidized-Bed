import sys
out = open(r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\probe_py_out.txt", "w", buffering=1)
out.write("PY JOURNAL RUNNING\n")
out.write("python %s\n" % sys.version)
g = sorted(k for k in globals().keys() if not k.startswith("_"))
out.write("globals: %s\n" % g)
for name in ("solver", "root", "session"):
    if name in globals():
        o = globals()[name]
        out.write("\n%s -> %s\n" % (name, type(o)))
        out.write("  members: %s\n" % [m for m in dir(o) if not m.startswith("_")][:60])
out.write("DONE\n")
out.close()
