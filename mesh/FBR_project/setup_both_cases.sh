#!/bin/bash
# Create both coupled case projects from the one settled bed.
set -u
cd "$(dirname "$0")"

ROCKY="E:/CFD/ANSYS Inc/v252/rocky/bin/Rocky.exe"
HERE='E:\CFD_Project_Fluidized_Bed\mesh\FBR_project'

setup () {
    CASE=$1; DUR=$2; DT=$3
    echo "=============================================="
    echo "Setting up $CASE  (duration ${DUR} s, Fluent dt ${DT} s)"
    echo "=============================================="
    sed -e "s|^CASE = .*|CASE = \"$CASE\"|" \
        -e "s|^DURATION = .*|DURATION = $DUR|" \
        -e "s|^DT = .*|DT = $DT|" \
        rocky_setup_case.py > _setup_${CASE}.py
    rm -rf "fbr_${CASE}.rocky" "fbr_${CASE}.rocky.files" "setup_${CASE}.txt"
    "$ROCKY" --headless --script "${HERE}\\_setup_${CASE}.py" > "setup_${CASE}.log" 2>&1
    echo "rocky exit=$?"
    if [ -f "setup_${CASE}.txt" ]; then
        awk '/=== PROBLEMS/,0' "setup_${CASE}.txt"
        grep -E "convective heat transfer laws|drag law in use|^solver:" "setup_${CASE}.txt"
    else
        echo "!! no setup log produced"
    fi
}

setup Re500  8.0 5.0e-4
setup Re2000 6.0 2.0e-4

echo
echo "=== projects ==="
ls -la fbr_Re500.rocky fbr_Re2000.rocky 2>&1
