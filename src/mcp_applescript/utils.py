"""Security utilities for AppleScript execution."""

import os
import re


def get_allowed_apps() -> list[str]:
    """
    Get the list of allowed applications from environment variable.
    """
    # Default to "*" if not set
    allowed = os.getenv("ALLOWED_APPS", "*").strip()

    # Empty string means explicit lockdown
    if not allowed:
        return []

    # Wildcard means allow all
    if allowed == "*":
        return ["*"]

    # Parse comma-separated list, normalize to title case for AppleScript
    return [app.strip().title() for app in allowed.split(",") if app.strip()]


def is_dangerous_blocking_enabled() -> bool:
    """
    Check if dangerous pattern blocking is enabled.
    """
    value = os.getenv("BLOCK_DANGEROUS", "true").lower()
    return value in ("true", "1", "yes", "on")


def extract_applications(script: str) -> list[str]:
    """
    Extract application names from AppleScript.
    """
    pattern = r'tell\s+(?:application|app)\s+"([^"]+)"'
    matches = re.findall(pattern, script, re.IGNORECASE)
    return list(set(app.title() for app in matches))


def check_allowed_apps(apps: list[str], allowed: list[str]) -> tuple[bool, str]:
    """
    Validate applications against allowlist.
    """
    if "*" in allowed:
        return True, ""

    if not apps:
        return True, ""

    if not allowed:
        error = (
            f"AppleScript blocked: All applications are blocked\n"
            f"Applications found in script: {', '.join(apps)}\n"
            f"Configure via: ALLOWED_APPS environment variable"
        )
        return False, error

    blocked_apps = [app for app in apps if app not in allowed]

    if blocked_apps:
        error = (
            f"AppleScript blocked: Application(s) not in allowlist: {', '.join(blocked_apps)}\n"
            f"Allowed applications: {', '.join(allowed)}\n"
            f"Configure via: ALLOWED_APPS environment variable"
        )
        return False, error

    return True, ""


def detect_dangerous_patterns(script: str) -> list[str]:
    """
    Detect dangerous patterns in AppleScript.
    """
    dangerous = []

    # Pattern definitions: (pattern, description)
    patterns = [
        (r"\bdo\s+shell\s+script\b", "do shell script (arbitrary command execution)"),
        (r"\bshutdown\b", "shutdown (system control)"),
        (r"\brestart\b", "restart (system control)"),
        (r"\blog\s+out\b", "log out (system control)"),
        (r"\bsleep\b", "sleep (system control)"),
        (r"/System/", "access to /System directory"),
        (r"/Library/", "access to /Library directory"),
        (r"~/\.ssh/", "access to SSH keys"),
        (r"/etc/", "access to /etc directory"),
        (r"/private/", "access to /private directory"),
        (r"with\s+hidden\s+answer", "password prompt (potential phishing)"),
        (r"\bdelete\s+file\b", "file deletion"),
        (r"\bmove\s+.*\s+to\s+trash\b", "move to trash"),
    ]

    for pattern, description in patterns:
        if re.search(pattern, script, re.IGNORECASE):
            dangerous.append(description)

    return dangerous


def validate_script(script: str) -> tuple[bool, str, dict]:
    """
    Validate AppleScript for security concerns and allowed apps.
    """
    metadata = {
        "applications": [],
        "dangerous_patterns": [],
        "blocked_by": None,
    }

    # Extract applications
    apps = extract_applications(script)
    metadata["applications"] = apps

    # Check allowlist
    allowed_apps = get_allowed_apps()
    is_allowed, allowlist_error = check_allowed_apps(apps, allowed_apps)

    if not is_allowed:
        metadata["blocked_by"] = "allowlist"
        return False, allowlist_error, metadata

    # Check dangerous patterns (if enabled)
    if is_dangerous_blocking_enabled():
        dangerous = detect_dangerous_patterns(script)
        metadata["dangerous_patterns"] = dangerous

        if dangerous:
            metadata["blocked_by"] = "dangerous_patterns"
            patterns_list = "\n".join(f"  - {pattern}" for pattern in dangerous)
            error = (
                f"AppleScript blocked: Dangerous pattern(s) detected:\n"
                f"{patterns_list}\n\n"
                "To override, set: BLOCK_DANGEROUS=false"
            )
            return False, error, metadata

    return True, "", metadata
