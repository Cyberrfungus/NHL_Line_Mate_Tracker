@echo off
setlocal

REM ── Move to the project folder no matter where this file is launched from ──
cd /d "%~dp0"

REM ── Get yesterday's date as YYYY-MM-DD using Python ────────────────────────
REM   Post-game data is always for yesterday's slate (games that just finished)
for /f %%d in ('py -c "from datetime import date, timedelta; print(date.today() - timedelta(days=1))"') do set GAMEDAY=%%d

echo.
echo ============================================================
echo   NHL LINE-MATE TRACKER — POST-GAME PIPELINE
echo   Scoring slate: %GAMEDAY%
echo ============================================================
echo.
echo   Run this AFTER all games are final (~midnight or later).
echo   If West Coast games are still live, wait and re-run.
echo.

REM ── Fetch goal chains ────────────────────────────────────────────────────────
echo [1/3] Fetching goal chains from NHL API...
py scripts\fetch_postgame.py chains --date %GAMEDAY%
if errorlevel 1 (
    echo   ERROR: fetch_postgame failed.
    echo   If games are still in progress, wait and re-run this file.
    goto :error
)
echo.

REM ── Score results ────────────────────────────────────────────────────────────
echo [2/3] Scoring predictions vs actual chains...
py scripts\score_results.py --date %GAMEDAY%
if errorlevel 1 (
    echo   WARNING: score_results returned an error.
    echo   If date is already scored, run: py scripts\score_results.py --date %GAMEDAY% --force
)
echo.

REM ── Analyze results ──────────────────────────────────────────────────────────
echo [3/3] Running win-rate analysis...
py scripts\analyze_results.py
echo.

REM ── Done ────────────────────────────────────────────────────────────────────
echo ============================================================
echo   POST-GAME COMPLETE
echo ============================================================
echo.
echo   results_log.csv updated for %GAMEDAY%
echo   Run analyze_results.py with --since / --until for date ranges:
echo     py scripts\analyze_results.py --since 2026-04-14 --until %GAMEDAY%
echo.
goto :end

:error
echo.
echo   Pipeline stopped due to error above.
echo.

:end
pause
endlocal
