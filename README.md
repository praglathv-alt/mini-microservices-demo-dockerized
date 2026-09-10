# Mini Microservices Demo (Python + Flask)

A simple, self-contained demo to explain the **microservices architecture** to
students. No database, no Docker, no internet needed after setup — runs fine
on an old Windows 7 laptop with 4GB RAM.

## Architecture

```
                     ┌─────────────────────┐
   Browser  ───────▶ │   API GATEWAY :5000   │
                     └─────────┬─────────────┘
                               │ forwards requests
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
     USER SERVICE       PRODUCT SERVICE     ORDER SERVICE
        :5002               :5001               :5003
                                                   │
                              (Order service calls User & Product
                               services over HTTP to validate an order)
```

Each service:
- Is a **separate Python/Flask process** with its own port
- Owns its **own data** (in-memory dict, no shared DB — keeps it simple)
- Talks to other services only through **HTTP REST APIs** (`requests` library)

This is the core idea to show students: independent, loosely-coupled
services communicating over the network, fronted by a single **API Gateway**.

## Setup (one-time)

1. Make sure Python is installed (Command Prompt: `python --version`)
2. Open Command Prompt in this folder and run:
   ```
   pip install -r requirements.txt
   ```

## Run the demo

**Easiest way:** double-click `run_all.bat`
- It opens 4 separate Command Prompt windows (one per service) and then
  opens your browser to `http://127.0.0.1:5000`

**Manual way (if you want to show each service starting one by one):**
Open 4 separate Command Prompt windows and run:
```
python user_service.py
python product_service.py
python order_service.py
python api_gateway.py
```
Then open `http://127.0.0.1:5000` in your browser.

## Demo script (suggested flow for students)

1. Show the 4 Command Prompt windows — point out each is an independent
   process on its own port. Kill one (Ctrl+C in the User Service window)
   to show the app doesn't crash entirely — only user-related features break.
2. Open the dashboard, click **Refresh Status** — show the "DOWN" service.
3. Restart it, click **Refresh Status** again — it's back "UP".
4. Click **Load Users** / **Load Products** — data is coming from two
   different services independently.
5. Place an order — explain that behind the scenes, `order_service.py`
   is calling `user_service.py` and `product_service.py` over HTTP to
   validate the user and reduce stock, then creates the order itself.
   You can open `order_service.py` and walk through the `requests.get(...)`
   calls live — this is the key teaching moment.
6. Load Orders — show the final result, and reload Products to show the
   stock count went down.

## Stopping the demo

Close the 4 Command Prompt windows, or press Ctrl+C in each.

## File structure

```
mini-microservices-demo/
├── api_gateway.py            # Entry point (port 5000)
├── user_service.py           # Port 5002
├── product_service.py        # Port 5001
├── order_service.py          # Port 5003
├── static/index.html         # Demo dashboard UI
├── requirements.txt
├── run_all.bat                # One-click launcher (no Docker)
├── Dockerfile.api_gateway     # One image per service
├── Dockerfile.user_service
├── Dockerfile.product_service
├── Dockerfile.order_service
├── docker-compose.yml         # Builds & wires up all 4 containers
├── .dockerignore
└── README.md
```

## Running with Docker (optional)

Each service is packaged as its **own container image** — this mirrors how
real microservices are deployed, where every service ships and scales
independently.

```
docker compose up --build
```

This builds all four images and starts them on a shared Docker network
called `microservices-net`. Inside that network, containers find each
other by **service name** instead of `127.0.0.1` — e.g. the order service
reaches the user service at `http://user-service:5002`. That's set via
environment variables in `docker-compose.yml`; the Python code falls back
to `127.0.0.1` if those variables aren't set, so the same files still work
with `run_all.bat` outside Docker.

Once it's up, open `http://localhost:5000` — same dashboard as before.

Stop everything with:
```
docker compose down
```

Rebuild after changing code:
```
docker compose up --build
```

**Note:** Docker Desktop requires Windows 10/11 (WSL2 or Hyper-V) — it
will not run on Windows 7. To actually build/run these containers, use a
cloud sandbox (e.g. [Play with Docker](https://labs.play-with-docker.com/)),
a Linux VM, or a cloud VM (AWS/GCP free tier). Upload this folder there,
then run the commands above.
