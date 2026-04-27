import types
import unittest
from unittest import mock

import scan_controllers
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

    def test_get_winget_package_details_parses_turkish_labels(self):
        fake_process = types.SimpleNamespace(
            PIPE=object(),
            CREATE_NO_WINDOW=0,
            run=lambda *args, **kwargs: types.SimpleNamespace(stdout="Yayıncı: Google LLC\nSürüm: 1.2.3\n", stderr=""),
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

    def test_has_available_upgrade_detects_turkish_up_to_date_message(self):
        fake_process = types.SimpleNamespace(
            PIPE=object(),
            CREATE_NO_WINDOW=0,
            run=lambda *args, **kwargs: types.SimpleNamespace(stdout="Bu paket için güncelleme bulunamadı", stderr=""),
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

    def test_run_helper_executable_raises_when_file_is_missing(self):
        fake_os = types.SimpleNamespace(
            path=types.SimpleNamespace(
                dirname=lambda _path: "C:\\app",
                join=lambda base, name: f"{base}\\{name}",
                exists=lambda _path: False,
            )
        )
        with self.assertRaises(FileNotFoundError):
            scan_services.run_helper_executable("idm.exe", os_module=fake_os)

    def test_run_helper_executable_falls_back_to_elevated_runner_for_winerror_740(self):
        class ElevationRequiredError(OSError):
            def __init__(self):
                super().__init__("elevation required")
                self.winerror = 740

        fake_process = types.SimpleNamespace(
            PIPE=object(),
            CREATE_NO_WINDOW=0,
            run=lambda *args, **kwargs: (_ for _ in ()).throw(ElevationRequiredError()),
        )
        fake_os = types.SimpleNamespace(
            path=types.SimpleNamespace(
                dirname=lambda _path: "C:\\app",
                join=lambda base, name: f"{base}\\{name}",
                exists=lambda _path: True,
            )
        )
        return_code, output = scan_services.run_helper_executable(
            "idm.exe",
            subprocess_module=fake_process,
            os_module=fake_os,
            shell_execute_runner=lambda path: (0, f"elevated:{path}"),
        )
        self.assertEqual(return_code, 0)
        self.assertIn("elevated:", output)

    def test_helper_result_returns_success_feedback(self):
        feedback = scan_controllers.helper_result(0, "")
        self.assertEqual(feedback["history_status"], "success")
        self.assertIn("başarıyla", feedback["detail"])

    def test_helper_result_returns_error_feedback(self):
        feedback = scan_controllers.helper_result(2, "error: access denied")
        self.assertEqual(feedback["history_status"], "error")
        self.assertIn("2", feedback["hint"])

    def test_helper_missing_feedback_returns_expected_message(self):
        feedback = scan_controllers.helper_missing_feedback()
        self.assertEqual(feedback["title"], "Yardımcı araç bulunamadı")
        self.assertIn("idm.exe", feedback["detail"])


if __name__ == "__main__":
    unittest.main()
