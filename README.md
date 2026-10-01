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
