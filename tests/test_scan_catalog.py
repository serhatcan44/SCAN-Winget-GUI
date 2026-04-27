import unittest

from scan_catalog import APP_ALIASES, APPS


class ScanCatalogTests(unittest.TestCase):
    def test_catalog_contains_expected_core_apps(self):
        self.assertIn("Google Chrome", APPS)
        self.assertEqual(APPS["Google Chrome"]["id"], "Google.Chrome")

    def test_aliases_include_vscode_short_name(self):
        self.assertIn("vscode", APP_ALIASES["Visual Studio Code"])

    def test_catalog_contains_idm(self):
        self.assertIn("Internet Download Manager", APPS)
        self.assertEqual(APPS["Internet Download Manager"]["id"], "Tonec.InternetDownloadManager")

    def test_idm_aliases_include_short_names(self):
        self.assertIn("idm", APP_ALIASES["Internet Download Manager"])
        self.assertIn("idman", APP_ALIASES["Internet Download Manager"])


if __name__ == "__main__":
    unittest.main()
