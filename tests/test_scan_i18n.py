import unittest

from scan_i18n import get_theme_values


class ScanI18nTests(unittest.TestCase):
    def test_get_theme_values_returns_correct_turkish_labels(self):
        self.assertEqual(get_theme_values("Türkçe"), ["Koyu", "Açık"])

    def test_get_theme_values_returns_correct_russian_labels(self):
        self.assertEqual(get_theme_values("Русский"), ["Тёмная", "Светлая"])


if __name__ == "__main__":
    unittest.main()
