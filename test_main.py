import pytest
from main import process_weather_data
import json

# Static test data that simulates a response from YR's API
# This data represents a warm and sunny day
# You can change the values here to test other scenarios
hot_and_sunny_data = {
    "properties": {
        "timeseries": [
            {  # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 25.0, "ultraviolet_index_clear_sky": 4.5}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            },
            {  # 09:00
                "time": "2025-08-29T09:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 26.0, "ultraviolet_index_clear_sky": 5.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            }
        ]
    }
}

# Static test data for a rainy and cool day
rainy_and_cool_data = {
    "properties": {
        "timeseries": [
            {  # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 12.0, "ultraviolet_index_clear_sky": 1.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 2.5, "precipitation_amount_min": 1.0, "precipitation_amount_max": 3.0}}
                }
            },
            {  # 09:00
                "time": "2025-08-29T09:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": 10.0, "ultraviolet_index_clear_sky": 1.5}},
                    "next_1_hours": {"details": {"precipitation_amount": 1.2, "precipitation_amount_min": 0.5, "precipitation_amount_max": 2.0}}
                }
            }
        ]
    }
}

# Static test data for a cold day below zero
cold_day_data = {
    "properties": {
        "timeseries": [
            {  # 08:00
                "time": "2025-08-29T08:00:00Z",
                "data": {
                    "instant": {"details": {"air_temperature": -2.0, "ultraviolet_index_clear_sky": 1.0}},
                    "next_1_hours": {"details": {"precipitation_amount": 0.0, "precipitation_amount_min": 0.0, "precipitation_amount_max": 0.0}}
                }
            },
            {  # 09:00
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
    """Tests the logic for a warm and sunny day."""
    recommendation = process_weather_data(hot_and_sunny_data)
    assert "Det blir varmt!" in recommendation
    assert "smörj in dig med solkräm" in recommendation
    assert "regnkläder och stövlar" not in recommendation
    assert "UV-indexet blir högt (5.0)" in recommendation


def test_rainy_and_cool_day():
    """Tests the logic for a rainy and cool day."""
    recommendation = process_weather_data(rainy_and_cool_data)
    assert "Ta med dunjacka" in recommendation
    assert "regnkläder och stövlar" in recommendation
    assert "smörj in dig med solkräm" not in recommendation
    assert "Total mängd: 3.7 mm" in recommendation


def test_cold_day():
    """Tests the logic for a cold day below zero."""
    recommendation = process_weather_data(cold_day_data)
    assert "overall, mössa och dubbla vantar" in recommendation
    assert "Det blir kallt." in recommendation
    assert "shorts och t-shirt" not in recommendation
    assert "regnkläder och stövlar" not in recommendation