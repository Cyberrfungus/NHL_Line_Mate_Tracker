@echo off
setlocal

REM ── Move to the project folder no matter where this file is launched from ──
cd /d "%~dp0"

REM ── Get today's date as YYYY-MM-DD using Python ────────────────────────────
for /f %%d in ('py -c "from datetime import date; print(date.today())"') do set TODAY=%%d

echo.
echo ============================================================
echo   NHL LINE-MATE TRACKER — PRE-GAME PIPELINE
echo   Date: %TODAY%
echo ============================================================
echo.

REM ── Pull latest scripts from GitHub ────────────────────────────────────────
echo [1/5] Pulling latest code from GitHub...
git pull origin claude/init-repo-setup-x14pg
if errorlevel 1 (
    echo   WARNING: git pull failed. Continuing with local scripts.
)
echo.

REM ── Lineups ─────────────────────────────────────────────────────────────────
echo [2/5] Fetching lineups...
py scripts\fetch_lineups_nhl.py --date %TODAY%
if errorlevel 1 (
    echo   ERROR: fetch_lineups_nhl failed. Check your internet connection.
    goto :error
)
echo.

REM ── Goalies ─────────────────────────────────────────────────────────────────
echo [3/5] Fetching starting goalies...
py scripts\fetch_goalies.py --date %TODAY%
if errorlevel 1 (
    echo   WARNING: fetch_goalies failed. Continuing without goalie data.
    echo   advanced_metrics will use season SV%% only.
    set GOALIES_FLAG=
) else (
    set GOALIES_FLAG=--goalies-json data\goalies_%TODAY%.json
)
echo.

REM ── Advanced Metrics ────────────────────────────────────────────────────────
echo [4/5] Fetching advanced metrics...
py scripts\fetch_advanced_metrics.py --date %TODAY% %GOALIES_FLAG%
if errorlevel 1 (
    echo   ERROR: fetch_advanced_metrics failed.
    goto :error
)
echo.

REM ── Verify Players ──────────────────────────────────────────────────────────
echo [5/5] Verifying players (game logs + cold/hot tiers)...
py scripts\verify_players.py --date %TODAY%
if errorlevel 1 (
    echo   ERROR: verify_players failed.
    goto :error
)
echo.

REM ── Done ────────────────────────────────────────────────────────────────────
echo ============================================================
echo   PRE-GAME COMPLETE
echo ============================================================
echo.
echo   Files saved to data\:
echo     lineups_%TODAY%.json
echo     goalies_%TODAY%.json
echo     advanced_metrics_%TODAY%.json
echo     verified_%TODAY%.json
echo.
echo   NEXT STEP — Upload these 3 files to your Claude Project:
echo     data\verified_%TODAY%.json
echo     data\lineups_%TODAY%.json
echo     data\advanced_metrics_%TODAY%.json
echo   Then paste your picks prompt.
echo.
goto :end

:error
echo.
echo   Pipeline stopped due to error above.
echo.

:end
pause
endlocal
