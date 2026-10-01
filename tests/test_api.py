import unittest

from fastapi.testclient import TestClient

from app import app


class GasApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_stations_are_clearly_sample_data(self):
        response = self.client.get("/stations")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["sample_data"])
        self.assertEqual(body["price_unit"], "USD per gallon")
        self.assertEqual(body["count"], 4)
        self.assertTrue(all(station["sample_data"] for station in body["stations"]))

    def test_filter_by_city_and_price(self):
        response = self.client.get(
            "/stations", params={"city": "PHILADELPHIA", "fuel_type": "regular", "max_price": 3.40}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([station["id"] for station in response.json()["stations"]], ["station-1", "station-3"])

    def test_summary_uses_only_matching_stations(self):
        response = self.client.get("/prices/summary", params={"city": "Philadelphia"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["station_count"], 4)
        self.assertEqual(body["average_price"], 3.42)
        self.assertEqual(body["cheapest_station_id"], "station-3")

    def test_estimate_uses_selected_station_and_fuel(self):
        response = self.client.get(
            "/estimate", params={"station_id": "station-1", "fuel_type": "diesel", "gallons": 12}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estimated_cost"], 46.68)

    def test_estimate_rounds_half_cents_up(self):
        response = self.client.get(
            "/estimate", params={"station_id": "station-1", "gallons": 0.5}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estimated_cost"], 1.70)

    def test_sample_endpoint_and_price_report(self):
        response = self.client.get("/v1/stations/sample")
        self.assertEqual(response.status_code, 200)
        station = response.json()["stations"][0]
        self.assertEqual(station["prices"][0]["source"], "sample")
        self.assertIn("latitude", station)
        posted = self.client.post("/v1/stations/station-1/prices",
                                  json={"fuel_type": "regular", "price": 3.27})
        self.assertEqual(posted.status_code, 201)
        updated = self.client.get("/v1/stations/sample").json()["stations"][0]
        self.assertEqual(updated["prices"][0]["price"], 3.27)
        self.assertEqual(updated["prices"][0]["source"], "community")
        self.assertEqual(self.client.post("/v1/stations/nope/prices",
                                          json={"fuel_type": "regular", "price": 3.2}).status_code, 404)
        self.assertEqual(self.client.post("/v1/stations/station-1/prices",
                                          json={"fuel_type": "regular", "price": -2}).status_code, 422)

    def test_bad_inputs_have_http_errors(self):
        self.assertEqual(self.client.get("/stations/no-such-station").status_code, 404)
        self.assertEqual(self.client.get("/prices/summary?city=Nowhere").status_code, 404)
        self.assertEqual(self.client.get("/stations?fuel_type=rocket").status_code, 422)
        self.assertEqual(self.client.get("/estimate?station_id=station-1&gallons=0").status_code, 422)


if __name__ == "__main__":
    unittest.main()
