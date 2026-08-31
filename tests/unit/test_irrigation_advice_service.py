from __future__ import annotations

import unittest

from backend.app.services.irrigation_advice_service import build_irrigation_advice


class IrrigationAdviceServiceTest(unittest.TestCase):
    def advice(self, **changes):
        values = {"current_moisture": 28.0, "threshold": 35.0, "suggested_duration": 20, "stage_code": "FRUIT_EXPANSION", "device_online": True, "weather": {"available": True, "rainProbability24h": 10}}
        values.update(changes)
        return build_irrigation_advice(**values)

    def test_low_moisture_and_low_rain_recommends_irrigation(self):
        self.assertEqual(self.advice()["decision"], "IRRIGATE")

    def test_offline_device_requires_check(self):
        self.assertEqual(self.advice(device_online=False)["decision"], "CHECK_DEVICE")

    def test_high_rain_probability_blocks_irrigation(self):
        self.assertEqual(self.advice(weather={"available": True, "rainProbability24h": 80})["decision"], "NO_IRRIGATION")

    def test_missing_moisture_is_insufficient(self):
        self.assertEqual(self.advice(current_moisture=None)["decision"], "DATA_INSUFFICIENT")

    def test_weather_failure_keeps_farm_rule_available(self):
        result = self.advice(weather={"available": False})
        self.assertEqual(result["decision"], "IRRIGATE")
        self.assertTrue(any("天气" in reason for reason in result["reasons"]))


if __name__ == "__main__":
    unittest.main()
