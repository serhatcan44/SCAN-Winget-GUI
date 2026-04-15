import unittest

from scan_ui_presenter import (
    DEFAULT_PROGRESS_HINT,
    apply_operation_feedback,
    hide_progress_modal,
    show_progress_modal,
    update_progress_modal,
)


class FakeWidget:
    def __init__(self):
        self.values = {}
        self.placed = False
        self.lifted = False

    def configure(self, **kwargs):
        self.values.update(kwargs)

    def set(self, value):
        self.values["progress"] = value

    def place(self, **kwargs):
        self.placed = True
        self.values.update(kwargs)

    def place_forget(self):
        self.placed = False

    def lift(self):
        self.lifted = True


class ScanUiPresenterTests(unittest.TestCase):
    def test_show_progress_modal_updates_widgets(self):
        title = FakeWidget()
        detail = FakeWidget()
        bar = FakeWidget()
        hint = FakeWidget()
        overlay = FakeWidget()
        card = FakeWidget()
        show_progress_modal(title, detail, bar, hint, overlay, card, "Baslik", "Detay", 0.5)
        self.assertEqual(title.values["text"], "Baslik")
        self.assertEqual(detail.values["text"], "Detay")
        self.assertEqual(bar.values["progress"], 0.5)
        self.assertEqual(hint.values["text"], DEFAULT_PROGRESS_HINT)
        self.assertTrue(overlay.placed)
        self.assertTrue(card.lifted)

    def test_update_progress_modal_updates_only_given_values(self):
        title = FakeWidget()
        detail = FakeWidget()
        bar = FakeWidget()
        update_progress_modal(title, detail, bar, detail_text="Yeni", progress=1)
        self.assertEqual(detail.values["text"], "Yeni")
        self.assertEqual(bar.values["progress"], 1)

    def test_hide_progress_modal_hides_overlay(self):
        overlay = FakeWidget()
        overlay.placed = True
        hide_progress_modal(overlay)
        self.assertFalse(overlay.placed)

    def test_apply_operation_feedback_schedules_updates(self):
        calls = []
        history = []

        def scheduler(delay, callback):
            calls.append(delay)
            callback()

        def update_progress(title, detail, progress):
            history.append(("progress", title, detail, progress))

        def set_hint(hint):
            history.append(("hint", hint))

        def add_history(action_name, target_name, status, detail):
            history.append(("history", action_name, target_name, status, detail))

        def hide():
            history.append(("hide",))

        def refresh_scan():
            history.append(("scan",))

        apply_operation_feedback(
            scheduler,
            update_progress,
            set_hint,
            add_history,
            hide,
            "Yukleme",
            "Chrome",
            {
                "title": "Tamam",
                "detail": "Bitti",
                "progress": 1,
                "hint": "Dogrulandi",
                "history_status": "success",
                "history_detail": "Ok",
            },
            refresh_scan_callback=refresh_scan,
            hide_delay_ms=1500,
        )
        self.assertIn(("progress", "Tamam", "Bitti", 1), history)
        self.assertIn(("hint", "Dogrulandi"), history)
        self.assertIn(("history", "Yukleme", "Chrome", "success", "Ok"), history)
        self.assertIn(("scan",), history)
        self.assertIn(("hide",), history)
        self.assertIn(1500, calls)


if __name__ == "__main__":
    unittest.main()
