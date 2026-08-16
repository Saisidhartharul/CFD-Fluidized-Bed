# Task C — Fluidized Bed Reactor: Build and Run Handout

Rocky DEM ↔ Fluent 2025 R2 two-way coupled gas–solid fluidized bed.
CFD Simulation for Energy Systems, SS 2026 · TUM Campus Straubing.

Everything described here lives in `mesh/FBR_project/`.
Source documents: `docs/CFD_SS2026_Project_Update_FBR.pdf` (the assignment) and
`docs/FBR_Tutorial_Workflow_Re500_Re2000_Rev2.docx` (the workflow this build follows).

---

## 1. Status — 16 Aug 2026

| Item | State |
|---|---|
| Fluid mesh | **Built and verified** |
| Fluent cases (both Re) | **Built and verified** |
| Settled particle bed | **Complete** — 80,214 particles, measured |
| Coupled projects (both Re) | **Configured**, not yet run to completion |
| Case A — Re = 500 | **Crashed** at output 35/400 (t = 0.700 s of 8.0 s), out of memory |
| Case B — Re = 2000 | **Halted** — launched into the same shortage, never started |
| Post-processing (§7, §8) | Not started |

Nothing in the model setup is implicated in the crashes. Case A ran correctly at the
expected pace for 35 outputs. Both failures were **resource** failures — see §2.

No Ansys processes are running and no stale `.lock` files remain. The project is ready
to launch as soon as §2 is satisfied.

---

## 2. Before you run anything — free the memory

**This is the single operational requirement, and both crashes came from ignoring it.**

The machine has 15.2 GB of RAM. A coupled run needs most of it. During the failed Case A,
Rocky's own progress file reported **free memory ≈ 0.68 GB from the very first output** —
it was starved from the start and died 48 minutes later with `bad allocation` once the bed
fluidized and the neighbour lists grew.

What was holding the memory:

| Application | Processes | Held |
|---|---|---|
| Vivaldi | 18 | 2.6 GB |
| Cursor | 16 | 2.1 GB |
| Edge WebView | 19 | 0.7 GB |

**Close the browser and the editor before launching.** That returns roughly 4.7 GB and
about triples the headroom. Check before you start:

```powershell
$os = Get-CimInstance Win32_OperatingSystem
"{0:N2} GB free of {1:N2} GB" -f ($os.FreePhysicalMemory/1MB), ($os.TotalVisibleMemorySize/1MB)
```

Aim for **6 GB or more free**. Below ~3 GB, expect the run to die partway.

Two further rules that follow from the same cause:

- **One coupled case at a time.** Two will not fit, and the second will either hang in
  Fluent startup or kill the first.
- **No build or setup scripts while a case is running.** They cost several hundred MB at
  exactly the wrong moment.

---

## 3. How to run

All commands from `mesh/FBR_project/`. Paths assume Ansys at `E:\CFD\ANSYS Inc\v252`.

### 3.1 Launch a production case

Rocky refuses to start a project that already holds results, so clear them first by
re-running the setup script for that case — it rebuilds the project from the settled bed:

```bash
# Case A (Re = 500, bubbling): 8 s, dt 5e-4, ~10 h
sed -e 's|^CASE = .*|CASE = "Re500"|' -e 's|^DURATION = .*|DURATION = 8.0|' \
    -e 's|^DT = .*|DT = 5.0e-4|' rocky_setup_case.py > _setup_Re500.py
rm -rf fbr_Re500.rocky fbr_Re500.rocky.files
"E:/CFD/ANSYS Inc/v252/rocky/bin/Rocky.exe" --headless \
    --script 'E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\_setup_Re500.py'

# then run it
"E:/CFD/ANSYS Inc/v252/rocky/bin/Rocky.exe" --simulate \
    'E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\fbr_Re500.rocky' \
    --ncpus 4 --use-gpu 1 --gpu-num 0 > run_Re500.log 2>&1 &
```

For Case B substitute `Re2000`, `DURATION = 4.0`, `DT = 4.0e-4`.

Resuming a crashed run via `Rocky.exe --resume` has **not been tested here**; a clean
restart as above is the reliable path.

### 3.2 Watch progress

```powershell
Get-Content 'fbr_Re500.rocky.files\simulation\rocky_simulation.rocky20.prg' -Tail 1
```

The JSON gives `current_output` (of 400), `current_simulation_time`, `eta` in seconds,
`n_particles`, and `free_mem`. Three things to watch:

- **`free_mem`** — if it drops below ~1 GB the run is on borrowed time.
- **`n_particles`** — must stay at 80,214. A steady decline means solids are leaving
  through the outlet.
- **`eta`** — settles after a few outputs.

### 3.3 Rebuild from scratch

```bash
python make_mesh.py -o fbr_column.msh                     # geometry + mesh
fluent 3ddp -g -t2 -i check_mesh.jou                      # verify mesh
bash build_all_cases.sh                                   # both .cas.h5
Rocky.exe --headless --script rocky_build_bed.py          # build bed project
Rocky.exe --simulate fbr_bed_settle.rocky --ncpus 4 --use-gpu 1 --gpu-num 0
Rocky.exe --headless --script rocky_measure_bed.py        # -> bed_measurements.txt
bash setup_both_cases.sh                                  # both coupled projects
```

Each step writes a `*.txt` log listing every setting applied and every one that failed.

---

## 4. Verified parameters — fill these into Appendix A

Values below were **read back from Fluent and Rocky after each step**, not copied from
the input scripts.

### 4.1 Geometry and mesh

| Quantity | Value |
|---|---|
| Domain | x −0.14…0.14, y −0.02…0.02, z 0…1.00 m |
| Slab depth | 0.04 m = 10 d_p (quasi-2D, standard for fluidized-bed DEM) |
| Total volume | 1.1200 × 10⁻² m³ |
| Divisions | 28 × 4 × 100 |
| Cells / nodes / faces | 11,200 hex / 14,645 / 36,912 |
| Cell size Δx | 10.0 mm |
| Δx / d_p | 2.50 |
| Cell volume / particle volume | 29.8 |
| Min orthogonal quality | 1.00000 |
| Max aspect ratio | 1.73205 |
| Named zones | inlet, outlet, wall-left, wall-right, wall-front, wall-back |

Hydraulic diameter: `D_h = 4A/P = 4(0.28×0.04)/(2(0.28+0.04)) = 0.070 m` — not 0.28 m.

### 4.2 Fluent (both cases)

| Setting | Case A · Re = 500 | Case B · Re = 2000 |
|---|---|---|
| Solver | pressure-based, transient, absolute | same |
| Gravity | (0, 0, −9.81) m/s² | same |
| Multiphase | off — solids live in Rocky | same |
| Energy | on | same |
| Viscous | k-ε standard, scalable wall functions | same |
| Air ρ, μ | 1.2 kg/m³, 1.8 × 10⁻⁵ Pa·s (constant) | same |
| Inlet velocity U₀ | 1.875 m/s | 7.500 m/s |
| Inlet turbulence | I = 5 %, D_h = 0.07 m | same |
| Inlet temperature | 293.15 K | same |
| Outlet | 0 Pa gauge, backflow 293.15 K, I = 5 %, D_h = 0.07 m | same |
| Walls | no-slip, stationary, adiabatic | same |
| P–V coupling | SIMPLE | same |
| Transient formulation | First Order Implicit *(mandatory)* | same |
| Time advancement | Fixed *(mandatory)* | same |
| Time step | 5 × 10⁻⁴ s | 4 × 10⁻⁴ s |
| Run length | 8.0 s | 4.0 s |
| Fluent steps | 16,000 | 10,000 |
| Residual criterion | Fluent defaults: 10⁻³ flow / 10⁻⁶ energy — meets the sheet's 10⁻³ | same |

### 4.3 Rocky

| Entity | Parameter | Value |
|---|---|---|
| Physics | Gravity | (0, 0, −9.81) m/s² |
| Physics | Numerical softening factor | 0.1 |
| Physics | Thermal model | enabled |
| Physics | Conduction correction | Morris et al. Area+Time |
| Default Particles | Density ρ_p | 1500 kg/m³ |
| Default Particles | Young's modulus | 1 × 10⁷ N/m² — *modelling assumption, report it* |
| Default Particles | Thermal conductivity | 1.4 W/m·K |
| Default Particles | Specific heat | 800 J/kg·K |
| sand4mm | Shape / size | sphere, 0.004 m @ 100 % |
| Bed Fill | Mass, temperature | 4.032 kg @ 363 K |
| Bed Fill | Seed coordinates | (0, 0, 0.02) m |
| Bed Fill | Box centre / dimensions | (0, 0, 0.22) / (0.28, 0.04, 0.44) m |

### 4.4 Coupling

| Setting | Value |
|---|---|
| Mode | 2-Way Fluent (`fluent_two_way`) |
| Fluent release | 2025 R2 |
| Convective heat transfer law | **RanzMarshall1952** — required, or particle temperature comes out flat |
| Drag law | **HuilinGidaspow2003** (Rocky default) — a modelling choice, report it |
| Lift / torque / virtual mass | Rocky defaults, unchanged |
| Coupling files kept | 0 = keep all, so Fluent `.dat` files survive for post-processing |
| Fluent solver processes | 4 (licence limit) |
| Rocky target | GPU 0 (RTX 4060), 4 CPU |
| Output cadence | Fluent outputs multiplier 40 (A) / 50 (B) → 0.02 s both |
| Output times | 400 (A) / 200 (B) |

> Rocky **rejects** a directly-set output time interval on a coupled case
> (*"Use Outputs multiplier instead"*). The multiplier is `interval / dt`.

---

## 5. Measured bed results — report these, not the targets

Sub-task (i): *"always report what exact values were used in your simulations."*

| Quantity | Measured | Doc expectation | |
|---|---|---|---|
| Particle count | 80,214 | ≈ 80,200 | ✓ |
| Bed mass | 4.0320 kg | 4.032 kg | ✓ |
| Solids volume V_s | 0.002688 m³ | 0.002688 m³ | ✓ |
| Settled height H (99th pct) | 0.4151 m | 0.38 – 0.42 m | ✓ |
| Highest particle centre | 0.4213 m | — | |
| **Actual α_p** | **0.578** | 0.60 – 0.63 | **below** |
| Δp_plateau from inventory | 3528.8 Pa | 3529 Pa | ✓ |
| Bed at rest — mean \|v\| | 2 × 10⁻⁵ m/s | ≈ 0 | ✓ |
| Bed at rest — max \|v\| | 8.8 × 10⁻³ m/s | ≈ 0 | ✓ |

### The α_p result is worth a paragraph in the report

The bed settled **looser**, not denser, than the workflow document predicted:
α_p = 0.578 against 0.60–0.63. In a slab only ten particle diameters deep, wall ordering
holds the packing below the random-close-packing value an unconfined bed would reach.

This is a real DEM result, not an error — and it is precisely the kind of thing a
two-fluid model *assumes* rather than predicts. It changes nothing downstream:
Δp_plateau is set by the bed **weight**, not by α_p, and the measured inventory gives
3528.8 Pa against the 3529 Pa reference.

### Hand-calculation reference targets (sub-task c)

```
Ar     = d_p^3 ρ_g (ρ_p − ρ_g) g / μ²      = 3.485 × 10⁶
Re_mf  (Ergun force balance)               = 332.2   → U_mf = 1.246 m/s
Re_mf  (Wen & Yu 1966, cross-check)        = 344.9   → U_mf = 1.293 m/s  (+3.8 %)
Δp_plateau = (ρ_p − ρ_g)(1 − ε) g H₀       = 3529 Pa
```

Δp_plateau is independent of d_p, of U₀ (provided U₀ > U_mf) and of Reynolds number.
It is the same in both cases and is your primary validation target.

---

## 6. Scope — read this before spending more compute

Checked against the assignment PDF, slides 6-2 and 6-3.

**Sub-task (e), verbatim:** *"Run **at least 1 case** that was assigned to your group
(see Excel file on Moodle): Bubbling, Turbulent, or Fast fluidized."*

**One case.** And the assignment is a **regime name** from a Moodle spreadsheet — not a
pair of Reynolds numbers. The Rev.2 workflow document asserts this group was assigned
Re = 500 and Re = 2000; that claim appears nowhere in the assignment PDF, and the Moodle
file is not on this machine, so it could not be verified.

**Check the spreadsheet before running both cases.** Everything in Rev.2 that follows
from the two-Reynolds premise — two production runs, the comparison figures, the
"5–7 days" estimate — rests on it.

| Point | Reading |
|---|---|
| Rocky DEM is the intended route | **Supported.** The sheet says "Load case as instructed in Chapter 14: Tutorial – Fluidized Bed" and links the Rocky DEM tutorial; sub-task (h) asks how Rocky differs from Fluent; and the slide 6-2 image is discrete spheres coloured by temperature in °C — a Rocky render, not a Fluent contour. |
| Sub-task (b) says "Eulerian multiphase … granular solid phase" | **Contradicts the above** — that is literal Fluent two-fluid vocabulary. The sheet reads as an older Fluent-only assignment repointed at the Rocky tutorial with (b) left unedited. Worth one email to the supervisors. |
| Number of cases required | **One.** Running two is the source of the wall-clock cost, not the physics. |
| d_p = 4 mm | Inside the sheet's 1–5 mm and sub-task (b)'s 3–5 mm. Chosen so Re = 500 and Re = 2000 straddle the bubbling→turbulent transition. |

---

## 7. What remains

| § | Task |
|---|---|
| §6 | Complete at least one production run |
| §7 | Solid volume fraction, gas velocity, particle temperature at start / middle / end |
| §8 | Pressure drop (two-cube method + Fluent inlet report), Ergun comparison, Δp–Re sweep |
| §9 | Written answers: 1/2/4-way coupling; Rocky vs Fluent particle modelling; why not FVM |
| App. A | Parameter sheet — §4 and §5 above fill it directly |
| App. D | Fluent Eulerian–Granular route, for the literal reading of sub-task (b) |
| Stage 1 | Tutorial baseline (`mesh/FBR_rocky/`) reached 0.5 s of the tutorial's 3 s |

---

## 8. File map

`mesh/FBR_project/`

| File | Purpose |
|---|---|
| `make_mesh.py` | Writes the Fluent mesh directly (box → structured hex) |
| `check_mesh.jou` | Fluent mesh check / quality |
| `fbr_column.msh` | The fluid mesh |
| `build_case.py`, `build_all_cases.sh` | Build both `.cas.h5` via the PyFluent settings API |
| `fbr_Re500.cas.h5`, `fbr_Re2000.cas.h5` | The two Fluent cases |
| `rocky_build_bed.py` | Builds the Rocky project and bed fill |
| `fbr_bed_settle.rocky` | The settled bed — shared initial condition |
| `rocky_measure_bed.py` → `bed_measurements.txt` | Bed height, α_p, at-rest check |
| `rocky_setup_case.py`, `setup_both_cases.sh` | Restart + 2-way coupling per case |
| `fbr_Re500.rocky`, `fbr_Re2000.rocky` | The two coupled projects |
| `chain.ps1` | Watcher that runs Case B after Case A (see §9) |
| `build_*.txt`, `setup_*.txt` | Per-step logs: every setting applied, every failure |

---

## 9. Gotchas

Hard-won; each cost time to find.

**Rocky headless scripting** (`Rocky.exe --headless --script foo.py`)

- The injected global is **`app`**, *not* `Rocky`. Also available: `project`, `script`.
- **Save the project before importing geometry.** Import calls `ObtainProjectFilename()`,
  which on an unsaved project opens a Save-As dialog; headless that returns `None` and the
  import dies with `'NoneType' object is not subscriptable`.
- `study.StartSimulation()` returns `True` from a `--script` session but **never launches
  RockySolver**. Run simulations from the CLI with `--simulate` instead.
- `--simulate` refuses to start if the project already holds results. Clear them first.
- Grid-function values: `gf.SetCurrentTimeStep(i)` then `gf.GetArray()`. There is no
  `GetValues()`.
- API stubs for the whole surface:
  `E:\CFD\ANSYS Inc\v252\rocky\bin\prepost_scripting_stubs\rocky30\plugins\api\*.pyi`

**Fluent**

- `fluent.exe 3ddp -g -tN -py -i journal.py` exposes the full **PyFluent settings API** as
  the global `solver`. Far more robust than TUI prompt sequences.
- End the journal with `solver.exit()` or the process hangs until timeout.
- `/file/read-mesh` is not valid here; `/file/read-case` reads `.msh` fine.

**Mesh generation**

- Fluent prints `Warning: Reversing N faces` for the outlet, wall-right and wall-back
  zones on read. **This is expected and harmless** — Fluent flips them itself and the mesh
  check passes. Do *not* "fix" it by listing the interior cell first: Fluent then aborts
  with a critical error while building the grid.

**Licensing and hardware**

- Licences come from `1055@licansysteach.lrz.de`. **The eduVPN tunnel must be up** or every
  checkout hangs with no useful error.
- 4 solver CPUs. Requesting 8 aborts with *"Fail to checkout additional CPU licenses
  required"*.
- Rocky uses the RTX 4060 (CUDA); Fluent uses the CPU cores. That split is the recommended
  configuration and is roughly an order of magnitude faster than CPU-only Rocky.

**Process supervision**

- A shell background job (`nohup … &`) is **torn down with its session**. The Ansys
  processes themselves are native and survive, but any watcher script must be launched
  detached: `Start-Process powershell -WindowStyle Hidden -File chain.ps1`.
- Do not probe for a running solver through a piped shell call and treat empty output as
  "finished" — a transient probe failure then reads as success and launches a second case
  on top of the first. `chain.ps1` now requires three consecutive confirmations *and*
  independent evidence the previous case completed, and refuses to launch otherwise.
- After killing a run, delete the stale `*.lock` file or Rocky will refuse to reopen the
  project.

---

*Values in §4 and §5 were read back from the solvers after each step. Timings were measured
on this machine: Rocky on an RTX 4060 (8 GB), Fluent on 4 of 8 Ryzen 7 7840HS cores,
15.2 GB RAM.*
