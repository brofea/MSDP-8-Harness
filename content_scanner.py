import re
from typing import Any

SENSITIVE_PATTERNS = {
    "phone": (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "手机号"),
    "id_card": (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "身份证号"),
    "api_key": (
        re.compile(r"(sk-[A-Za-z0-9_-]{6,}|api[_-]?key\s*[=:]\s*[\w-]+)", re.IGNORECASE),
        "疑似 API Key",
    ),
    "private_ip": (
        re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"),
        "内网 IP 地址",
    ),
}

INJECTION_PATTERNS = {
    "ignore_rules": (
        re.compile(
            r"(忽略|忘记|无视)\s*(所有|上述|之前|一切)?\s*的?\s*(规则|指令|要求|限制)",
            re.IGNORECASE,
        ),
        "疑似提示注入：试图覆盖系统规则",
    ),
    "forced_action": (
        re.compile(r"(你\s*(现在|必须|应当|应该)\s*(执行|运行|操作|删除|修改))", re.IGNORECASE),
        "疑似提示注入：试图强制 Agent 执行操作",
    ),
    "role_spoofing": (
        re.compile(r"(?im)^\s*(system|assistant|user)\s*:\s*"),
        "疑似提示注入：尝试伪造对话角色",
    ),
}


def scan_content(content: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for name, (pattern, label) in SENSITIVE_PATTERNS.items():
        for match in pattern.finditer(content):
            findings.append(
                {
                    "category": "sensitive_info",
                    "type": name,
                    "label": label,
                    "position": match.start(),
                    "matched": match.group(),
                }
            )

    for name, (pattern, label) in INJECTION_PATTERNS.items():
        for match in pattern.finditer(content):
            findings.append(
                {
                    "category": "prompt_injection",
                    "type": name,
                    "label": label,
                    "position": match.start(),
                    "matched": match.group(),
                }
            )

    return sorted(findings, key=lambda item: item["position"])


def redact_content(content: str, findings: list[dict[str, Any]]) -> str:
    redacted = content
    for finding in sorted(findings, key=lambda item: item["position"], reverse=True):
        start = finding["position"]
        end = start + len(finding["matched"])
        placeholder = f"[{finding['type'].upper()}]"
        redacted = redacted[:start] + placeholder + redacted[end:]
    return redacted
