# CFD Fluidized Bed Simulation

Computational fluid dynamics simulation of a gas-solid fluidized bed using OpenFOAM. The project models particle flow behaviour, pressure drop, and voidage distribution across varying fluidization regimes.

---

## Overview

| Item | Detail |
|---|---|
| Solver | OpenFOAM (twoPhaseEulerFoam / reactingTwoPhaseEulerFoam) |
| Particle type | Geldart Group B |
| Bed geometry | Rectangular column, 2D/3D |
| Drag model | Gidaspow |
| Turbulence | k-epsilon (gas phase) |
| Operating regime | Bubbling to turbulent fluidization |

---

## Repository Structure

```
cfd-fluidized-bed/
├── case/
│   ├── 0/                  # Initial and boundary conditions
│   ├── constant/           # Physical properties, turbulence settings
│   ├── system/             # fvSolution, fvSchemes, controlDict
│   ├── Allrun              # Full run script (mesh + solve)
│   └── Allclean            # Resets case to pre-run state
├── mesh/
│   ├── blockMeshDict       # Base mesh definition
│   └── snappyHexMeshDict   # Refined mesh config (if applicable)
├── postproc/
│   ├── plot_pressure_drop.py
│   ├── extract_voidage.py
│   └── requirements.txt
├── docs/
│   ├── mesh_independence.md
│   └── validation_notes.md
├── runs/
│   └── run_log.csv         # Simulation run history
├── .gitignore
└── README.md
```

> Result directories (`postProcessing/`, `processor*/`, time step folders) are excluded from version control via `.gitignore`.

---

## Getting Started

### Prerequisites

- OpenFOAM v9 or later (or ESI-OpenCFD v2212+)
- Python 3.9+ with packages listed in `postproc/requirements.txt`

### Running the simulation

```bash
# Clone the repo
git clone https://github.com/yourname/cfd-fluidized-bed.git
cd cfd-fluidized-bed/case

# Generate mesh
blockMesh

# Run solver
twoPhaseEulerFoam

# Or use the all-in-one script
./Allrun
```

### Cleaning the case

```bash
./Allclean
```

### Post-processing

```bash
cd postproc/
pip install -r requirements.txt
python plot_pressure_drop.py
python extract_voidage.py
```

---

## Key Parameters

| Parameter | Value |
|---|---|
| Particle diameter | 500 um |
| Particle density | 2500 kg/m3 |
| Gas (air) density | 1.225 kg/m3 |
| Gas viscosity | 1.81e-5 Pa.s |
| Minimum fluidization velocity (Umf) | ~0.25 m/s |
| Superficial gas velocity (U0) | 0.5 - 2.0 m/s |
| Initial bed height | 0.3 m |
| Column dimensions | 0.1 m x 0.6 m (W x H) |

---

## Validation

Pressure drop and voidage profiles are benchmarked against the Kunii and Levenspiel (1991) correlations and experimental data where available. Mesh independence was verified at three refinement levels — see `docs/mesh_independence.md` for details.

---

## Run Log

Simulation history is tracked in `runs/run_log.csv` with the following fields:

```
date, branch, mesh_cells, U0 (m/s), Re, Cd, avg_voidage, converged, notes
```

---

## Branching Convention

| Branch | Purpose |
|---|---|
| `main` | Validated baseline case |
| `study/U0-sweep` | Parametric velocity studies |
| `mesh/refine-v2` | Mesh refinement iterations |
| `feat/new-drag-model` | Testing alternative drag correlations |
| `docs/report` | Thesis / report write-up |

---

## Commit Convention

This project uses conventional commits:

```
feat: add Gidaspow drag model to fvModels
fix: correct inlet BC for Re = 5000
sim: U0 = 0.5 m/s baseline run, Cd converged to 0.42
docs: add mesh independence study to docs/
refactor: split Allrun into Allrun.mesh and Allrun.solve
```

---

## References

- Kunii, D. and Levenspiel, O. (1991). *Fluidization Engineering*. 2nd ed. Butterworth-Heinemann.
- Gidaspow, D. (1994). *Multiphase Flow and Fluidization*. Academic Press.
- OpenFOAM User Guide: https://www.openfoam.com/documentation/user-guide

---

