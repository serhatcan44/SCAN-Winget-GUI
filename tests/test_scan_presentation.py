import unittest

from scan_presentation import apply_theme_menu_language, get_install_status_text, get_ui_texts


class FakeThemeMenu:
    def __init__(self):
        self.configured_values = None
        self.selected = None

    def configure(self, values):
        self.configured_values = values

    def set(self, value):
        self.selected = value


class ScanPresentationTests(unittest.TestCase):
    def test_get_ui_texts_uses_language_values(self):
        texts = get_ui_texts({"install": "Install", "installed_apps": "Installed Apps"})
        self.assertEqual(texts["install_button"], "Install")
        self.assertEqual(texts["installed_label"], "Installed Apps")

    def test_apply_theme_menu_language_selects_dark_value(self):
        menu = FakeThemeMenu()
        apply_theme_menu_language(menu, "English", "Dark")
        self.assertEqual(menu.configured_values, ["Dark", "Light"])
        self.assertEqual(menu.selected, "Dark")

    def test_get_install_status_text(self):
        self.assertEqual(get_install_status_text(True), "Kurulu")
        self.assertEqual(get_install_status_text(False), "Kurulu değil")


if __name__ == "__main__":
    unittest.main()
