#!/bin/bash
# Run the two production cases back to back.
#
# They must be sequential, not parallel: the academic licence covers 4-way
# Fluent parallel and one Rocky solver, and there is a single CUDA GPU.
# Two coupled runs at once would contend for all three.
#
# Case A is normally already running when this starts; the script waits it out
# and then launches Case B.
set -u
cd "$(dirname "$0")"

ROCKY="E:/CFD/ANSYS Inc/v252/rocky/bin/Rocky.exe"
HERE='E:\CFD_Project_Fluidized_Bed\mesh\FBR_project'

solver_running () {
    powershell -NoProfile -Command \
      "if (Get-Process RockySolver -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }" \
      2>/dev/null | tr -d '\r\n '
}

launch () {
    CASE=$1
    echo "[$(date '+%F %T')] launching $CASE"
    "$ROCKY" --simulate "${HERE}\\fbr_${CASE}.rocky" \
             --ncpus 4 --use-gpu 1 --gpu-num 0 > "run_${CASE}.log" 2>&1
    echo "[$(date '+%F %T')] $CASE finished, rocky exit=$?"
    tail -3 "run_${CASE}.log"
}

# ---- wait for whatever is running now (Case A) -------------------------
echo "[$(date '+%F %T')] waiting for the running solver to finish..."
while [ "$(solver_running)" = "yes" ]; do
    sleep 60
done
echo "[$(date '+%F %T')] no solver running"

if grep -q '"status": "FINISHED"' run_Re500.log 2>/dev/null; then
    echo "[$(date '+%F %T')] Case A (Re=500) completed successfully"
else
    echo "[$(date '+%F %T')] WARNING: Case A did not report FINISHED -- last lines:"
    tail -5 run_Re500.log 2>/dev/null
    echo "[$(date '+%F %T')] launching Case B anyway; inspect Case A before trusting it"
fi

# ---- Case B ------------------------------------------------------------
launch Re2000

echo "[$(date '+%F %T')] chain complete"
grep -c '"status": "ERROR"' run_Re500.log run_Re2000.log 2>/dev/null
