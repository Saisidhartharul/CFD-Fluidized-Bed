#!/bin/bash
# Build both Fluent cases from build_case.py by patching its parameter block.
# Usage:  bash build_all_cases.sh
set -u
cd "$(dirname "$0")"

FLUENT="E:/CFD/ANSYS Inc/v252/fluent/ntbin/win64/fluent.exe"

build () {
    NAME=$1; U0=$2; DT=$3
    echo "=============================================="
    echo "Building case $NAME :  U0 = $U0 m/s   dt = $DT s"
    echo "=============================================="
    sed -e "s|^CASE_NAME = .*|CASE_NAME = \"$NAME\"|" \
        -e "s|^U0 = .*|U0 = $U0|" \
        -e "s|^DT = .*|DT = $DT|" \
        build_case.py > _build_${NAME}.py
    rm -f "build_${NAME}.txt" "fbr_${NAME}.cas.h5"
    "$FLUENT" 3ddp -g -t4 -py -i "_build_${NAME}.py" > "build_${NAME}.log" 2>&1
    echo "fluent exit=$?"
    if [ -f "build_${NAME}.txt" ]; then
        awk '/=== PROBLEMS/,0' "build_${NAME}.txt"
    else
        echo "!! no build log produced"
    fi
    ls -la "fbr_${NAME}.cas.h5" 2>&1
}

build Re500  1.875 5.0e-4
build Re2000 7.500 2.0e-4

echo
echo "=== summary ==="
ls -la fbr_Re500.cas.h5 fbr_Re2000.cas.h5 2>&1
