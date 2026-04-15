import unittest

from scan_operation_logic import (
    CANCEL_TOKENS,
    build_manage_command,
    build_upgrade_command,
    get_manage_action_meta,
    summarize_bulk_update,
)


class ScanOperationLogicTests(unittest.TestCase):
    def test_get_manage_action_meta_returns_expected_labels(self):
        self.assertEqual(get_manage_action_meta("install"), ("yükleniyor", "Yükleme"))
        self.assertEqual(get_manage_action_meta("uninstall"), ("kaldırılıyor", "Kaldırma"))

    def test_build_manage_command_adds_agreements_for_install(self):
        cmd = build_manage_command("winget.exe", "install", "Google.Chrome")
        self.assertIn("--accept-package-agreements", cmd)

    def test_build_upgrade_command_is_exact_and_safe(self):
        cmd = build_upgrade_command("winget.exe", "Google.Chrome")
        self.assertEqual(cmd[:4], ["winget.exe", "upgrade", "--id", "Google.Chrome"])

    def test_summarize_bulk_update_formats_counts(self):
        self.assertEqual(summarize_bulk_update(2, 1, 0), "2 başarılı, 1 atlandı, 0 başarısız.")

    def test_cancel_tokens_include_common_values(self):
        self.assertIn("1602", CANCEL_TOKENS)


if __name__ == "__main__":
    unittest.main()
