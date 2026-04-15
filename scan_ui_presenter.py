from __future__ import annotations

from typing import Any, Callable

DEFAULT_PROGRESS_HINT = "Kurulum adımları canlı olarak burada gösterilir."


def show_progress_modal(
    progress_title_label: Any,
    progress_detail_label: Any,
    progress_modal_bar: Any,
    progress_hint_label: Any,
    progress_overlay: Any,
    progress_card: Any,
    title_text: str,
    detail_text: str = "",
    progress: float = 0.0,
) -> None:
    progress_title_label.configure(text=title_text)
    progress_detail_label.configure(text=detail_text)
    progress_modal_bar.set(progress)
    progress_hint_label.configure(text=DEFAULT_PROGRESS_HINT)
    progress_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    progress_overlay.lift()
    progress_card.lift()


def update_progress_modal(
    progress_title_label: Any,
    progress_detail_label: Any,
    progress_modal_bar: Any,
    title_text: str | None = None,
    detail_text: str | None = None,
    progress: float | None = None,
) -> None:
    if title_text is not None:
        progress_title_label.configure(text=title_text)
    if detail_text is not None:
        progress_detail_label.configure(text=detail_text)
    if progress is not None:
        progress_modal_bar.set(progress)


def hide_progress_modal(progress_overlay: Any) -> None:
    progress_overlay.place_forget()


def apply_operation_feedback(
    scheduler: Callable[[int, Callable[[], None]], None],
    update_progress: Callable[[str, str, float], None],
    set_hint: Callable[[str], None],
    add_history_item: Callable[[str, str, str, str], None],
    hide_progress: Callable[[], None],
    action_name: str,
    target_name: str,
    feedback: dict[str, Any],
    refresh_scan_callback: Callable[[], None] | None = None,
    refresh_details_callback: Callable[[], None] | None = None,
    hide_delay_ms: int = 1800,
) -> None:
    scheduler(0, lambda: update_progress(feedback["title"], feedback["detail"], feedback.get("progress", 0)))
    if feedback.get("hint"):
        scheduler(0, lambda hint=feedback["hint"]: set_hint(hint))
    add_history_item(action_name, target_name, feedback["history_status"], feedback["history_detail"])
    if refresh_scan_callback is not None:
        scheduler(0, refresh_scan_callback)
    if refresh_details_callback is not None:
        scheduler(0, refresh_details_callback)
    scheduler(hide_delay_ms, hide_progress)
