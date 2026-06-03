import shlex
import subprocess

ALLOWED_COMMANDS = {"echo", "date", "wc"}
BLOCKED_OPERATORS = {"|", ">", "<", "`", "$(", "&", ";", "||", "&&"}


class CommandHarnessError(Exception):
    pass


def validate_command(cmd: str) -> list[str]:
    cmd = cmd.strip()
    if not cmd:
        raise CommandHarnessError("命令不能为空")

    for operator in BLOCKED_OPERATORS:
        if operator in cmd:
            raise CommandHarnessError(f"检测到危险操作符：{operator}")

    try:
        parts = shlex.split(cmd)
    except ValueError as exc:
        raise CommandHarnessError(f"命令解析失败：{exc}") from exc

    if not parts:
        raise CommandHarnessError("命令解析结果为空")
    if parts[0] not in ALLOWED_COMMANDS:
        raise CommandHarnessError(f"不允许的命令：{parts[0]}")

    return parts


def run_command(cmd: str) -> str:
    parts = validate_command(cmd)
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            input="",
            timeout=10,
            cwd="/tmp",
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandHarnessError("命令执行超时") from exc

    output = result.stdout.strip()
    if result.stderr:
        output = (output + "\n" if output else "") + "[stderr] " + result.stderr.strip()
    return output
