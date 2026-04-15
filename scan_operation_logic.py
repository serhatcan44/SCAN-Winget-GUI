from __future__ import annotations

CANCEL_TOKENS = ["cancel", "canceled", "cancelled", "iptal", "1602"]
NO_UPGRADE_TOKENS = [
    "no available upgrade found",
    "no newer package versions are available",
    "güncelleme bulunamadı",
    "daha yeni sürüm bulunamadı",
    "yükseltme bulunamadı",
]
NOT_INSTALLED_TOKENS = [
    "no installed package found",
    "paket yüklü değil",
    "kurulu paket bulunamadı",
]


def get_manage_action_meta(action: str) -> tuple[str, str]:
    if action == "install":
        return "yükleniyor", "Yükleme"
    return "kaldırılıyor", "Kaldırma"


def build_manage_command(winget_path: str, action: str, app_id: str) -> list[str]:
    cmd = [winget_path, action, "--id", app_id, "--exact"]
    if action == "install":
        cmd += ["--accept-package-agreements", "--accept-source-agreements"]
    return cmd


def build_upgrade_command(winget_path: str, app_id: str) -> list[str]:
    return [winget_path, "upgrade", "--id", app_id, "--exact", "--accept-package-agreements", "--accept-source-agreements"]


def summarize_bulk_update(success_count: int, skipped_count: int, failed_count: int) -> str:
    return f"{success_count} başarılı, {skipped_count} atlandı, {failed_count} başarısız."
