import os
import subprocess

from pydantic import Field

from mcp.server import FastMCP

from .utils import get_allowed_apps, is_dangerous_blocking_enabled, validate_script

mcp = FastMCP("MCP AppleScript", log_level="INFO")


@mcp.tool()
async def status() -> dict:
    """Returns the list of allowed apps and whether dangerous command blocking is enabled."""
    allowed_apps = get_allowed_apps()

    if "*" in allowed_apps:
        apps_display = "all applications"
    elif not allowed_apps:
        apps_display = "none (all blocked)"
    else:
        apps_display = allowed_apps

    return {
        "allowed_apps": apps_display,
        "block_dangerous": is_dangerous_blocking_enabled(),
    }


@mcp.tool()
async def run_applescript(
    script: str = Field(description="AppleScript code to execute."),
) -> str:
    """
    Execute AppleScript commands on macOS.
    Use 'tell application "AppName"' to control apps. Multi-line scripts supported.
    Returns plain text output, truncated to 10,000 chars for large results.
    Access limited to allowed apps (configure ALLOWED_APPS). Dangerous operations blocked.
    """
    timeout = int(os.getenv("TIMEOUT", "30"))
    max_output = int(os.getenv("MAX_OUTPUT", "10000"))

    is_safe, error_message, _ = validate_script(script)
    if not is_safe:
        raise RuntimeError(error_message)

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            output = result.stdout.strip()

            if not output:
                return "Script executed successfully (no output)"

            # Truncate if output exceeds limit
            if len(output) > max_output:
                truncated = output[:max_output]
                return (
                    f"{truncated}\n\n"
                    f"[Output truncated: {len(output):,} characters total, showing first {max_output:,}]"
                )

            return output
        else:
            raise RuntimeError(f"AppleScript execution failed: {result.stderr.strip()}")

    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Script execution timed out after {timeout} seconds") from e
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Failed to execute AppleScript: {str(e)}") from e


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
