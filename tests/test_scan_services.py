import types
import unittest
from unittest import mock

import scan_services


class ScanServicesTests(unittest.TestCase):
    def test_get_app_aliases_includes_known_variants(self):
        aliases = scan_services.get_app_aliases(
            "Visual Studio Code",
            "Microsoft.VisualStudioCode",
            {"Visual Studio Code": ["vscode"]},
        )
        self.assertIn("vscode", aliases)
        self.assertIn("microsoft.visualstudiocode", aliases)

    def test_get_winget_package_details_parses_version_and_publisher(self):
        fake_process = types.SimpleNamespace(
            PIPE=object(),
            CREATE_NO_WINDOW=0,
            run=lambda *args, **kwargs: types.SimpleNamespace(stdout="Publisher: Google LLC\nVersion: 1.2.3\n", stderr=""),
        )
        fake_shutil = types.SimpleNamespace(which=lambda name: "winget.exe")
        details = scan_services.get_winget_package_details("Google.Chrome", subprocess_module=fake_process, shutil_module=fake_shutil)
        self.assertEqual(details["publisher"], "Google LLC")
        self.assertEqual(details["version"], "1.2.3")

    def test_has_available_upgrade_detects_up_to_date(self):
        fake_process = types.SimpleNamespace(
            PIPE=object(),
            CREATE_NO_WINDOW=0,
            run=lambda *args, **kwargs: types.SimpleNamespace(stdout="No available upgrade found", stderr=""),
        )
        fake_shutil = types.SimpleNamespace(which=lambda name: "winget.exe")
        available, status = scan_services.has_available_upgrade(
            "Google Chrome",
            "Google.Chrome",
            {"Google Chrome": ["google chrome"]},
            subprocess_module=fake_process,
            shutil_module=fake_shutil,
        )
        self.assertFalse(available)
        self.assertEqual(status, "up_to_date")

    def test_get_installed_apps_snapshot_uses_cache_when_fresh(self):
        scan_cache = {"timestamp": 100.0, "installed": {"Google Chrome"}}
        registry_cache = {"timestamp": 0.0, "names": []}
        fake_time = types.SimpleNamespace(time=lambda: 101.0)
        installed, from_cache = scan_services.get_installed_apps_snapshot(
            {"Google Chrome": {"id": "Google.Chrome"}},
            {},
            scan_cache,
            12,
            registry_cache,
            180,
            force_refresh=False,
            time_module=fake_time,
        )
        self.assertTrue(from_cache)
        self.assertEqual(installed, {"Google Chrome"})

    def test_is_app_installed_uses_registry_fallback(self):
        with mock.patch.object(scan_services, "get_registry_display_names", return_value=["Google Chrome"]):
            installed = scan_services.is_app_installed(
                "Google Chrome",
                "Google.Chrome",
                {"Google Chrome": ["google chrome"]},
                {"timestamp": 0.0, "names": []},
                180,
                subprocess_module=types.SimpleNamespace(PIPE=object(), CREATE_NO_WINDOW=0, run=lambda *a, **k: types.SimpleNamespace(stdout="", stderr="")),
                shutil_module=types.SimpleNamespace(which=lambda name: None),
                winreg_module=None,
                time_module=types.SimpleNamespace(time=lambda: 0.0),
            )
        self.assertTrue(installed)


if __name__ == "__main__":
    unittest.main()
