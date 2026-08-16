"""Dump the PyFluent settings-tree paths needed to build the FBR cases."""
import traceback

OUT = r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\discover_out.txt"
out = open(OUT, "w", buffering=1)


def w(*a):
    out.write(" ".join(str(x) for x in a) + "\n")


def kids(path):
    """Print the child names of a settings node given as a dotted path."""
    try:
        obj = eval(path, globals())
    except Exception as e:
        w("!! %-70s  %s" % (path, e))
        return None
    names = [m for m in dir(obj) if not m.startswith("_")]
    names = [n for n in names if n not in (
        'get_state', 'set_state', 'is_active', 'is_read_only', 'get_attr',
        'get_attrs', 'to_python_keys', 'before_execute', 'after_execute',
        'find_children', 'add_on_changed', 'children', 'command_names',
        'query_names', 'arguments', 'fluent_name', 'obj_name', 'path',
        'python_name', 'flproxy', 'parent', 'child_names', 'file_transfer_service',
        'scheme_doc', 'get_active_child_names', 'get_completer_info',
        'add_child_object', 'child_object_type', 'get_object_names',
        'user_creatable', 'rename', 'items', 'keys', 'values', 'get')]
    w("== %s" % path)
    w("   %s" % names)
    return obj


try:
    solver.settings.file.read_case(file_name=r"E:\CFD_Project_Fluidized_Bed\mesh\FBR_project\fbr_column.msh")
    w("read_case OK\n")
except Exception:
    w("read_case FAILED:\n" + traceback.format_exc())

for path in [
    "solver.settings",
    "solver.settings.setup",
    "solver.settings.setup.general",
    "solver.settings.setup.general.solver",
    "solver.settings.setup.general.operating_conditions",
    "solver.settings.setup.models",
    "solver.settings.setup.models.energy",
    "solver.settings.setup.models.viscous",
    "solver.settings.setup.models.viscous.options",
    "solver.settings.setup.models.viscous.near_wall_treatment",
    "solver.settings.setup.materials",
    "solver.settings.setup.materials.fluid",
    "solver.settings.setup.boundary_conditions",
    "solver.settings.setup.boundary_conditions.velocity_inlet",
    "solver.settings.setup.boundary_conditions.pressure_outlet",
    "solver.settings.solution",
    "solver.settings.solution.methods",
    "solver.settings.solution.methods.p_v_coupling",
    "solver.settings.solution.initialization",
    "solver.settings.solution.run_calculation",
    "solver.settings.solution.run_calculation.transient_controls",
    "solver.settings.file",
]:
    kids(path)

# Zone / material names actually present
try:
    w("\nfluid materials: %s" % list(solver.settings.setup.materials.fluid.keys()))
except Exception as e:
    w("fluid material keys ! %s" % e)
for bc in ("velocity_inlet", "pressure_outlet", "wall"):
    try:
        w("%s zones: %s" % (bc, list(getattr(solver.settings.setup.boundary_conditions, bc).keys())))
    except Exception as e:
        w("%s ! %s" % (bc, e))

# Detail on the specific leaves we must set
for path in [
    "solver.settings.setup.materials.fluid['air']",
    "solver.settings.setup.materials.fluid['air'].density",
    "solver.settings.setup.boundary_conditions.velocity_inlet['inlet']",
    "solver.settings.setup.boundary_conditions.velocity_inlet['inlet'].momentum",
    "solver.settings.setup.boundary_conditions.velocity_inlet['inlet'].turbulence",
    "solver.settings.setup.boundary_conditions.velocity_inlet['inlet'].thermal",
    "solver.settings.setup.boundary_conditions.pressure_outlet['outlet']",
    "solver.settings.setup.boundary_conditions.pressure_outlet['outlet'].momentum",
    "solver.settings.setup.boundary_conditions.pressure_outlet['outlet'].turbulence",
    "solver.settings.setup.boundary_conditions.pressure_outlet['outlet'].thermal",
]:
    kids(path)

w("\nDONE")
out.close()
solver.exit()
