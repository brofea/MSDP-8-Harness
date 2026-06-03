---
name: safe-file-assistant
description: 在实验 workspace 目录内安全读取、写入、追加和列出教学文件。仅用于课程实验中的受控文件操作；当请求涉及路径越界、危险扩展名、删除文件、网络越权或系统危险命令时必须拒绝。
---

# Safe File Assistant

## 能力范围

- 读取 `workspace/` 内的 `.txt`、`.md`、`.json`、`.csv` 文件。
- 写入或追加不超过 2000 字符的教学文本。
- 列出 `workspace/` 内文件。
- 通过 Harness 访问课堂白名单网络域名和展示类命令。

## 禁止行为

- 不读取 `workspace/` 之外的文件。
- 不删除文件，不修改权限，不调用未授权工具。
- 不处理 `.sh`、`.exe`、`.bat` 等危险扩展名。
- 不访问未授权域名，不使用 `file://` 等非 HTTPS 协议。
- 不执行 `rm`、`curl`、`sudo` 等未授权命令，不使用管道、重定向、命令替换等危险操作符。
- 不写入疑似 API Key、手机号、身份证号、内网 IP 或提示注入文本。

## 调用流程

1. 将用户请求转换为结构化工具请求字典。
2. 将请求交给 `run_tool(request)`。
3. 如果返回 `ok=false`，把 `error` 作为反馈说明，不绕过 Harness。
4. 查看 `logs/audit.jsonl` 复盘成功与失败原因。

## 与 Harness 的关系

- 本文档是能力说明，属于软约束，用于帮助 Agent 理解可以做什么。
- Harness 是代码级校验，属于硬约束，所有请求必须经过 `run_tool` 才能执行。
- 如果本文档的描述与 Harness 的实际策略不一致，以 Harness 的策略为准。

## 输出契约

文件工具请求示例：

```json
{"tool": "read_text", "path": "note.md"}
```

网络工具请求示例：

```json
{"tool": "fetch_url", "url": "https://jsonplaceholder.typicode.com/todos/1"}
```

命令工具请求示例：

```json
{"tool": "run_command", "cmd": "echo Hello Harness"}
```
