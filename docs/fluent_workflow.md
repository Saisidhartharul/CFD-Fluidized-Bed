# ANSYS Fluent Workflow — FBR Project (TUM CFD SS2026, Task C: Fluidized Bed)

Step-by-step execution plan for the task sheet in `CFD_SS2026_Project_Update_FBR.pdf`.
Targets Fluent 2025 R2 (v252), which is the version in the task's documentation link.

---

## 0. Two things to resolve before you start

**0.1 — The documentation link may point at the wrong tutorial.**
The task sheet links to `.../v252/en/dem_tut/dem_tut_14.html`. The `dem_tut` path is the
**Rocky DEM** tutorial collection, not the Fluent tutorial guide (`flu_tut`). But sub-tasks
(b), (d), (e), (f), (g) describe Fluent's **Eulerian–Granular (Two-Fluid Model)** — granular
solid phase, k-ε on the gas phase, patched volume fraction, Ergun comparison. Those are
Fluent TFM concepts, not DEM concepts.

Reinforcing this: the task says to pick dₚ "for a reasonable total number of particles."
In a 2D Eulerian TFM there *is no* particle count — solids are a continuum. A particle
count only constrains a DEM run. See §9 for the numbers.

**Action:** ask Huber/Abdullayev which is intended. This guide covers the Fluent
Eulerian–Granular path, which satisfies every sub-task as written. §9 covers the Rocky
variant if that turns out to be the intent.

**0.2 — Which regime is your group assigned?**
Sub-task (e) requires *at least one* of Bubbling / Turbulent / Fast fluidized, per the
Excel file on Moodle. This drives your inlet velocity and, critically, your particle
diameter — see §2. Get this before choosing dₚ.

---

## 1. Reference numbers (compute these yourself for the report — sub-task c)

Given: ρₚ = 1500 kg/m³, ρg = 1.2 kg/m³, μ = 1.8×10⁻⁵ Pa·s, ε_mf = 0.40 (αₚ = 0.60),
spherical particles (φₛ = 1), g = 9.81 m/s².

### Minimum fluidization velocity

U_mf is the superficial gas velocity at which the upward drag force on the bed exactly
balances its net weight. Below it the bed is a fixed packed bed and Δp rises with U;
at U_mf the particles are just suspended and Δp stops rising — the pressure drop
plateaus at the bed's weight per unit area, and stays there for all higher velocities.

Derived by setting the Ergun packed-bed pressure gradient equal to the buoyant bed weight
per unit height:

```
1.75/(ε_mf³ φₛ) · Re_mf²  +  150(1-ε_mf)/(ε_mf³ φₛ²) · Re_mf  =  Ar
```

with `Ar = dₚ³ ρg (ρₚ - ρg) g / μ²` and `Re_mf = dₚ U_mf ρg / μ`.

Terminal velocity U_t from Haider & Levenspiel (1989) for spheres.

| dₚ [mm] | Ar | Re_mf | **U_mf [m/s]** | **U_t [m/s]** | Re_t |
|---:|---:|---:|---:|---:|---:|
| 1 | 5.45×10⁴ | 25.8 | **0.387** | **5.24** | 349 |
| 2 | 4.36×10⁵ | 103.1 | **0.773** | **8.01** | 1068 |
| 3 | 1.47×10⁶ | 207.6 | **1.038** | **10.01** | 2001 |
| 4 | 3.49×10⁶ | 332.2 | **1.246** | **11.66** | 3108 |
| 5 | 6.81×10⁶ | 473.9 | **1.422** | **13.09** | 4364 |

Sanity check at dₚ = 3 mm, U = U_mf = 1.038 m/s — Ergun gives
1752 Pa/m (viscous) + 7070 Pa/m (inertial) = **8822 Pa/m**, and the required gradient
(ρₚ−ρg)(1−ε)g = 1498.8 × 0.6 × 9.81 = **8822 Pa/m**. Exact match, as it must be.

Cross-check with Wen & Yu (1966), `Re_mf = √(33.7² + 0.0408 Ar) − 33.7`:
dₚ = 3 mm → U_mf = 1.068 m/s (vs 1.038 above, +3%). Report both; the agreement is a good
validation point for sub-task (c).

### Fluidized pressure-drop plateau

```
Δp_plateau = (ρₚ − ρg)(1 − ε) g H₀ = 1498.8 × 0.60 × 9.81 × 0.40 = 3529 Pa
```

**This is your single most important validation target.** Independent of dₚ and of U₀
(above U_mf). If your simulated bed Δp doesn't settle near ~3.5 kPa, something is wrong
with the patch, the BCs, or the packing limit.

> Note: these particles are **Geldart Group D** (large, dense, spoutable), not Group B.
> The repo README says Group B — that was written for a different parameter set and is
> stale. Group D beds spout and channel readily and are coarser-bubbling than Group B.
> Mention the classification in your report; it explains what you'll see.

---

## 2. Choose dₚ and U₀ for your assigned regime

Regime boundaries scale with U_mf and U_t from §1. Rules of thumb (Kunii & Levenspiel 1991;
Bi & Grace 1995 for the turbulent onset):

| Regime | Criterion | dₚ = 3 mm | dₚ = 1 mm |
|---|---|---|---|
| Fixed bed | U₀ < U_mf | < 1.04 | < 0.39 |
| Bubbling | ~2–4 U_mf | **2.0 – 4.0 m/s** | 0.8 – 1.5 m/s |
| Turbulent | ~U_c, roughly 4–7 U_mf | **5.0 – 7.0 m/s** | 1.8 – 2.7 m/s |
| Fast fluidized | U₀ > U_t (needs solids recirculation) | > 10.0 m/s | > 5.2 m/s |

**Recommendation by assignment:**

- **Bubbling** → dₚ = 3 mm, U₀ ≈ 2.5 m/s (≈ 2.4 U_mf). Comfortable, well-resolved bubbles.
- **Turbulent** → dₚ = 3 mm, U₀ ≈ 6 m/s. Workable.
- **Fast fluidized** → **use dₚ = 1 mm** (task allows 1–5 mm in the Details block; the 3–5 mm
  in sub-task (b) is a suggestion, and sub-task (i) explicitly permits deviation if reported).
  At 3 mm you need U₀ > 10 m/s in a 0.28 m column — the transit time through a 1 m column is
  ~0.1 s, your CFL-limited time step collapses, and without a recycle loop the bed simply
  blows out the top within a second. At 1 mm, U₀ ≈ 6 m/s is enough and it is tractable.
  **Also add a recycle/return** or accept that you are simulating a transient blow-out and
  say so explicitly.

Whatever you pick, sub-task (i) requires you to **state the exact values used**. Put a
parameter table at the front of your report.

---

## 3. Geometry and mesh

**Do this in 2D planar unless you have a specific reason not to.** A 2D bed is standard for
TFM fluidization studies, runs ~100× faster, and lets you do the whole velocity sweep for
sub-task (g). Note in the report that 2D over-predicts bubble size somewhat and suppresses
the third velocity component.

1. **DesignModeler / SpaceClaim**: rectangle 0.28 m (x) × 1.0 m (y).
   If the tutorial geometry is imported in mm, use **Scale** in Fluent's Domain ribbon
   (`Domain → Mesh → Scale → Convert Units mm → m`) and **verify** with
   `Domain → Mesh → Info → Size` that the bounding box reads 0.28 × 1.0 (sub-task a).
2. **Named selections** — create these in the mesher, not after (sub-task a):
   - `inlet` — bottom edge (y = 0)
   - `outlet` — top edge (y = 1.0)
   - `wall-left`, `wall-right` — the two vertical edges
3. **Mesh**: uniform quadrilateral, Element Size **4 mm**.
   → 70 × 250 = **17,500 cells**.

   Sizing rationale: TFM closures assume the cell is large compared to a particle but small
   compared to a bubble. Target **Δx ≈ 2–10 dₚ**. At dₚ = 3 mm, 4 mm cells give Δx/dₚ = 1.3 —
   slightly under the ideal range, so also run **8 mm** (35 × 125 = 4,375 cells,
   Δx/dₚ = 2.7) and compare. This gives you a mesh-independence study for `docs/mesh_independence.md`
   at near-zero extra cost.

   Mapped/structured quads. `Mesh → Method → Quadrilateral Dominant` or a Multizone/Face
   Meshing mapped control. Check orthogonal quality > 0.9 (trivially satisfied for a
   uniform quad mesh).

---

## 4. Fluent setup

Launch: **2D, Double Precision, Serial or 4 cores.** Double precision matters — volume
fraction packing near 0.63 is sensitive.

### 4.1 General (sub-task a)
- Solver: **Pressure-Based**, **Transient**, **Planar**, Absolute velocity.
- Gravity: **on**, `Y = -9.81 m/s²`. *Forgetting this is the single most common failure —
  the bed just sits there and nothing fluidizes.*

### 4.2 Models (sub-task b)
- **Multiphase → Eulerian**, Number of Eulerian Phases = **2**.
  - Leave "Dense Discrete Phase Model" OFF.
- **Viscous → k-epsilon (2 eqn), Standard**, Standard Wall Functions.
  - Multiphase Turbulence: **Mixture** (robust default, one shared k-ε field).
  - If you want to satisfy the task wording "k-ε turbulence *for gas phase*" literally,
    select **Per Phase** instead and enable turbulence only on air. It is less stable and
    ~30% slower. Mixture is the accepted practice for dense beds; state your choice and why.
  - Do **not** use "Dispersed" — it assumes a dilute secondary phase, which αₚ = 0.6 violates.
- **Energy: OFF** — see §7 on "particle temperature."

### 4.3 Materials
- `air`: ρ = **1.2 kg/m³** (constant, *not* ideal-gas), μ = **1.8e-5 kg/m-s**.
- Create new solid material `sand` (Fluent Database → copy any solid, or create):
  ρ = **1500 kg/m³**. Only density matters if energy is off.

### 4.4 Phases (sub-task b)
- **Phase 1 (primary)**: name `air`, material air.
- **Phase 2 (secondary)**: name `solids`, material sand, **Granular = ON**.
  - Diameter: **0.003 m** (or your chosen dₚ)
  - Granular Viscosity: **Gidaspow**
  - Granular Bulk Viscosity: **Lun et al.**
  - Frictional Viscosity: **Schaeffer**
  - Frictional Pressure: **Based-ktgf**; Friction Packing Limit: **0.61**
  - Angle of Internal Friction: **30°**
  - Solids Pressure: **Lun et al.**
  - Radial Distribution: **Lun et al.**
  - Granular Temperature Model: **Phase Property → Algebraic**
    (Algebraic is cheaper and adequate. Switch to **Partial Differential Equation** if you
    want a proper granular-temperature transport field for the sub-task (f) plot — see §7.)
  - **Packing Limit: 0.63**
- **Phase Interaction → Drag**: **gidaspow**.
  Gidaspow blends Ergun (dense, αg < 0.8) with Wen–Yu (dilute) — exactly right for a bed
  that spans both. Syamlal–O'Brien is the common alternative; if you have time, run one
  case with each and compare bed expansion for bonus credit (sub-task j).
- Restitution coefficient (air–solids and solids–solids): **0.9**.

### 4.5 Boundary conditions (sub-task d)

| Zone | Type | Settings |
|---|---|---|
| `inlet` | velocity-inlet | **Mixture tab**: Turbulent Intensity 5%, Hydraulic Diameter 0.28 m<br>**air tab**: Velocity Magnitude = U₀ (normal to boundary)<br>**solids tab**: Velocity = 0, **Volume Fraction = 0** |
| `outlet` | pressure-outlet | Gauge Pressure = 0 Pa<br>Backflow: solids Volume Fraction = **0**, Turb. Intensity 5%, D_h 0.28 m |
| `wall-left/right` | wall | **air**: No Slip<br>**solids**: No Slip (per task) |

> On the solids wall BC: the task says no-slip, so use it. Physically, Johnson–Jackson
> **partial slip** (Specularity Coefficient ≈ 0.2–0.5) is more realistic and is what the
> literature uses — no-slip over-damps the near-wall solids and slightly under-predicts bed
> expansion. Worth one comparison run and a paragraph (sub-task j).

### 4.6 Initialization and patching the packed bed (sub-task d)

This is the step people get wrong. Order matters.

1. **Define the bed region first.**
   `Domain → Adapt → Refinement Criteria` is *not* what you want.
   Use `Domain → Adapt → Cell Registers → New → Region`:
   - Shape: **Hex** (works for 2D as a rectangle)
   - Input Coordinates: X min = 0, X max = 0.28, Y min = 0, Y max = **0.40**
   - Name it `bed`, click **Save/Display** and confirm the highlighted region is the
     bottom 40% of the column.

2. **Standard Initialize.**
   `Solution → Initialization → Standard` (not Hybrid — Hybrid does not handle multiphase
   volume fractions well). Compute From: `inlet`. Ensure solids Volume Fraction = 0.
   Click **Initialize**.

3. **Patch.**
   `Solution → Initialization → Patch`:
   - Phase: **solids**
   - Variable: **Volume Fraction**
   - Value: **0.6**
   - Registers to Patch: **bed**
   - Click **Patch**.

4. **Verify before running.** Make a contour of solids Volume Fraction (Filled, Node Values
   off). You must see a sharp block of 0.6 from y = 0 to y = 0.40 and 0 above. If it is
   smeared or empty, the patch failed — redo step 3.

### 4.7 Solution methods and controls

- **Scheme: Phase Coupled SIMPLE**
- Gradient: Least Squares Cell Based
- Momentum: **First Order Upwind** for the first ~0.5 s, then switch to **Second Order Upwind**
- Volume Fraction: **First Order Upwind** initially → **QUICK** after startup
  (QUICK preserves the bed interface far better; first-order smears it badly)
- Turbulent KE / Dissipation: First Order Upwind → Second Order Upwind
- Transient Formulation: **First Order Implicit**
  (bounded and stable for volume fraction; Second Order Implicit is more accurate but
  more prone to unbounded αₛ — only try it once the case is running cleanly)

**Under-Relaxation Factors** — start conservative, relax once stable:

| Variable | Start | Once stable |
|---|---|---|
| Pressure | 0.3 | 0.5 |
| Momentum | 0.2 | 0.4 |
| Volume Fraction | 0.2 | 0.5 |
| Granular Temperature | 0.2 | 0.2 |
| Turbulent KE / Diss. | 0.5 | 0.8 |

**Residual Monitors**: set all Absolute Criteria to **1e-3** (this is the task's stated
minimum convergence criterion). Keep "Check Convergence" ticked.

### 4.8 Run controls

- **Time Step Size: 5e-4 s.** If you see divergence or floating-point errors in the first
  100 steps, drop to **1e-4 s** for 0.2 s, then step back up.
- **Max Iterations/Time Step: 40.** If Fluent is routinely hitting 40 without converging to
  1e-3, your time step is too big.
- **Number of Time Steps**: enough for **12–20 s** of physical time.
  At dt = 5e-4 that is 24,000–40,000 steps. Budget: on 4 cores, a 17.5k-cell 2D case runs
  roughly 3–8 hours for 15 s. Start it overnight.
- Reporting Interval: 1. Profile Update Interval: 1.

---

## 5. Data collection during the run

Set all of this up **before** you hit Calculate. Re-running to collect a forgotten report
is the main time sink in this project.

### 5.1 Pressure-drop report (sub-tasks e, g)

`Solution → Report Definitions → New → Surface Report → Area-Weighted Average`
- Field Variable: **Pressure → Static Pressure**, Phase: **mixture**
- Surface: **inlet**
- Name: `dp_bed`
- Tick **Report File**, **Report Plot**, and set Create Output Parameter.

Because the outlet is at 0 Pa gauge, `dp_bed` **is** the pressure drop across the bed
(plus the small dilute-freeboard contribution, which is negligible). Compare to the
3529 Pa target from §1.

### 5.2 Bed height / expansion monitor
`New → Volume Report → Volume Integral` of solids Volume Fraction over the fluid domain.
Should stay constant (mass conservation check). If it drifts down, solids are leaving
through the outlet — that means blow-out, expected only in fast fluidization.

### 5.3 Time-averaging (sub-task f — *essential*)

`Solution → Calculation Activities → Data Sampling for Time Statistics`
- Tick it, but **only enable it after the startup transient has died** (~3 s).
- Practical method: run 3 s with sampling off, pause, tick sampling on, then run to 15 s.
  You get statistics over 12 s of developed flow.
- Sampling Interval: 1.
- This creates `Mean Static Pressure`, `Mean Volume Fraction`, `Mean Velocity` fields you
  can contour directly.

### 5.4 Autosave and image capture (sub-task f needs start / middle / end)

`Solution → Calculation Activities → Autosave` — Save Data File Every **1000** time steps
(= every 0.5 s). You will want these for post-hoc plotting.

Also set up `Solution Animations` on a contour of solids Volume Fraction, writing to file
every 100 steps — this gives you a bubble-formation movie, which directly answers
"where do bubbles form and how do they coalesce?"

---

## 6. The velocity sweep for the Ergun comparison (sub-task g)

You need Δp vs U₀ spanning below and above U_mf. Do **not** try to ramp velocity within one
transient run — the bed hysteresis will contaminate the curve.

**Method:** 8–10 separate short runs. For dₚ = 3 mm (U_mf = 1.038 m/s):

```
U0 = 0.2, 0.4, 0.6, 0.8, 0.9, 1.0, 1.1, 1.3, 1.6, 2.0, 2.5  [m/s]
```

For each: initialize + patch fresh, run **2.0 s**, and time-average `dp_bed` over the
**last 1.0 s**. Points below U_mf reach steady state almost immediately (it's a fixed bed);
points above need the full 2 s for the bubbling to become statistically stationary.

Automate it with a Fluent journal so you aren't clicking for hours — write a `.jou` that
loops over velocities, patches, solves, and writes each report file.

**Compare against Ergun** for the packed-bed branch (U₀ < U_mf):

```
Δp/L = 150 μ (1-ε)² U₀ / (ε³ dₚ²)  +  1.75 ρg (1-ε) U₀² / (ε³ dₚ)
```

with L = H₀ = 0.40 m, ε = 0.40, dₚ = 0.003 m. Two terms: viscous (linear in U₀) and
inertial (quadratic). At Re_p ≈ 200 the **inertial term dominates** — at U_mf it's 7070 of
the 8822 Pa/m, i.e. 80%. Say this in the report; it's a real physical point about Group D
particles that most groups will miss.

Expected curve shape: quadratic rise following Ergun up to U_mf ≈ 1.04 m/s, then a flat
plateau at **≈ 3529 Pa** for all higher velocities. Some overshoot right at the transition
is physical (the bed must break its packed structure) and is a nice thing to note if you
capture it.

Use `postproc/plot_pressure_drop.py` (currently an empty placeholder in the repo) for this.

---

## 7. "Particle temperature" in sub-task (f) — read this

The task asks you to plot **particle temperature**. There are two things this could mean
and they are completely different:

1. **Granular temperature Θₛ** [m²/s²] — the KTGF measure of particle velocity fluctuation
   (the granular analogue of thermodynamic temperature). This is almost certainly what is
   meant: it comes free with the Eulerian–Granular model, requires no energy equation,
   and is the standard diagnostic for a fluidized bed. High Θₛ marks the vigorous,
   dilute bubble wakes; low Θₛ marks the dense emulsion.
   - To get a proper field: set Granular Temperature Model = **Partial Differential Equation**
     in the solids phase panel (§4.4). Contour it as
     `Contours → Phases... → Granular Temperature`, Phase = solids.

2. **Thermal temperature T** [K] — requires enabling the Energy equation, a heat-transfer
   coefficient model (**Gunn** is the standard for packed/fluidized beds), inlet/wall
   thermal BCs, and solids heat capacity. **The task sheet specifies no thermal boundary
   conditions and no heat source at all** — with a uniform 300 K everywhere, nothing
   happens and the plot is a flat field.

**Recommendation:** plot granular temperature, and add one sentence in the report stating
which interpretation you used and why. If you want to hedge, enable Energy with a
hot inlet (e.g. 400 K gas into a 300 K bed) as an "own test" under sub-task (j) — that
gives you a genuinely interesting thermal-front plot and covers both readings.

---

## 8. Answers to sub-task (h) — the written questions

### Coupling regimes

The classification is Elghobashi (1994), based on solids volume fraction αₛ:

| | αₛ range | What is modeled | Valid for |
|---|---|---|---|
| **1-way** | αₛ < 10⁻⁶ | Fluid moves particles. Particles do **not** affect the fluid. | Very dilute tracers, aerosols, spray dispersion |
| **2-way** | 10⁻⁶ – 10⁻³ | Momentum exchanged **both** ways — particle drag feeds back as a source term in the fluid momentum equation. Particles still don't see each other. | Dilute sprays, pneumatic transport, particle-laden jets |
| **4-way** | > 10⁻³ | 2-way **plus** particle–particle and particle–wall collisions/contacts. | Dense flows: **fluidized beds**, hoppers, packed beds, risers |

Your bed at αₛ = 0.60 is firmly **4-way**. This is exactly why the granular phase needs
KTGF closures (solids pressure, granular viscosity, radial distribution function) — those
terms *are* the continuum representation of the particle–particle collisions.

### Rocky (DEM) vs Fluent (Eulerian–Granular)

| | **Fluent Eulerian–Granular (TFM)** | **Rocky DEM** |
|---|---|---|
| Frame | Eulerian — solids as an interpenetrating **continuum** on the same mesh as the gas | Lagrangian — **every particle** tracked individually |
| Governing eqns | PDEs (mass + momentum per phase) solved by FVM | Newton–Euler **ODEs** per particle, explicitly time-integrated |
| Collisions | *Modeled* via KTGF closures (solids pressure, granular viscosity) | *Resolved* via contact laws (Hertz–Mindlin, linear spring–dashpot) with real stiffness, damping, friction |
| Particle shape | Spheres only, single diameter (or a few discrete bins) | Arbitrary — polyhedra, fibers, flexible/breakable particles |
| Size distribution | Awkward — needs one extra phase per size class | Native polydispersity |
| Cost | Independent of particle count; scales with **cell count** | Scales with **particle count**; ~10⁵–10⁷ particles feasible on GPU |
| Industrial scale | Yes | Only for coarse particles / small domains |
| Coupling | Inherently 4-way through the closures | Inherently 4-way, resolved directly; couples to Fluent 1-way, 2-way, or 4-way (with volume displacement) |

Summary: **TFM trades particle-level fidelity for scalability.** It cannot tell you contact
forces, segregation by shape, attrition, or what an individual particle did — but it will
run a full industrial reactor. DEM gives you all of that but the cost scales with particle
count, so you are limited to lab scale or coarse particles.

### Why not use finite volume methods for particle modeling?

FVM is a **continuum** discretization. It integrates conservation PDEs over control volumes
and needs the field variables to be well-defined continuum quantities over each cell. That
fails for particles on three counts:

1. **The governing equations are the wrong type.** A particle obeys Newton–Euler ODEs
   (`m dv/dt = ΣF`, `I dω/dt = ΣT`) — six ODEs per particle, coupled through discrete,
   instantaneous, non-smooth contact events. There is no PDE to discretize over a mesh.

2. **Contacts are discontinuous.** Collisions produce impulsive force changes over
   microsecond timescales. FVM's implicit time-marching and flux-based spatial
   discretization are built for smooth fields, not for the non-smooth, event-driven
   mechanics of contact.

3. **Resolving particles with FVM is prohibitively expensive.** You *can* do it —
   particle-resolved DNS with immersed boundaries — but it needs ~20+ cells across each
   particle diameter plus moving/deforming boundaries. For your bed, 10⁵–10⁶ particles ×
   ~10⁴ cells each is ~10⁹–10¹⁰ cells with moving interfaces. That is a research-grade
   supercomputer run for a few seconds of physics.

So the field splits: **FVM for the fluid** (a genuine continuum), and either **DEM**
(track each particle, resolve contacts) or a **continuum granular closure** (TFM/KTGF —
pretend the solids are a fluid and model the collisions) for the solids. Fluent's
Eulerian–Granular takes the second route; Rocky takes the first.

---

## 9. If it turns out to be the Rocky DEM path

The "reasonable total number of particles" hint in the task Details makes sense only here.
Particle counts at αₚ = 0.6, H₀ = 0.40 m, 0.28 m wide:

| Domain | dₚ = 3 mm | dₚ = 5 mm |
|---|---:|---:|
| Full 3D (0.28 × 0.40 × 0.28 m) | ~1,330,000 | ~287,000 |
| **Thin slab (0.28 × 0.40 × 0.02 m)** | **~95,000** | **~20,500** |

A full 3D bed at 3 mm is a million-particle DEM run — heavy even on a GPU. **Use a thin
quasi-2D slab** (20–30 mm deep, periodic or frictionless front/back walls). ~20k–95k
particles is very comfortable for Rocky on a single GPU, and the slab geometry is standard
practice for validating fluidized-bed DEM against 2D experimental beds.

In that case: Fluent supplies the gas phase and Rocky the particles, coupled **2-way with
volume displacement** (which is effectively 4-way overall, since Rocky resolves the
particle–particle contacts itself).

---

## 10. Execution checklist

- [ ] Confirm assigned regime from the Moodle Excel file (§0.2)
- [ ] Confirm Fluent-TFM vs Rocky-DEM with the instructors (§0.1)
- [ ] Hand-compute U_mf for your chosen dₚ and write it up (sub-task c) — §1
- [ ] Build 0.28 × 1.0 m geometry, verify scale in meters (sub-task a) — §3
- [ ] Mesh at 4 mm; also mesh at 8 mm for mesh independence — §3
- [ ] Set transient + **gravity −9.81 y** (sub-task a) — §4.1
- [ ] Eulerian 2-phase, k-ε, granular solids with Gidaspow drag (sub-task b) — §4.2–4.4
- [ ] BCs: velocity inlet / pressure outlet / no-slip walls (sub-task d) — §4.5
- [ ] Initialize, patch αₛ = 0.6 to y = 0.40, **visually verify the patch** (sub-task d) — §4.6
- [ ] Set up `dp_bed` report + data sampling + autosave **before** running — §5
- [ ] Run 15 s of the assigned regime (sub-task e) — §4.8
- [ ] Plot time-avg αₛ, gas velocity vectors, granular temperature at start/mid/end (sub-task f) — §5.3, §7
- [ ] Velocity sweep, plot Δp vs U₀ against Ergun, check the 3529 Pa plateau (sub-task g) — §6
- [ ] Write up coupling regimes + Rocky vs Fluent + why-not-FVM (sub-task h) — §8
- [ ] **Parameter table with every value actually used** (sub-task i) — §2
- [ ] Optional extras: Syamlal–O'Brien drag, partial-slip walls, thermal front (sub-task j)

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Bed never moves | Gravity not enabled | §4.1 — set Y = −9.81 |
| Bed falls through the bottom | Gravity sign wrong (+9.81) | §4.1 |
| Δp ≈ 0 | Patch failed; no solids in the domain | Re-do §4.6, contour to verify |
| Δp far below 3529 Pa | Patched region wrong height, or αₛ patched < 0.6 | Check register Y max = 0.40 |
| Diverges in first 50 steps | Time step too large, URFs too high | dt → 1e-4, momentum URF → 0.2 |
| αₛ exceeds 0.63 / floating point error | Packing limit or frictional model misconfigured | Verify packing limit = 0.63, frictional packing limit = 0.61, URF(VF) = 0.2 |
| Solids leave through the outlet | U₀ above U_t, or backflow VF ≠ 0 | Set backflow solids VF = 0; check U₀ against §1 |
| Bed interface smears into mush | Volume fraction on First Order Upwind | Switch to QUICK (§4.7) |
| Hits 40 iterations every step | dt too large for the flow | Halve dt |
| Time-averaged plots look identical to instantaneous | Data Sampling never enabled | §5.3 |

---

## References

- Ergun, S. (1952). *Fluid flow through packed columns.* Chem. Eng. Prog. 48(2), 89–94.
- Wen, C.Y. & Yu, Y.H. (1966). *A generalized method for predicting the minimum fluidization velocity.* AIChE J. 12(3), 610–612.
- Haider, A. & Levenspiel, O. (1989). *Drag coefficient and terminal velocity of spherical and nonspherical particles.* Powder Technol. 58(1), 63–70.
- Kunii, D. & Levenspiel, O. (1991). *Fluidization Engineering*, 2nd ed. Butterworth-Heinemann.
- Elghobashi, S. (1994). *On predicting particle-laden turbulent flows.* Appl. Sci. Res. 52, 309–329.
- Gidaspow, D. (1994). *Multiphase Flow and Fluidization.* Academic Press.
- Bi, H.T. & Grace, J.R. (1995). *Flow regime diagrams for gas-solid fluidization and upward transport.* Int. J. Multiphase Flow 21(6), 1229–1236.
- Lun, C.K.K. et al. (1984). *Kinetic theories for granular flow.* J. Fluid Mech. 140, 223–256.
- ANSYS Fluent Theory Guide, Ch. 17 (Multiphase Flows) — Eulerian model and KTGF closures.
