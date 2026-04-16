# Gitea Workflow Dashboard

A lightweight dashboard for monitoring **Gitea Actions workflow runs** across multiple repositories.

It includes:

- `gitea-dashboard.html`: a single-page UI for viewing latest workflow status per repository, with expandable older runs.
- `launcher.py`: a small local HTTP server + API proxy that serves the dashboard and forwards API calls to Gitea.

## Why this project exists

When opening the HTML file directly (or serving it from a different origin), browser CORS rules can block calls to the Gitea API.
This project solves that by using a local Python proxy (`launcher.py`) so the browser talks to `http://127.0.0.1:8765`, and the proxy forwards requests to Gitea.

## Tested environment

This project is tested against a **local Gitea deployment** listening at:

- `http://localhost:3000/`

The default UI and proxy settings are aligned to that local setup.

## Quick start

### 1) Create an API token

Create a Gitea token with permissions to read repositories and actions/workflow runs.

### 2) Save token to `token.txt`

Put only the token string in `token.txt` (no quotes):

```text
<your-token>
```

`launcher.py` reads this token automatically and injects it into proxied requests, so the browser never sees it.

### 3) Run the launcher

```bash
python3 launcher.py
```

You should see output similar to:

- `Serving at http://127.0.0.1:8765`
- `Proxy: http://127.0.0.1:8765/gitea/* -> http://localhost:3000/*`

### 4) Open the dashboard

Open:

- `http://127.0.0.1:8765/gitea-dashboard.html`

The dashboard talks to the proxy by default; the API base is:

- `http://127.0.0.1:8765/gitea`

## How the Python launcher avoids CORS issues

`launcher.py` solves the browser CORS problem with two mechanisms:

1. **Same-origin serving for the UI**
   - The dashboard is served from the same local origin as the proxy (`127.0.0.1:8765`).

2. **Backend proxy for Gitea API calls**
   - Requests to `/gitea/...` are forwarded server-side to `http://localhost:3000/...`.
   - The browser no longer talks directly to `localhost:3000`, so cross-origin blocks are avoided.

Additionally, the launcher:

- Handles CORS/OPTIONS headers for browser compatibility.
- Forwards common HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).
- Injects `Authorization: token <token>` from `token.txt` so the token never leaves the local machine via the browser.

## Dashboard usage notes

- Leave repositories empty to auto-discover from `/api/v1/user/repos`.
- Use filtering for failed/running workflows.
- Expand a row to inspect older runs of the same workflow.
- Use **Run now** to manually dispatch the latest workflow shown for a repo (you will be prompted for ref and optional JSON inputs).
- Auto-refresh interval is configurable.

## Token scope recommendations

For the dashboard features in this repo:

- `read:user` is recommended for auto-discovery (`/api/v1/user/repos`).
- `write:repository` is required for manual workflow dispatch under `/repos/*` routes.

Use least privilege and avoid broad admin scopes unless you explicitly need them.

## Files

- `gitea-dashboard.html` — dashboard UI and client-side data fetching.
- `launcher.py` — static file server + API proxy.
- `token.txt` — local token file (not for production secret management).

## Security note

This project is intended for local/internal use.

- Treat `token.txt` as sensitive.
- Prefer least-privilege tokens.
- Do not expose this proxy publicly without authentication and tighter hardening.
