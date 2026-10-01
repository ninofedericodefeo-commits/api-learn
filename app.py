"""A local learning API with fictional gas station prices."""

from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from price_reports import add_report, latest_reports


class FuelType(StrEnum):
    regular = "regular"
    midgrade = "midgrade"
    premium = "premium"
    diesel = "diesel"


class Station(BaseModel):
    id: str
    name: str
    city: str
    state: str
    prices: dict[FuelType, float]
    latitude: float
    longitude: float
    address: str
    sample_data: bool = True


class StationList(BaseModel):
    stations: list[Station]
    count: int
    price_unit: str = "USD per gallon"
    sample_data: bool = True


class PriceSummary(BaseModel):
    city: str | None
    fuel_type: FuelType
    station_count: int
    lowest_price: float
    highest_price: float
    average_price: float
    cheapest_station_id: str
    price_unit: str = "USD per gallon"
    sample_data: bool = True


class CostEstimate(BaseModel):
    station_id: str
    fuel_type: FuelType
    gallons: float
    price_per_gallon: float
    estimated_cost: float
    currency: str = "USD"
    sample_data: bool = True


STATIONS = [
    Station(
        id="station-1", name="Example Fuel North", city="Philadelphia", state="PA",
        latitude=39.9526, longitude=-75.1652, address="123 Market St",
        prices={FuelType.regular: 3.39, FuelType.midgrade: 3.69,
                FuelType.premium: 3.99, FuelType.diesel: 3.89},
    ),
    Station(
        id="station-2", name="Example Fuel Central", city="Philadelphia", state="PA",
        latitude=39.9535, longitude=-75.1622, address="45 Chestnut Ave",
        prices={FuelType.regular: 3.45, FuelType.midgrade: 3.75,
                FuelType.premium: 4.05, FuelType.diesel: 3.95},
    ),
    Station(
        id="station-3", name="Example Fuel East", city="Philadelphia", state="PA",
        latitude=39.9492, longitude=-75.1701, address="88 Walnut St",
        prices={FuelType.regular: 3.35, FuelType.midgrade: 3.65,
                FuelType.premium: 3.95, FuelType.diesel: 3.85},
    ),
    Station(
        id="station-4", name="Example Fuel West", city="Philadelphia", state="PA",
        latitude=39.9457, longitude=-75.1576, address="202 Broad St",
        prices={FuelType.regular: 3.49, FuelType.midgrade: 3.79,
                FuelType.premium: 4.09, FuelType.diesel: 3.99},
    ),
]

app = FastAPI(
    title="Gas Prices Learning API",
    description="Local demo using fictional sample prices in USD per gallon. No live pricing is provided.",
    version="0.1.0",
)


def find_station(station_id: str) -> Station:
    for station in STATIONS:
        if station.id == station_id:
            return station
    raise HTTPException(status_code=404, detail="Station not found")


def matching_stations(city: str | None) -> list[Station]:
    if city is None:
        return STATIONS
    return [station for station in STATIONS if station.city.casefold() == city.strip().casefold()]


@app.get("/")
def home() -> dict[str, str | bool]:
    return {"message": "Try /docs to explore the API", "sample_data": True}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/fuel-types")
def fuel_types() -> dict[str, list[str] | str | bool]:
    return {"fuel_types": [fuel.value for fuel in FuelType],
            "price_unit": "USD per gallon", "sample_data": True}


@app.get("/stations", response_model=StationList)
def list_stations(
    city: str | None = Query(default=None, min_length=1),
    fuel_type: FuelType = FuelType.regular,
    max_price: float | None = Query(default=None, gt=0),
) -> StationList:
    stations = matching_stations(city)
    if max_price is not None:
        stations = [station for station in stations if station.prices[fuel_type] <= max_price]
    return StationList(stations=stations, count=len(stations))


@app.get("/stations/{station_id}", response_model=Station)
def get_station(station_id: str) -> Station:
    return find_station(station_id)


@app.get("/prices/summary", response_model=PriceSummary)
def price_summary(
    city: str | None = Query(default=None, min_length=1),
    fuel_type: FuelType = FuelType.regular,
) -> PriceSummary:
    stations = matching_stations(city)
    if not stations:
        raise HTTPException(status_code=404, detail="No stations found for that city")
    prices = [station.prices[fuel_type] for station in stations]
    cheapest = min(stations, key=lambda station: station.prices[fuel_type])
    return PriceSummary(
        city=city, fuel_type=fuel_type, station_count=len(stations),
        lowest_price=min(prices), highest_price=max(prices),
        average_price=round(sum(prices) / len(prices), 2),
        cheapest_station_id=cheapest.id,
    )


@app.get("/estimate", response_model=CostEstimate)
def estimate_cost(
    station_id: str,
    gallons: float = Query(gt=0, le=100),
    fuel_type: FuelType = FuelType.regular,
) -> CostEstimate:
    station = find_station(station_id)
    price = station.prices[fuel_type]
    return CostEstimate(
        station_id=station_id, fuel_type=fuel_type, gallons=gallons,
        price_per_gallon=price,
        estimated_cost=float(
            (Decimal(str(price)) * Decimal(str(gallons))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        ),
    )


class PriceReportInput(BaseModel):
    fuel_type: FuelType
    price: float = Field(gt=0, le=30, allow_inf_nan=False)


@app.get("/v1/stations/sample")
def sample_stations() -> dict:
    """App-facing station list. Community prices replace the seed price for that fuel."""
    reports = latest_reports()
    stations = []
    for station in STATIONS:
        prices = []
        for fuel_type, seed_price in station.prices.items():
            report = reports.get((station.id, fuel_type.value))
            prices.append({"fuelType": fuel_type.value,
                           "price": report["price"] if report else seed_price,
                           "currency": "USD",
                           "reportedAt": report["reported_at"] if report else "2026-01-01T00:00:00Z",
                           "source": "community" if report else "sample"})
        stations.append({"id": station.id, "name": station.name,
                         "latitude": station.latitude, "longitude": station.longitude,
                         "address": station.address, "city": station.city,
                         "state": station.state, "prices": prices})
    return {"provider": "api-learn", "sample_data": True, "stations": stations}


@app.post("/v1/stations/{station_id}/prices", status_code=201)
def report_station_price(station_id: str, report: PriceReportInput) -> dict:
    """Save an unverified user report. No account or receipt photo is collected."""
    find_station(station_id)
    return add_report(station_id, report.fuel_type.value, report.price)
