@echo off
if "%~1"=="" (
    echo [ERROR] No data source provided.
    echo Usage: scripts\run_all.bat "C:\path\to\video.mp4"
    pause
    exit /b 1
)

set "SOURCE=%~1"
echo Starting JATAYU-SENTINEL Pipeline with source: "%SOURCE%"

echo Starting R Shiny Dashboard...
start "Jatayu Dashboard" cmd /k "conda activate python_analysis && Rscript -e ""shiny::runApp('r/app.R', port = 8080, host = '127.0.0.1')"""

echo Starting Video Stream Server...
start "Jatayu Video" cmd /k "conda activate python_analysis && python scripts/video_server.py"

echo Starting Spark Streaming...
start "Jatayu Spark" cmd /k "conda activate python_analysis && python spark/stream_aggregate.py"

echo Starting Detector...
start "Jatayu Detector" cmd /k "conda activate python_analysis && python detector/detect_track.py"

echo Waiting 10 seconds for services to initialize...
timeout /t 10 /nobreak

echo Starting Producer...
start "Jatayu Producer" cmd /k "conda activate python_analysis && python producer/replay_producer.py --source ^"%SOURCE%^" --fps 30"

echo All services started! Dashboard available at http://127.0.0.1:8080