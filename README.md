# Gas prices API

A small local API for exploring gas station prices and estimating fill-up costs. **All stations and prices are fictional sample data, not live gas prices.** No API key or external service is needed.

## Run it

Python 3.12 or newer and [uv](https://docs.astral.sh/uv/) are required.

```bash
export UV_CACHE_DIR=/tmp/api-learn-uv-cache
uv sync --extra test --frozen --link-mode=copy
uv run --frozen uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for an interactive page where you can try each endpoint. The server listens only on your computer.

## Try a few requests

In another terminal:

```bash
curl http://127.0.0.1:8000/stations
curl 'http://127.0.0.1:8000/stations?city=Albany&fuel_type=regular&max_price=3.50'
curl 'http://127.0.0.1:8000/prices/summary?city=Albany&fuel_type=regular'
curl 'http://127.0.0.1:8000/estimate?station_id=station-1&fuel_type=regular&gallons=12'
```

Prices are in US dollars per gallon. `/fuel-types` lists supported fuels. `/health` provides a simple readiness check. Invalid fuel types, station IDs, and amounts return useful HTTP errors.

## Run tests

```bash
UV_CACHE_DIR=/tmp/api-learn-uv-cache uv run --frozen python -m unittest discover -s tests -v
```

To use real prices later, you would need a data provider and its terms, coverage, update frequency, and possibly an API key. The sample data in `app.py` can be replaced once you choose one.

## Use it with GasFinder

The Expo app reads `GET /v1/stations/sample` and submits a manually entered pump price with
`POST /v1/stations/{station_id}/prices` (`{"fuel_type":"regular","price":3.27}`).
The four fictional Philadelphia stations live in this repository. The latest community report
for each station and fuel replaces its sample price in the app response and is marked
`source: "community"`; all other prices remain clearly labeled as fictional samples.
Reports are saved in `price_reports.sqlite3` (or `GAS_API_DB_PATH`) and survive restarts.
The app does not upload receipt photos or personal savings data.

`GET /v1/stations/{station_id}/prices/history?fuel_type=regular&days=30` returns
saved reports in time order for the graph. `days` accepts 1–365; omit it for all
time. Fictional starting prices are excluded. The graph therefore stays empty
until someone reports a price for that station and fuel.

For a phone on the same trusted Wi-Fi, run Uvicorn with `--host 0.0.0.0` and
set the app URL to your computer's private LAN IP. This exposes the unauthenticated
report route to devices on that network, so use it only while testing locally.

Set `EXPO_PUBLIC_SAMPLE_API_URL=http://localhost:8000` in the app's `.env.local` for an iOS
simulator. A physical phone needs a reachable HTTPS deployment. This learning API has no
accounts, authentication, moderation, or rate limit: **do not expose its write endpoint
publicly until those protections are added**. GitHub hosting of this source does not run
an API server or synchronize a database by itself.
