from __future__ import annotations

import shutil
import subprocess
import time
from typing import Any

from scan_matchers import contains_any_alias, output_contains_any

try:
    import winreg
except Exception:
    winreg = None


AppAliases = dict[str, list[str]]
AppCatalog = dict[str, dict[str, str]]
RegistryCache = dict[str, float | list[str]]
ScanCache = dict[str, float | set[str]]


def get_app_aliases(app_name: str, app_id: str, app_aliases: AppAliases) -> list[str]:
    app_id_lower = app_id.lower()
    aliases = {app_name.lower(), app_id_lower, app_id_lower.replace(".exe", ""), app_id_lower.split(".")[-1]}
    for alias in app_aliases.get(app_name, []):
        aliases.add(alias.lower())
    return sorted((alias for alias in aliases if alias), key=len, reverse=True)


def scan_registry_uninstall(root: Any, subkey: str, winreg_module: Any = None) -> list[str]:
    reg = winreg_module or winreg
    names = []
    if reg is None:
        return names
    try:
        with reg.OpenKey(root, subkey) as key:
            for i in range(0, reg.QueryInfoKey(key)[0]):
                try:
                    skey_name = reg.EnumKey(key, i)
                    with reg.OpenKey(key, skey_name) as sk:
                        try:
                            display_name = reg.QueryValueEx(sk, "DisplayName")[0]
                            names.append(display_name)
                        except Exception:
                            pass
                except Exception:
                    continue
    except Exception:
        pass
    return names


def get_registry_display_names(
    registry_cache: RegistryCache,
    registry_cache_ttl_sec: int,
    use_cache: bool = True,
    winreg_module: Any = None,
    time_module: Any = None,
) -> list[str]:
    reg = winreg_module or winreg
    clock = time_module or time
    if reg is None:
        return []
    now = clock.time()
    if use_cache and now - registry_cache["timestamp"] < registry_cache_ttl_sec:
        return list(registry_cache["names"])
    found_names = []
    found_names += scan_registry_uninstall(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg_module=reg)
    found_names += scan_registry_uninstall(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", winreg_module=reg)
    found_names += scan_registry_uninstall(reg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg_module=reg)
    registry_cache["timestamp"] = now
    registry_cache["names"] = list(found_names)
    return found_names


def get_registry_app_details(app_name: str, app_id: str, app_aliases: AppAliases, winreg_module: Any = None) -> dict[str, str]:
    reg = winreg_module or winreg
    if reg is None:
        return {}

    aliases = get_app_aliases(app_name, app_id, app_aliases)
    registry_paths = [
        (reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (reg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root, subkey in registry_paths:
        try:
            with reg.OpenKey(root, subkey) as key:
                for i in range(0, reg.QueryInfoKey(key)[0]):
                    try:
                        skey_name = reg.EnumKey(key, i)
                        with reg.OpenKey(key, skey_name) as sk:
                            display_name = reg.QueryValueEx(sk, "DisplayName")[0]
                            if not contains_any_alias(display_name, aliases):
                                continue

                            details = {"name": display_name}
                            for value_name, target_key in [("DisplayVersion", "version"), ("Publisher", "publisher")]:
                                try:
                                    details[target_key] = reg.QueryValueEx(sk, value_name)[0]
                                except Exception:
                                    pass
                            return details
                    except Exception:
                        continue
        except Exception:
            continue

    return {}


def get_winget_package_details(app_id: str, subprocess_module: Any = None, shutil_module: Any = None) -> dict[str, str]:
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    winget_path = shell_api.which("winget")
    if winget_path is None:
        return {}

    try:
        result = process_api.run(
            [winget_path, "show", "--id", app_id, "--exact", "--accept-source-agreements"],
            stdout=process_api.PIPE,
            stderr=process_api.PIPE,
            text=True,
            creationflags=process_api.CREATE_NO_WINDOW,
        )
    except Exception:
        return {}

    output = result.stdout or ""
    details = {}
    for line in output.splitlines():
        clean_line = line.strip()
        if ":" not in clean_line:
            continue
        key, value = [part.strip() for part in clean_line.split(":", 1)]
        lowered = key.lower()
        if lowered in {"publisher", "author", "yayımlayan", "yayıncı", "yayinci"} and value:
            details["publisher"] = value
        elif lowered in {"version", "sürüm", "surum"} and value:
            details["version"] = value
    return details


def get_installed_version(app_name: str, app_id: str, app_aliases: AppAliases, winreg_module: Any = None) -> str:
    registry_details = get_registry_app_details(app_name, app_id, app_aliases, winreg_module=winreg_module)
    return (registry_details.get("version") or "").strip()


def has_available_upgrade(
    app_name: str,
    app_id: str,
    app_aliases: AppAliases,
    subprocess_module: Any = None,
    shutil_module: Any = None,
) -> tuple[bool, str]:
    # Mevcut versiyonu winget show ile sorgula (upgrade başlatmaz)
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    winget_path = shell_api.which("winget")
    if winget_path is None:
        return False, "winget_missing"
    
    try:
        result = process_api.run(
            [winget_path, "show", "--id", app_id, "--exact", "--accept-source-agreements"],
            stdout=process_api.PIPE,
            stderr=process_api.PIPE,
            text=True,
            creationflags=process_api.CREATE_NO_WINDOW,
            errors="replace",
        )
    except Exception:
        return False, "unknown"

    output_text = result.stdout or ""
    
    # Kurulu ve mevcut versiyonları çıkart
    installed_version = ""
    available_version = ""
    in_installed_section = False
    
    for line in output_text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Kurulu sürüm bölümünü belirle
        if "installed version" in clean_line.lower() or "kurulu sürüm" in clean_line.lower() or "kurulu surum" in clean_line.lower():
            in_installed_section = True
            if ":" in clean_line:
                _, version = clean_line.split(":", 1)
                installed_version = version.strip()
            continue
            
        # Available version bölümünü belirle
        if "available version" in clean_line.lower() or "mevcut sürüm" in clean_line.lower() or "mevcut surum" in clean_line.lower():
            if ":" in clean_line:
                _, version = clean_line.split(":", 1)
                available_version = version.strip()
            continue
        
        # Basit version ayrıştırması
        if ":" not in clean_line:
            continue
            
        key, value = [part.strip() for part in clean_line.split(":", 1)]
        key_lower = key.lower()
        
        if in_installed_section and key_lower in {"version", "sürüm", "surum"}:
            installed_version = value
            in_installed_section = False
        elif key_lower in {"version", "sürüm", "surum"} and not available_version:
            available_version = value
    
    # Güncellemesi olmadığını belirten çıktıları kontrol et
    output_lower = output_text.lower()
    if any(token in output_lower for token in ["no available upgrade found", "no newer package versions are available", "güncelleme bulunamadı", "daha yeni sürüm bulunamadı", "yükseltme bulunamadı"]):
        return False, "up_to_date"
    
    # Eğer mevcut versiyon bilgisi yoksa
    if not available_version and not installed_version:
        return False, "unknown"
    
    # Versiyonları karşılaştır (basit string karşılaştırması)
    if available_version and installed_version and available_version != installed_version:
        return True, "available"
    
    return False, "up_to_date"


def is_app_installed_via_winget(app_id: str, subprocess_module: Any = None, shutil_module: Any = None) -> bool:
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    winget_path = shell_api.which("winget")
    if winget_path is None:
        return False
    try:
        result = process_api.run(
            [winget_path, "list", "--id", app_id],
            stdout=process_api.PIPE,
            stderr=process_api.PIPE,
            text=True,
            creationflags=process_api.CREATE_NO_WINDOW,
        )
        output = (result.stdout or "").lower()
        return app_id.lower() in output
    except Exception:
        return False


def get_bulk_update_candidates(
    apps: AppCatalog,
    app_aliases: AppAliases,
    subprocess_module: Any = None,
    shutil_module: Any = None,
) -> tuple[list[str], str]:
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    winget_path = shell_api.which("winget")
    if winget_path is None:
        return [], "winget_missing"
    try:
        result = process_api.run(
            [winget_path, "upgrade"],
            stdout=process_api.PIPE,
            stderr=process_api.PIPE,
            text=True,
            creationflags=process_api.CREATE_NO_WINDOW,
            errors="replace",
        )
    except Exception:
        return [], "unknown"

    output_text = "\n".join(part for part in [result.stdout, result.stderr] if part).lower()
    if output_contains_any(output_text, ["no installed package found", "no available upgrade found", "no newer package versions are available"]):
        return [], "up_to_date"

    matched_apps = []
    for app_name, app_info in apps.items():
        aliases = get_app_aliases(app_name, app_info["id"], app_aliases)
        if contains_any_alias(output_text, aliases) and is_app_installed_via_winget(app_info["id"], subprocess_module=process_api, shutil_module=shell_api):
            matched_apps.append(app_name)
    return sorted(set(matched_apps)), "available" if matched_apps else "unknown"


def get_installed_apps_snapshot(
    apps: AppCatalog,
    app_aliases: AppAliases,
    scan_cache: ScanCache,
    scan_cache_ttl_sec: int,
    registry_cache: RegistryCache,
    registry_cache_ttl_sec: int,
    force_refresh: bool = False,
    subprocess_module: Any = None,
    shutil_module: Any = None,
    winreg_module: Any = None,
    time_module: Any = None,
) -> tuple[set[str], bool]:
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    reg = winreg_module or winreg
    clock = time_module or time

    installed_apps = set()
    now = clock.time()
    if (not force_refresh) and (now - scan_cache["timestamp"] < scan_cache_ttl_sec):
        return set(scan_cache["installed"]), True

    winget_path = shell_api.which("winget")
    winget_full_output = ""
    if winget_path:
        try:
            winget_list = process_api.run(
                [winget_path, "list"],
                stdout=process_api.PIPE,
                stderr=process_api.PIPE,
                text=True,
                creationflags=process_api.CREATE_NO_WINDOW,
            )
            winget_full_output = (winget_list.stdout or "").lower()
        except Exception:
            winget_full_output = ""

    unresolved_apps = []
    for app_name, app_info in apps.items():
        aliases = get_app_aliases(app_name, app_info["id"], app_aliases)
        if winget_full_output and contains_any_alias(winget_full_output, aliases):
            installed_apps.add(app_name)
            continue
        unresolved_apps.append((app_name, aliases))

    if unresolved_apps and reg is not None:
        registry_names = get_registry_display_names(
            registry_cache,
            registry_cache_ttl_sec,
            use_cache=True,
            winreg_module=reg,
            time_module=clock,
        )
        registry_blob = "\n".join(registry_names).lower()
        for app_name, aliases in unresolved_apps:
            if contains_any_alias(registry_blob, aliases):
                installed_apps.add(app_name)

    if winget_path is None and reg is None:
        return set(), False

    scan_cache["timestamp"] = clock.time()
    scan_cache["installed"] = set(installed_apps)
    return set(installed_apps), False


def is_app_installed(
    app_name: str,
    app_id: str,
    app_aliases: AppAliases,
    registry_cache: RegistryCache,
    registry_cache_ttl_sec: int,
    subprocess_module: Any = None,
    shutil_module: Any = None,
    winreg_module: Any = None,
    time_module: Any = None,
) -> bool:
    process_api = subprocess_module or subprocess
    shell_api = shutil_module or shutil
    reg = winreg_module or winreg
    aliases = get_app_aliases(app_name, app_id, app_aliases)
    winget_path = shell_api.which("winget")
    if winget_path:
        try:
            result = process_api.run(
                [winget_path, "list", "--id", app_id],
                stdout=process_api.PIPE,
                stderr=process_api.PIPE,
                text=True,
                creationflags=process_api.CREATE_NO_WINDOW,
            )
            if contains_any_alias((result.stdout or "").lower(), aliases):
                return True
        except Exception:
            pass
        try:
            all_result = process_api.run(
                [winget_path, "list"],
                stdout=process_api.PIPE,
                stderr=process_api.PIPE,
                text=True,
                creationflags=process_api.CREATE_NO_WINDOW,
            )
            if contains_any_alias((all_result.stdout or "").lower(), aliases):
                return True
        except Exception:
            pass
    registry_blob = "\n".join(
        get_registry_display_names(
            registry_cache,
            registry_cache_ttl_sec,
            use_cache=False,
            winreg_module=reg,
            time_module=time_module,
        )
    ).lower()
    return contains_any_alias(registry_blob, aliases)
