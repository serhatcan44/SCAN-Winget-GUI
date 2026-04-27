from __future__ import annotations

from scan_matchers import output_contains_any
from scan_operation_logic import CANCEL_TOKENS, NOT_INSTALLED_TOKENS, NO_UPGRADE_TOKENS


Feedback = dict[str, str | int | bool | None]


def extract_error_message(output_text: str) -> str:
    """Winget veya yardımcı araç çıktısından kısa hata özetini üret."""
    if not output_text:
        return "Detay bulunamadı"

    lines = output_text.strip().split("\n")
    error_indicators = [
        "error:",
        "failed:",
        "unable to",
        "permission denied",
        "not found",
        "hata:",
        "başarısız:",
        "erişim reddedildi",
        "bulunamadı",
        "eksik:",
    ]

    for line in lines:
        clean = line.strip().lower()
        for indicator in error_indicators:
            if indicator in clean and len(line.strip()) > 5:
                return line.strip()[:150]

    for line in reversed(lines):
        clean = line.strip()
        if clean and len(clean) > 5 and not clean.startswith("%"):
            return clean[:150]

    return "Detay bulunamadı"


def manage_precheck(
    action: str,
    currently_installed: bool,
    currently_installed_via_winget: bool,
    selected_app: str,
    operation_name: str,
) -> Feedback | None:
    if action == "install" and currently_installed:
        return {
            "title": "İşlem atlandı",
            "detail": f"{selected_app} zaten kurulu görünüyor.",
            "hint": "Yeniden kurulum akışı başlatılmadı.",
            "delay_ms": 1500,
            "history_status": "warning",
            "history_detail": "Uygulama zaten kurulu olduğu için yeniden kurulum başlatılmadı.",
            "refresh_scan": True,
        }
    if action == "uninstall" and not currently_installed:
        return {
            "title": "İşlem atlandı",
            "detail": f"{selected_app} sistemde kurulu görünmüyor.",
            "hint": None,
            "delay_ms": 1200,
            "history_status": "warning",
            "history_detail": "Uygulama sistemde kurulu görünmediği için kaldırma atlandı.",
            "refresh_scan": True,
        }
    if action == "uninstall" and currently_installed and not currently_installed_via_winget:
        return {
            "title": "İşlem atlandı",
            "detail": f"{selected_app} kurulu, ancak winget paketi bulunamadı.",
            "hint": "Bu kurulum uygulamanın kendi kaldırıcı aracı ile silinmeli.",
            "delay_ms": 1500,
            "history_status": "warning",
            "history_detail": "winget paketi bulunmadığı için kaldırma güvenli şekilde atlandı.",
            "refresh_scan": True,
        }
    return None


def manage_result(
    action: str,
    installed_now: bool,
    is_cancelled: bool,
    return_code: int,
    output_text: str,
    selected_app: str,
) -> Feedback:
    if action == "install":
        if installed_now:
            return {
                "title": "Kurulum tamamlandı",
                "detail": f"{selected_app} yüklendi.",
                "hint": "Kurulum doğrulandı.",
                "history_status": "success",
                "history_detail": "Kurulum tamamlandı ve uygulama kurulu olarak doğrulandı.",
            }
        if is_cancelled:
            return {
                "title": "Kurulum iptal edildi",
                "detail": f"{selected_app} yükleme iptal edildi.",
                "hint": "Kullanıcı kurulumu iptal etti.",
                "history_status": "warning",
                "history_detail": "Kurulum kullanıcı tarafından iptal edildi.",
            }
        if return_code != 0:
            error_detail = extract_error_message(output_text)
            return {
                "title": "Kurulum başarısız",
                "detail": f"{selected_app} yüklenemedi.",
                "hint": f"Kurulum komutu hata kodu ile sonlandı: {return_code}",
                "history_status": "error",
                "history_detail": f"Kurulum başarısız. Sebep: {error_detail}",
            }
        return {
            "title": "Kurulum doğrulanamadı",
            "detail": f"{selected_app} kurulumu doğrulanamadı.",
            "hint": "Kurulum sonrası doğrulama başarısız.",
            "history_status": "error",
            "history_detail": "Kurulum komutu bitti ancak sonuç doğrulanamadı.",
        }

    if not installed_now:
        return {
            "title": "Kaldırma tamamlandı",
            "detail": f"{selected_app} kaldırıldı.",
            "hint": "Kaldırma doğrulandı.",
            "history_status": "success",
            "history_detail": "Kaldırma tamamlandı ve uygulamanın kaldırıldığı doğrulandı.",
        }
    if is_cancelled:
        return {
            "title": "Kaldırma iptal edildi",
            "detail": f"{selected_app} kaldırma iptal edildi.",
            "hint": "Kullanıcı kaldırma adımını iptal etti.",
            "history_status": "warning",
            "history_detail": "Kaldırma kullanıcı tarafından iptal edildi.",
        }
    if output_contains_any(output_text, NOT_INSTALLED_TOKENS):
        return {
            "title": "Paket bulunamadı",
            "detail": f"{selected_app} winget ile kurulu bulunamadı.",
            "hint": "Paket listede görünmüyor.",
            "history_status": "warning",
            "history_detail": "winget tarafında kurulu paket bulunamadığı için kaldırma tamamlanamadı.",
        }
    if return_code != 0:
        error_detail = extract_error_message(output_text)
        return {
            "title": "Kaldırma başarısız",
            "detail": f"{selected_app} kaldırılamadı.",
            "hint": f"Kaldırma komutu hata kodu ile sonlandı: {return_code}",
            "history_status": "error",
            "history_detail": f"Kaldırma başarısız. Sebep: {error_detail}",
        }
    return {
        "title": "Kaldırma doğrulanamadı",
        "detail": f"{selected_app} kaldırma sonrası doğrulanamadı.",
        "hint": "Kaldırma sonrası doğrulama başarısız.",
        "history_status": "error",
        "history_detail": "Kaldırma komutu bitti ancak sonuç doğrulanamadı.",
    }


def update_precheck(currently_installed: bool, currently_installed_via_winget: bool, selected_app: str) -> Feedback | None:
    if not currently_installed:
        return {
            "title": "İşlem atlandı",
            "detail": f"{selected_app} sistemde kurulu görünmüyor.",
            "hint": "Güncelleme yalnızca kurulu uygulamalar için çalıştırılır.",
            "delay_ms": 1500,
            "history_status": "warning",
            "history_detail": "Uygulama kurulu görünmediği için güncelleme atlandı.",
            "refresh_scan": True,
        }
    if not currently_installed_via_winget:
        return {
            "title": "İşlem atlandı",
            "detail": f"{selected_app} için winget paketi bulunamadı.",
            "hint": "Bu kurulum winget dışından yapıldığı için güncelleme başlatılmadı.",
            "delay_ms": 1500,
            "history_status": "warning",
            "history_detail": "winget paketi bulunmadığı için güncelleme güvenli şekilde atlandı.",
            "refresh_scan": True,
        }
    return None


def update_result(
    return_code: int,
    still_installed: bool,
    version_before: str,
    version_after: str,
    output_text: str,
    selected_app: str,
) -> Feedback:
    is_cancelled = output_contains_any(output_text, CANCEL_TOKENS)
    no_upgrade_found = output_contains_any(output_text, NO_UPGRADE_TOKENS)

    if no_upgrade_found:
        return {
            "title": "Zaten güncel",
            "detail": f"{selected_app} için yeni sürüm bulunmadı.",
            "hint": "Komut çalıştı, ancak yeni güncelleme bulunamadı.",
            "history_status": "info",
            "history_detail": "Güncelleme komutu çalıştı ancak yeni sürüm bulunmadı.",
        }
    if return_code == 0 and still_installed and version_before and version_after and version_before != version_after:
        return {
            "title": "Güncelleme tamamlandı",
            "detail": f"{selected_app} {version_before} sürümünden {version_after} sürümüne güncellendi.",
            "hint": "Sürüm değişikliği doğrulandı.",
            "history_status": "success",
            "history_detail": f"Sürüm {version_before} sürümünden {version_after} sürümüne yükseltildi.",
        }
    if return_code == 0 and still_installed and not version_before and version_after:
        return {
            "title": "Güncelleme tamamlandı",
            "detail": f"{selected_app} güncellendi.",
            "hint": "Uygulama kurulu durumda kaldı; yeni sürüm bilgisi alındı.",
            "history_status": "success",
            "history_detail": "Güncelleme tamamlandı ve yeni sürüm bilgisi alındı.",
        }
    if return_code == 0 and still_installed and version_before == version_after:
        return {
            "title": "Güncelleme doğrulanamadı",
            "detail": f"{selected_app} komutu tamamlandı ancak sürüm değişmedi.",
            "hint": "winget başarılı döndü, fakat sürüm bilgisi değişmedi.",
            "history_status": "error",
            "history_detail": "Komut başarılı döndü ancak sürüm değişimi doğrulanamadı.",
        }
    if is_cancelled:
        return {
            "title": "Güncelleme iptal edildi",
            "detail": f"{selected_app} güncelleme iptal edildi.",
            "hint": "Kullanıcı güncellemeyi iptal etti.",
            "history_status": "warning",
            "history_detail": "Güncelleme kullanıcı tarafından iptal edildi.",
        }
    return {
        "title": "Güncelleme başarısız",
        "detail": f"{selected_app} güncellenemedi.",
        "hint": f"Güncelleme komutu hata kodu ile sonlandı: {return_code}",
        "history_status": "error",
        "history_detail": f"Güncelleme başarısız. Sebep: {extract_error_message(output_text)}",
    }


def helper_missing_feedback(exe_name: str = "idm.exe") -> Feedback:
    return {
        "title": "Yardımcı araç bulunamadı",
        "detail": f"{exe_name} dosyası proje klasöründe bulunamadı.",
        "hint": "Dosyayı SCAN.py ile aynı klasöre ekleyin.",
        "history_status": "error",
        "history_detail": f"{exe_name} proje klasöründe bulunamadığı için yardımcı araç başlatılamadı.",
    }


def helper_result(return_code: int, output_text: str) -> Feedback:
    if return_code == 0:
        return {
            "title": "Yardımcı araç tamamlandı",
            "detail": "Yardımcı araç başarıyla çalıştırıldı.",
            "hint": "Yardımcı araç işlemi sorunsuz tamamlandı.",
            "history_status": "success",
            "history_detail": "Yardımcı araç başarıyla çalıştırıldı.",
        }
    error_detail = extract_error_message(output_text)
    return {
        "title": "Yardımcı araç başarısız",
        "detail": "Yardımcı araç çalıştırılırken bir hata oluştu.",
        "hint": f"Yardımcı araç hata kodu ile sonlandı: {return_code}",
        "history_status": "error",
        "history_detail": f"Yardımcı araç başarısız. Sebep: {error_detail}",
    }


def bulk_precheck(status: str) -> Feedback | None:
    if status == "up_to_date":
        return {
            "title": "Yeni güncelleme yok",
            "detail": "Katalogdaki uygulamalar için yeni sürüm bulunmadı.",
            "hint": "Tüm izlenen uygulamalar güncel görünüyor.",
            "delay_ms": 1500,
            "history_status": "info",
            "history_detail": "İzlenen uygulamalar için yeni güncelleme bulunmadı.",
        }
    if status != "available":
        return {
            "title": "Aday bulunamadı",
            "detail": "Toplu güncelleme için uygun uygulama bulunamadı.",
            "hint": "winget çıktısı katalog ile eşleşmedi.",
            "delay_ms": 1500,
            "history_status": "warning",
            "history_detail": "Toplu güncelleme için uygun aday bulunamadı.",
        }
    return None


def bulk_item_result(return_code: int, version_before: str, version_after: str, installed_now: bool, output_text: str) -> tuple[str, str]:
    if output_contains_any(output_text, CANCEL_TOKENS):
        return "warning", "Güncelleme kullanıcı tarafından iptal edildi."
    if return_code == 0 and version_before and version_after and version_before != version_after:
        return "success", f"Sürüm {version_before} sürümünden {version_after} sürümüne yükseltildi."
    if return_code == 0 and installed_now:
        return "success", "Güncelleme komutu tamamlandı."
    error_detail = extract_error_message(output_text)
    return "error", f"Güncelleme başarısız. Sebep: {error_detail}"


def bulk_final_status(failed_count: int) -> str:
    return "success" if failed_count == 0 else "warning"
