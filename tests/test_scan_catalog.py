import unittest

from scan_catalog import APP_ALIASES, APPS


class ScanCatalogTests(unittest.TestCase):
    def test_catalog_contains_expected_core_apps(self):
        self.assertIn("Google Chrome", APPS)
        self.assertEqual(APPS["Google Chrome"]["id"], "Google.Chrome")

    def test_aliases_include_vscode_short_name(self):
        self.assertIn("vscode", APP_ALIASES["Visual Studio Code"])


if __name__ == "__main__":
    unittest.main()
