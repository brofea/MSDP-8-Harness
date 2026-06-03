import json
from datetime import datetime
from pathlib import Path
from typing import Any

import command_tools
import network_tools
import tools
from content_scanner import scan_content
from policy import (
    ALLOWED_EXTENSIONS,
    ALLOWED_TOOLS,
    AUDIT_LOG,
    BLOCK_ON_INJECTION,
    BLOCK_ON_SENSITIVE,
    COMMAND_TOOLS,
    FILE_TOOLS,
    LOG_DIR,
    MAX_WRITE_CHARS,
    NETWORK_TOOLS,
    SCAN_ON_WRITE,
    WORKSPACE_DIR,
)


class HarnessError(Exception):
    pass


def resolve_workspace_path(path_str: str) -> Path:
    candidate = (WORKSPACE_DIR / path_str).resolve()
    try:
        candidate.relative_to(WORKSPACE_DIR)
    except ValueError as exc:
        raise HarnessError(f"路径越界：{path_str}") from exc

    if candidate.suffix and candidate.suffix not in ALLOWED_EXTENSIONS:
        raise HarnessError(f"不允许的文件类型：{candidate.suffix}")

    return candidate


def audit(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event["time"] = datetime.now().isoformat(timespec="seconds")
    with AUDIT_LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def _validate_content_security(tool_name: str, content: str) -> None:
    if not (SCAN_ON_WRITE and content and tool_name in {"write_text", "append_text"}):
        return

    findings = scan_content(content)
    if not findings:
        return

    sensitive = [item for item in findings if item["category"] == "sensitive_info"]
    injection = [item for item in findings if item["category"] == "prompt_injection"]
    messages: list[str] = []

    if sensitive and BLOCK_ON_SENSITIVE:
        labels = ", ".join(sorted({item["label"] for item in sensitive}))
        messages.append(f"发现 {len(sensitive)} 处疑似敏感信息：{labels}")
    if injection and BLOCK_ON_INJECTION:
        labels = ", ".join(sorted({item["label"] for item in injection}))
        messages.append(f"发现 {len(injection)} 处疑似注入指令：{labels}")

    if messages:
        raise HarnessError("内容安全检查未通过：" + "；".join(messages))


def validate_request(request: dict[str, Any]) -> None:
    if not isinstance(request, dict):
        raise HarnessError("工具请求必须是字典")

    tool_name = request.get("tool")
    if tool_name not in ALLOWED_TOOLS:
        raise HarnessError(f"工具未授权：{tool_name}")

    if tool_name in NETWORK_TOOLS:
        url = request.get("url")
        if not isinstance(url, str) or not url.strip():
            raise HarnessError("fetch_url 需要 url 参数")
        network_tools.validate_url(url)
        return

    if tool_name in COMMAND_TOOLS:
        cmd = request.get("cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            raise HarnessError("run_command 需要 cmd 参数")
        command_tools.validate_command(cmd)
        return

    if tool_name not in FILE_TOOLS:
        raise HarnessError(f"工具未实现：{tool_name}")

    path = request.get("path")
    if not isinstance(path, str) or not path.strip():
        raise HarnessError("path 参数必须是非空字符串")

    resolve_workspace_path(path)
    content = request.get("content", "")

    if tool_name in {"write_text", "append_text"}:
        if "content" not in request:
            raise HarnessError(f"{tool_name} 缺少 content 参数")
        if not isinstance(content, str):
            raise HarnessError("content 参数必须是字符串")
        if not content:
            raise HarnessError("content 参数必须是非空字符串")

    if tool_name in {"read_text", "list_files"} and "content" in request:
        raise HarnessError(f"{tool_name} 不应包含 content 参数")

    if isinstance(content, str) and len(content) > MAX_WRITE_CHARS:
        raise HarnessError("写入内容过长")

    _validate_content_security(tool_name, content if isinstance(content, str) else "")


def run_tool(request: dict[str, Any]) -> dict[str, Any]:
    try:
        validate_request(request)
        tool_name = request["tool"]

        if tool_name == "read_text":
            result = tools.read_text(resolve_workspace_path(request["path"]))
        elif tool_name == "write_text":
            result = tools.write_text(resolve_workspace_path(request["path"]), request["content"])
        elif tool_name == "append_text":
            result = tools.append_text(resolve_workspace_path(request["path"]), request["content"])
        elif tool_name == "list_files":
            result = tools.list_files(resolve_workspace_path(request["path"]))
        elif tool_name == "fetch_url":
            result = network_tools.fetch_url(request["url"])
        elif tool_name == "run_command":
            result = command_tools.run_command(request["cmd"])
        else:
            raise HarnessError(f"工具未实现：{tool_name}")

        response = {"ok": True, "result": result, "error": None}
        audit({"request": request, "response": response})
        return response

    except Exception as exc:
        response = {"ok": False, "result": None, "error": str(exc)}
        audit({"request": request, "response": response})
        return response


def build_feedback(response: dict[str, Any]) -> str:
    if response["ok"]:
        return f"工具执行成功，结果为：{response['result']}"
    return f"工具执行失败，原因：{response['error']}。请修改工具名或参数后重试。"
