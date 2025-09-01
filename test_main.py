import pytest
from main import process_weather_data
import json

# Statisk testdata som simulerar svar från YR:s API
# Denna data representerar en varm och solig dag
# Du kan ändra värdena här för att testa andra scenarion
hot_and_sunny_data = {
    "properties": {
        "timeseries": [
            { # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 25.0, "ultraviolet_index_clear_sky": 4.5}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            },
            { # 09:00
                "time": "2025-08-29T09:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 26.0, "ultraviolet_index_clear_sky": 5.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            }
        ]
    }
}

# Statisk testdata för en regnig och sval dag
rainy_and_cool_data = {
    "properties": {
        "timeseries": [
            { # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 12.0, "ultraviolet_index_clear_sky": 1.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 2.5, "precipitation_amount_min": 1.0, "precipitation_amount_max": 3.0}}
                }
            },
            { # 09:00
                "time": "2025-08-29T09:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 10.0, "ultraviolet_index_clear_sky": 1.5}},
                    "next_1_hours": {"details": {"precipitation_amount": 1.2, "precipitation_amount_min": 0.5, "precipitation_amount_max": 2.0}}
                }
            }
        ]
    }
}

# Statisk testdata för en kall dag under nollan
cold_day_data = {
    "properties": {
        "timeseries": [
            { # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": -2.0, "ultraviolet_index_clear_sky": 1.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            },
            { # 09:00
                "time": "2025-08-29T09:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 1.0, "ultraviolet_index_clear_sky": 1.5}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            }
        ]
    }
}


def test_hot_and_sunny_day():
    """Testar logiken för en varm och solig dag."""
    recommendation = process_weather_data(hot_and_sunny_data)
    assert "Det blir varmt!" in recommendation
    assert "smörj in dig med solkräm" in recommendation
    assert "regnkläder och stövlar" not in recommendation
    assert "UV-indexet blir högt (5.0)" in recommendation


def test_rainy_and_cool_day():
    """Testar logiken för en regnig och sval dag."""
    recommendation = process_weather_data(rainy_and_cool_data)
    assert "Ta med dunjacka" in recommendation
    assert "regnkläder och stövlar" in recommendation
    assert "smörj in dig med solkräm" not in recommendation
    assert "Total mängd: 3.7 mm" in recommendation


def test_cold_day():
    """Testar logiken för en kall dag med minusgrader."""
    recommendation = process_weather_data(cold_day_data)
    assert "overall, mössa och dubbla vantar" in recommendation
    assert "Det blir kallt." in recommendation
    assert "shorts och t-shirt" not in recommendation
    assert "regnkläder och stövlar" not in recommendation