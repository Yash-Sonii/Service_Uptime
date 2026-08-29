Service Uptime Monitor

A small Flask web app that checks the availability of a list of services on a background thread and displays their live status (up/down, response time) on an auto-refreshing dashboard.

How it works
A background thread pings each configured service URL every 30 seconds.
Results (up/down, status code, response time) are stored in memory.
The /status endpoint exposes this data as JSON.
The dashboard (/) polls /status every 5 seconds and updates a green/red indicator for each service.
/health is a simple endpoint used by the CI pipeline to confirm the app started correctly.
Run locally
bash
pip install -r requirements.txt
python app.py
# visit http://localhost:5000
Run with Docker
bash
docker build -t uptime-monitor .
docker run -p 5000:5000 uptime-monitor
CI/CD

On every push to main, GitHub Actions (.github/workflows/ci.yml) builds the Docker image, runs the container, and verifies the /health endpoint responds before the build is marked successful — the same build-run-verify pattern used in the Log Monitoring Dashboard project.

Tech stack

Python, Flask, Docker, GitHub Actions, requests