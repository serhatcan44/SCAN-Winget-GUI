import unittest
from unittest import mock

import scan_storage


class ScanStorageTests(unittest.TestCase):
    def test_load_history_normalizes_invalid_items(self):
        fake_history = [
            {"time": " 10:00 ", "action": " Install ", "target": " Chrome ", "status": "", "detail": " Done "},
            "invalid",
        ]
        with mock.patch.object(scan_storage, "load_json_file", return_value=fake_history):
            history = scan_storage.load_history(12)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["time"], "10:00")
        self.assertEqual(history[0]["status"], "info")

    def test_load_settings_applies_defaults(self):
        with mock.patch("scan_storage.os.path.exists", return_value=True), \
            mock.patch.object(scan_storage, "ensure_app_storage"), \
            mock.patch.object(scan_storage, "load_json_file", return_value={}):
            settings = scan_storage.load_settings()
        self.assertEqual(settings["language"], "Türkçe")
        self.assertEqual(settings["Theme"], "Dark")


if __name__ == "__main__":
    unittest.main()
