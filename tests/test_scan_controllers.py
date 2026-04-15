import unittest

from scan_controllers import (
    bulk_final_status,
    bulk_item_result,
    bulk_precheck,
    manage_precheck,
    manage_result,
    update_precheck,
    update_result,
)


class ScanControllersTests(unittest.TestCase):
    def test_manage_precheck_detects_already_installed(self):
        feedback = manage_precheck("install", True, True, "Google Chrome", "Yükleme")
        self.assertEqual(feedback["history_status"], "warning")

    def test_manage_result_returns_success_for_install(self):
        feedback = manage_result("install", True, False, 0, "", "Google Chrome")
        self.assertEqual(feedback["history_status"], "success")

    def test_update_precheck_detects_non_winget_install(self):
        feedback = update_precheck(True, False, "Google Chrome")
        self.assertIn("winget paketi", feedback["detail"])

    def test_update_result_detects_up_to_date(self):
        feedback = update_result(0, True, "1.0", "1.0", "no available upgrade found", "Google Chrome")
        self.assertEqual(feedback["history_status"], "info")

    def test_bulk_precheck_handles_up_to_date(self):
        feedback = bulk_precheck("up_to_date")
        self.assertEqual(feedback["history_status"], "info")

    def test_bulk_item_result_reports_success(self):
        status, detail = bulk_item_result(0, "1.0", "2.0", True, "")
        self.assertEqual(status, "success")
        self.assertIn("2.0", detail)

    def test_bulk_final_status_warns_on_failures(self):
        self.assertEqual(bulk_final_status(1), "warning")


if __name__ == "__main__":
    unittest.main()
