from __future__ import annotations

import unittest

from backend.tools.repair_template_text_encoding import restored_text


class TemplateTextEncodingTests(unittest.TestCase):
    def test_repairs_latin1_decoded_utf8_chinese(self) -> None:
        mojibake = "休眠期（清园越冬）".encode("utf-8").decode("latin1")
        self.assertEqual(restored_text(mojibake), "休眠期（清园越冬）")

    def test_keeps_normal_chinese_unchanged(self) -> None:
        self.assertIsNone(restored_text("休眠期（清园越冬）"))

    def test_keeps_non_utf8_latin1_text_unchanged(self) -> None:
        self.assertIsNone(restored_text("caf\u00e9"))


if __name__ == "__main__":
    unittest.main()
