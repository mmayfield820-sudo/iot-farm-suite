"""MQTT 配置和客户端基线测试。"""

import unittest

from src.config.settings import get_mqtt_settings


class MqttSettingsTest(unittest.TestCase):
    """验证应用能从 .env 读取 MQTT 配置。"""

    def test_get_mqtt_settings_reads_env(self) -> None:
        settings = get_mqtt_settings()

        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 1883)
        self.assertEqual(settings.username, "")
        self.assertEqual(settings.password, "")


if __name__ == "__main__":
    unittest.main()
