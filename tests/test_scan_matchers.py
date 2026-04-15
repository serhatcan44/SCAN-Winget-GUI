import unittest

from scan_matchers import contains_any_alias, normalize_match_text, output_contains_any


class ScanMatcherTests(unittest.TestCase):
    def test_normalize_match_text_collapses_symbols(self):
        self.assertEqual(normalize_match_text("Visual-Studio_Code++"), "visual studio code")

    def test_contains_any_alias_matches_compound_alias(self):
        aliases = ["visual studio code", "vscode", "microsoft.visualstudiocode"]
        self.assertTrue(contains_any_alias("Package: Microsoft.VisualStudioCode", aliases))

    def test_contains_any_alias_matches_spaced_alias_without_exact_spacing(self):
        aliases = ["google chrome"]
        self.assertTrue(contains_any_alias("GoogleChrome", aliases))

    def test_contains_any_alias_rejects_unrelated_text(self):
        aliases = ["discord", "slack"]
        self.assertFalse(contains_any_alias("Adobe Photoshop", aliases))

    def test_output_contains_any_detects_known_messages(self):
        self.assertTrue(output_contains_any("No available upgrade found", ["no available upgrade found"]))


if __name__ == "__main__":
    unittest.main()
