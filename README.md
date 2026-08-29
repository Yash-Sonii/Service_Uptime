# Service Uptime Monitor

A lightweight Flask web app that monitors a list of external services in the background and displays their live status — up/down, HTTP status code, and response time — on an auto-refreshing dashboard.

Built to demonstrate a full observability pipeline: background health checking → JSON API → live UI → containerization → CI verification.


## Features
- **Background monitoring** — a daemon thread checks every configured service every 30 seconds, independent of any web request.
- **Response time tracking** — not just up/down; each check records latency in milliseconds, so slow-but-technically-up services are visible too.
- **Live dashboard** — the frontend polls `/status` every 5 seconds and updates green/red indicators with zero manual refresh.
- **JSON API** — `/status` exposes the latest results for any client to consume, not just the built-in dashboard.
- **Containerized** — ships with a `Dockerfile` for consistent, portable runs anywhere Docker is available.
- **CI-verified** — GitHub Actions builds the image, runs the container, and confirms it actually boots by hitting `/health` on every push to `main`.

## How It Works
```
┌─────────────────────┐
│  background_checker  │  runs forever, every 30s
│  (daemon thread)      │──────┐
└─────────────────────┘      │
                              ▼
                    ┌───────────────────┐
                    │   status_store      │  in-memory dict
                    │  (thread-safe)       │
                    └───────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                          ▼
        GET /status (JSON)          GET / (dashboard)
                                     polls /status every 5s
```

1. `background_checker()` loops forever on a separate thread, calling `check_service()` for each URL in `SERVICES`.
2. `check_service()` sends an HTTP GET, times the response, and records status code + up/down.
3. Results are written to an in-memory `status_store`, protected by a lock for thread safety.
4. `/status` returns the current store as JSON.
5. `/` serves the dashboard, which polls `/status` every 5 seconds and redraws indicators — no page reload needed.
6. `/health` is a trivial endpoint used purely so CI can confirm the container started successfully.

## Tech Stack
| Layer | Tool |
|---|---|
| Backend | Python, Flask |
| Background job | Python `threading` |
| Frontend | HTML / CSS / vanilla JS (polling) |
| Containerization | Docker |
| CI/CD | GitHub Actions |

## Project Structure
```
Service_Uptime/
├── app.py                    # Flask app + background checker
├── templates/
│   └── index.html            # Dashboard UI
├── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml            # Build → run → verify /health
└── README.md
```

## Run Locally
```bash
pip install -r requirements.txt
python app.py
# visit http://localhost:8089
```

## Run with Docker
```bash
docker build -t uptime-monitor .
docker run -p 5000:8089 uptime-monitor
# visit http://localhost:5000
```
> Note: the app listens on port `8089` inside the container/locally. When running via Docker, `-p 5000:8089` maps host port `5000` to it — visit the **host** port (`5000`) in your browser.

## CI/CD Pipeline
On every push to `main`, `.github/workflows/ci.yml`:
1. Builds the Docker image.
2. Runs it as a container.
3. Curls `/health` to confirm the app started correctly.
4. Fails the build if the container doesn't respond as expected.

This mirrors the same build → run → verify pattern used in my [Log Monitoring Dashboard](#) project.

## Design Notes / Limitations
This project intentionally keeps scope tight rather than half-building a bigger feature set:
- **Fixed service list** — services are configured in `app.py`, not added dynamically through the UI.
- **In-memory storage** — no database, so history resets on restart.
- **No alerting** — status is visible on the dashboard, but nothing pushes a notification yet.
- **Detection, not diagnosis** — this tells you *that* something is down; the [Log Monitoring Dashboard](#) is the companion project for finding out *why*.

### Possible next steps
- Add a form to submit URLs dynamically (would need a small database).
- Add Slack/email alerting on status change.
- Add retry logic so a single failed check doesn't immediately flag as down.

## Adding a Service
Edit the `SERVICES` list in `app.py`:
```python
SERVICES = [
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"},
]
```