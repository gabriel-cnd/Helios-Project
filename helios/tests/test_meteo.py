from datetime import datetime, timezone


from helios.data import meteo


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_weather_nominal(monkeypatch):
    payload = {
        "timestamp": "2024-06-21T12:00:00Z",
        "measurements": {
            "temperature": {"value": 25},
            "humidity": {"value": 50},
            "globalRadiation": {"value": 800},
        },
    }

    class DummySession:
        def get(self, url, params=None, timeout=10):
            return DummyResponse(payload)

    client = meteo.MeteoSwissClient(session=DummySession())
    data = client.fetch_weather(
        latitude=46.5, longitude=6.6, when=datetime(2024, 6, 21, tzinfo=timezone.utc)
    )

    assert data["temperature"] == 25.0
    assert data["relative_humidity"] == 50.0
    assert data["global_radiation"] == 800.0
    assert data["source"] == "meteoswiss"


def test_fetch_weather_fallback(monkeypatch):
    # force _request à lever une exception pour déclencher le fallback
    client = meteo.MeteoSwissClient(allow_fallback=True)
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    monkeypatch.setattr(
        meteo, "get_sun_position", lambda *a, **k: {"elevation": 0.5, "azimuth": 1.0}
    )

    data = client.fetch_weather(
        latitude=46.5, longitude=6.6, when=datetime(2024, 6, 21, tzinfo=timezone.utc)
    )

    assert data["source"] == "synthetic-clear-sky"
    assert data["global_radiation"] is not None
