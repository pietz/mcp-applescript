# MCP AppleScript

An MCP (Model Context Protocol) server that enables Large Language Models to execute AppleScript commands on macOS. This allows LLMs to interact with and automate macOS applications through natural language requests.

## Features

- Execute AppleScript commands from LLM applications
- **Application allowlist** for controlled access to specific apps
- **Dangerous pattern detection** to block risky operations
- Configurable timeout protection
- Built on FastMCP for easy integration

## Installation

Using uv:

```bash
uv pip install mcp-applescript
```

Or install from source:

```bash
git clone https://github.com/pietz/mcp-applescript.git
cd mcp-applescript
uv sync
```

## Usage

### Running the Server

```bash
mcp-applescript
```

The server runs using stdio transport, making it compatible with any MCP client.

### Available Tools

#### `run_applescript`

Execute an AppleScript command on macOS.

**Parameters:**
- `script` (string): The AppleScript code to execute

**Returns:**
- String output from the script execution
- Raises error if script fails validation or execution

**Example:**

```applescript
tell application "Mail"
    get subject of first message of inbox
end tell
```

#### `get_server_status`

Get the current server configuration and security settings.

**Returns:**
- Server version and configuration
- Allowed applications list
- Security settings (dangerous pattern blocking, timeout)
- Environment variable documentation

**Example Response:**
```json
{
  "server": "MCP AppleScript",
  "version": "0.1.0",
  "security": {
    "allowed_apps": ["Mail", "Calendar"],
    "block_dangerous": true,
    "timeout_seconds": 30
  }
}
```

## Configuration

### MCP Client Setup

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "applescript": {
      "command": "mcp-applescript",
      "env": {
        "ALLOWED_APPS": "mail,calendar,contacts,notes",
        "BLOCK_DANGEROUS": "true"
      }
    }
  }
}
```

### Environment Variables

**`ALLOWED_APPS`** (optional)
- Comma-separated list of allowed applications (case-insensitive)
- Example: `"mail,calendar,contacts"` (lowercase recommended)
- **Not set** (default): Allows all applications (`"*"`)
- `"*"`: Explicitly allows all applications
- `""` (empty string): Blocks all applications (lockdown mode)
- **Security Note**: Set this to restrict access to specific apps only
- App names are automatically normalized to title case for AppleScript

**`BLOCK_DANGEROUS`** (optional)
- Enable/disable dangerous pattern detection
- Values: `"true"` or `"false"`
- Default: `"true"`
- Blocks patterns like: `do shell script`, file system access, system control commands

**`TIMEOUT`** (optional)
- Script execution timeout in seconds
- Default: `"30"`

### Security Profiles

#### Default (Out of the Box)
```json
"env": {
  // ALLOWED_APPS not set = allow all apps
  "BLOCK_DANGEROUS": "true"  // This is the default, can be omitted
}
```
- ✅ Works immediately without configuration
- ✅ Dangerous operations blocked
- ⚠️ Can access any application

#### Strict (Recommended for Production)
```json
"env": {
  "ALLOWED_APPS": "mail,calendar,contacts",
  "BLOCK_DANGEROUS": "true"
}
```
- ✅ Limited to specific applications
- ✅ Dangerous operations blocked
- ✅ Best security posture

#### Permissive (Development/Testing Only)
```json
"env": {
  "ALLOWED_APPS": "*",  // or omit this line
  "BLOCK_DANGEROUS": "false"
}
```
- ⚠️ Can access any application
- ⚠️ Dangerous operations allowed
- ⚠️ Use only in trusted environments

#### Lockdown (Explicit Block)
```json
"env": {
  "ALLOWED_APPS": ""  // Empty string = block all
}
```
- 🔒 Blocks all AppleScript execution
- Useful for temporary disabling

## Security

### Built-in Protections

1. **Application Allowlist** (optional)
   - Default: All applications allowed (for usability)
   - Configure `ALLOWED_APPS` to restrict to specific applications
   - Prevents unauthorized access to system apps when configured

2. **Dangerous Pattern Detection**
   - Blocks shell command execution (`do shell script`)
   - Prevents system control operations (shutdown, restart, logout)
   - Blocks access to sensitive paths (`/System`, `/Library`, `~/.ssh`)
   - Detects potential phishing (password dialogs)
   - Prevents file deletion operations

3. **Execution Timeout**
   - Prevents infinite loops and hanging scripts
   - Configurable timeout duration

### Blocked Operations Examples

```applescript
-- ❌ BLOCKED: Shell command execution
do shell script "rm -rf ~/"

-- ❌ BLOCKED: System control
tell application "System Events" to shut down

-- ❌ BLOCKED: Sensitive file access
do shell script "cat ~/.ssh/id_rsa"

-- ❌ BLOCKED: Unauthorized application (if not in ALLOWED_APPS)
tell application "Terminal" to do script "echo test"

-- ✅ ALLOWED: Reading from allowed app
tell application "Mail"
    get subject of first message of inbox
end tell
```

### Best Practices

- **Configure application allowlist**: Set `ALLOWED_APPS` to only the applications you need for production use
- **Keep dangerous blocking enabled**: Default is on - provides essential protection
- **Review server status**: Use `get_server_status` tool to understand current configuration
- **Principle of least privilege**: In production, only allow the minimum necessary applications
- **Start permissive, then restrict**: Begin with defaults, then lock down based on actual usage

## Usage Examples

### Check Server Configuration

Before running scripts, check what's allowed:

```
User: "What can you access on my system?"

LLM uses: get_server_status()

Response: "I can currently access: Mail, Calendar, and Contacts.
Dangerous operations are blocked, and scripts timeout after 30 seconds."
```

### Read Mail (Allowed)

```applescript
tell application "Mail"
    get subject of first message of inbox
end tell
```

### Get Calendar Events (Allowed)

```applescript
tell application "Calendar"
    get summary of every event of calendar "Work"
end tell
```

### System Information (Blocked - Security)

```applescript
-- This will be BLOCKED if "System Events" not in ALLOWED_APPS
tell application "System Events"
    name of first process whose frontmost is true
end tell
```

### Display Notification (Safe)

```applescript
-- Safe if no dangerous patterns
display notification "Hello from MCP!" with title "AppleScript"
```

## Requirements

- Python >= 3.12
- macOS (AppleScript is macOS-only)
- mcp >= 1.13.1

## License

MIT

## Author

Paul-Louis Pr�ve
