"""
Rocky: build the Task C project and settle the packed bed.
Workflow doc Rev.2, sections 5.5 and 5.5.1.

Produces  fbr_bed_settle.rocky  containing a settled monodisperse 4 mm bed of
4.032 kg (target alpha_p = 0.60 up to H0 = 0.40 m in a 0.28 x 0.04 x 1.00 m
column).  This DEM-only run is the shared initial condition for BOTH
production cases -- generate once, restart twice (doc section 5.5.2).

Run:  Rocky.exe --headless --script rocky_build_bed.py
"""
import traceback

PROJDIR = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project"
CAS = PROJDIR + r"\fbr_Re500.cas.h5"          # geometry source (same mesh both cases)
PROJ = PROJDIR + r"\fbr_bed_settle.rocky"
LOG = PROJDIR + r"\rocky_build_bed.txt"

# --- physical parameters (doc sections 5.5 / 5.5.1) ---------------------
RHO_P = 1500.0        # kg/m3   task value
YOUNGS = 1.0e7        # N/m2    softened contact stiffness, reported as an assumption
K_THERM = 1.4         # W/m.K
CP = 800.0            # J/kg.K
D_P = 0.004           # m       monodisperse 4 mm
BED_MASS = 4.032      # kg      = 0.28*0.04*0.40*0.60 * 1500
T_PART = 363.0        # K       hot particles in 293.15 K air
SEED = (0.0, 0.0, 0.02)
BOX_CENTER = (0.0, 0.0, 0.22)
BOX_DIMS = (0.28, 0.04, 0.44)
SETTLE_DURATION = 0.5     # s
SETTLE_OUTPUT = 0.05      # s

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


try:
    w("Rocky %s" % app.GetVersion())
    proj = app.CreateProject()
    study = proj.GetStudy() or proj.CreateStudy("FBR")
    do("study name", lambda: study.SetName("FBR"))

    # Save immediately: geometry import calls ObtainProjectFilename(), which on
    # an unsaved project pops a Save-As dialog.  Headless that dialog returns
    # None and the import dies with "'NoneType' object is not subscriptable".
    proj.SaveProject(PROJ)
    w("project saved up-front: %s" % PROJ)

    # ---- Physics (doc section 5.5) -------------------------------------
    ph = study.GetPhysics()
    do("gravity X = 0", lambda: ph.SetGravityXDirection(0.0))
    do("gravity Y = 0", lambda: ph.SetGravityYDirection(0.0))
    do("gravity Z = -9.81", lambda: ph.SetGravityZDirection(-9.81))
    do("numerical softening 0.1", lambda: ph.SetNumericalSofteningFactor(0.1))
    do("thermal model on", lambda: ph.SetEnableThermalModel(True))
    do("conduction correction Morris et al. Area+Time",
       lambda: ph.SetThermalCorrectionModel("morris_et_al_area_time"))

    # ---- Geometry: import the walls from the Fluent case ---------------
    walls = do("import walls from %s" % CAS,
               lambda: study.ImportWall(CAS, 1.0, False, None))
    names = [g.GetName() for g in study.GetGeometryCollection()]
    w("geometries imported: %s" % names)
    for expect in ("inlet", "outlet", "wall-left", "wall-right",
                   "wall-front", "wall-back"):
        if expect not in names:
            problems.append("geometry zone missing after import: %s" % expect)

    for g in study.GetGeometryCollection():
        try:
            g.SetThermalBoundaryType("adiabatic")
            notes.append("OK   %s thermal = adiabatic" % g.GetName())
        except Exception as e:
            notes.append("note %s thermal not set (%s)" % (g.GetName(), e))

    # ---- Material: Default Particles -----------------------------------
    mat = None
    for m in study.GetMaterialCollection():
        if m.GetName().strip().lower() == "default particles":
            mat = m
            break
    if mat is None:
        problems.append("could not find the 'Default Particles' material")
    else:
        do("use bulk density cleared", lambda: mat.SetUseBulkDensity(False))
        do("density 1500", lambda: mat.SetDensity(RHO_P))
        do("Young's modulus 1e7", lambda: mat.SetYoungsModulus(YOUNGS))
        do("thermal conductivity 1.4", lambda: mat.SetThermalConductivity(K_THERM))
        do("specific heat 800", lambda: mat.SetSpecificHeat(CP))

    # ---- Particle: one monodisperse 4 mm group -------------------------
    # Single size, not the tutorial's two: Re = rho*U0*d_p/mu is only
    # single-valued if d_p is (doc section 5.5).
    part = study.CreateParticle()
    do("particle name sand4mm", lambda: part.SetName("sand4mm"))
    try:
        w("particle shape = %s" % part.GetShape())
    except Exception:
        pass
    sd = part.GetSizeDistributionList()
    w("size distribution entries: %d" % len(sd))
    if len(sd) == 0:
        sd.New()
    do("size 0.004 m", lambda: sd[0].SetSize(D_P))
    do("cumulative 100%", lambda: sd[0].SetCumulativePercentage(100.0))
    while len(sd) > 1:
        del sd[1]

    # ---- Volumetric inlet: build the bed (doc section 5.5.1) -----------
    vi = do("create volumetric inlet", lambda: study.CreateVolumeFill(
        particle=part,
        name="Bed Fill",
        mass=BED_MASS,
        seed_coordinates=SEED,
        use_geometries_to_compute=False,
        box_center=BOX_CENTER,
        box_dimensions=BOX_DIMS,
    ))
    if vi is not None:
        do("all geometries enabled",
           lambda: vi.SetGeometries([g for g in study.GetGeometryCollection()]))
        props = vi.GetInputPropertiesList()
        w("inlet property rows: %d" % len(props))
        if len(props) == 0:
            props.New()
        do("bed particle = sand4mm", lambda: props[0].SetParticle(part))
        do("bed mass 4.032 kg", lambda: props[0].SetMass(BED_MASS))
        do("bed temperature 363 K", lambda: props[0].SetTemperature(T_PART))
        do("seed coordinates", lambda: vi.SetSeedCoordinates(SEED))
        do("box center", lambda: vi.SetBoxCenter(BOX_CENTER))
        do("box dimensions", lambda: vi.SetBoxDimensions(BOX_DIMS))

    # ---- Solver: cheap DEM-only settling run ---------------------------
    solver = study.GetSolver()
    do("duration 0.5 s", lambda: solver.SetSimulationDuration(SETTLE_DURATION))
    do("output interval 0.05 s", lambda: solver.SetTimeInterval(SETTLE_OUTPUT))
    # Rocky on the GPU, Fluent on the CPU cores, is the recommended split
    # (doc section 5.6).  The academic licence only covers 4 solver CPUs --
    # asking for more aborts with "Fail to checkout additional CPU licenses".
    do("simulation target GPU", lambda: solver.SetSimulationTarget("GPU"))
    do("target gpu 0", lambda: solver.SetTargetGpu(0), required=False)
    do("target gpus [0]", lambda: solver.SetTargetGpus([0]), required=False)
    do("processors 4", lambda: solver.SetNumberOfProcessors(4))

    # ---- Save, then run -------------------------------------------------
    w("\n=== saving project ===")
    proj.SaveProject(PROJ)
    w("saved %s" % PROJ)

    # The simulation itself is launched separately with
    #   Rocky.exe --simulate <proj> --ncpus 4 --use-gpu 1 --gpu-num 0
    # StartSimulation() from inside a --script session returns True without
    # ever launching RockySolver, so the run is driven from the CLI instead.
    w("\nproject built; run it with Rocky.exe --simulate")

except Exception:
    w("\nFATAL:\n" + traceback.format_exc())

w("\n=== NOTES (%d) ===" % len(notes))
for s in notes:
    w("  " + s)
w("\n=== PROBLEMS (%d) ===" % len(problems))
for s in problems:
    w("  " + s)
w("\n__ROCKY_BUILD_DONE__")
log.close()

try:
    app.Exit()
except Exception:
    import os
    os._exit(0)
