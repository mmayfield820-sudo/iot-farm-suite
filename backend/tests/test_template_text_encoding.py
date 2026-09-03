from __future__ import annotations

import unittest

from backend.app.text_encoding import display_text, restored_text


class TemplateTextEncodingTests(unittest.TestCase):
    def test_repairs_latin1_decoded_utf8_chinese(self) -> None:
        mojibake = "休眠期（清园越冬）".encode("utf-8").decode("latin1")
        self.assertEqual(restored_text(mojibake), "休眠期（清园越冬）")

    def test_keeps_normal_chinese_unchanged(self) -> None:
        self.assertIsNone(restored_text("休眠期（清园越冬）"))

    def test_keeps_non_utf8_latin1_text_unchanged(self) -> None:
        self.assertIsNone(restored_text("caf\u00e9"))

    def test_display_text_repairs_legacy_plot_name(self) -> None:
        mojibake = "二号田地".encode("utf-8").decode("latin1")
        self.assertEqual(display_text(mojibake), "二号田地")

    def test_display_text_repairs_windows_1252_mojibake(self) -> None:
        def mysql_latin1_character(byte: int) -> str:
            try:
                return bytes([byte]).decode("cp1252")
            except UnicodeDecodeError:
                return chr(byte)

        mojibake = "".join(mysql_latin1_character(byte) for byte in "二号田地".encode("utf-8"))
        self.assertEqual(display_text(mojibake), "二号田地")

    def test_display_text_preserves_normal_value(self) -> None:
        self.assertEqual(display_text("东坡一号果园"), "东坡一号果园")


if __name__ == "__main__":
    unittest.main()
