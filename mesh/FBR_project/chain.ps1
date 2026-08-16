# Wait for the running coupled case to finish, then launch Case B.
#
# Must be started detached (Start-Process -WindowStyle Hidden) rather than as a
# shell background job.
#
# HARDENED after a false positive on 16 Aug 2026: the original bash version
# probed for RockySolver via a piped PowerShell call, and when that probe
# transiently returned nothing it read the empty result as "Case A finished"
# and launched Case B on top of a still-running Case A. That launch died on
# "INTEL MKL ERROR: The paging file is too small" -- 15 GB of RAM will not hold
# two coupled cases -- so it was harmless, but only by luck.
#
# Three defences here:
#   1. A missing solver must be observed CONFIRMS_NEEDED times in a row.
#   2. Case A must independently show that it actually completed.
#   3. If it did not, REFUSE to launch rather than launching "anyway".

$ErrorActionPreference = 'Continue'
$here  = 'E:\CFD_Project_Fluidized_Bed\mesh\FBR_project'
$rocky = 'E:\CFD\ANSYS Inc\v252\rocky\bin\Rocky.exe'
$log   = Join-Path $here 'chain_watcher.log'
$aLog  = Join-Path $here 'run_Re500.log'
$aPrg  = Join-Path $here 'fbr_Re500.rocky.files\simulation\rocky_simulation.rocky20.prg'

$CONFIRMS_NEEDED = 3
$EXPECTED_OUTPUTS = 400

function Say($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    for ($i = 0; $i -lt 5; $i++) {
        try { Add-Content -Path $log -Value $line -Encoding utf8 -ErrorAction Stop; return }
        catch { Start-Sleep -Milliseconds 400 }
    }
}

# Returns $true / $false, or $null when the probe itself could not be trusted.
function Test-SolverRunning {
    try {
        $p = @(Get-Process RockySolver -ErrorAction SilentlyContinue)
        return ($p.Count -gt 0)
    } catch {
        return $null
    }
}

Say "chain watcher started (pid $PID), needs $CONFIRMS_NEEDED consecutive clear probes"

$clear = 0
while ($clear -lt $CONFIRMS_NEEDED) {
    Start-Sleep -Seconds 60
    $running = Test-SolverRunning
    if ($running -eq $null) { Say "probe failed, ignoring this tick"; continue }
    if ($running) { if ($clear -gt 0) { Say "solver back, resetting confirmations" }; $clear = 0 }
    else { $clear++; Say "no solver ($clear/$CONFIRMS_NEEDED)" }
}
Say "solver confirmed gone"

# ---- did Case A actually complete? -------------------------------------
$finished = $false
if ((Test-Path $aLog) -and (Select-String -Path $aLog -Pattern '"status": "FINISHED"' -Quiet)) {
    $finished = $true
    Say "Case A reported FINISHED"
} elseif (Test-Path $aPrg) {
    try {
        $last = (Get-Content $aPrg -Tail 1 | ConvertFrom-Json)
        Say ("Case A last output {0}/{1} at t = {2} s" -f $last.current_output, $EXPECTED_OUTPUTS, $last.current_simulation_time)
        if ($last.current_output -ge $EXPECTED_OUTPUTS) { $finished = $true }
    } catch { Say "could not parse Case A progress file" }
}

if (-not $finished) {
    Say "REFUSING to launch Case B: Case A did not complete."
    Say "Inspect run_Re500.log and the .prg progress file, then start Case B by hand:"
    Say "  Rocky.exe --simulate $here\fbr_Re2000.rocky --ncpus 4 --use-gpu 1 --gpu-num 0"
    Say "chain stopped"
    exit 1
}

# ---- Case B ------------------------------------------------------------
Say "launching Case B (Re=2000, 4 s at dt=4e-4)"
$out = Join-Path $here 'run_Re2000.log'
& $rocky --simulate (Join-Path $here 'fbr_Re2000.rocky') `
         --ncpus 4 --use-gpu 1 --gpu-num 0 *> $out
Say "Case B process exited, code=$LASTEXITCODE"

if ((Test-Path $out) -and (Select-String -Path $out -Pattern '"status": "FINISHED"' -Quiet)) {
    Say "Case B (Re=2000) completed successfully"
} else {
    Say "WARNING: Case B did not report FINISHED -- check run_Re2000.log"
}
Say "chain complete"
