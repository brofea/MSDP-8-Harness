from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

WORKSPACE_DIR = (BASE_DIR / "workspace").resolve()
BLOCKED_DIR = (BASE_DIR / "blocked").resolve()
LOG_DIR = (BASE_DIR / "logs").resolve()
AUDIT_LOG = LOG_DIR / "audit.jsonl"

FILE_TOOLS = {
    "read_text",
    "write_text",
    "append_text",
    "list_files",
}

NETWORK_TOOLS = {"fetch_url"}
COMMAND_TOOLS = {"run_command"}
ALLOWED_TOOLS = FILE_TOOLS | NETWORK_TOOLS | COMMAND_TOOLS

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}
MAX_WRITE_CHARS = 2000

SCAN_ON_WRITE = True
BLOCK_ON_SENSITIVE = True
BLOCK_ON_INJECTION = True
