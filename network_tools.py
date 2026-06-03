from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_DOMAINS = {"jsonplaceholder.typicode.com"}
ALLOWED_SCHEMES = {"https"}
MAX_RESPONSE_BYTES = 50_000


class NetworkHarnessError(Exception):
    pass


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise NetworkHarnessError(f"不允许的协议：{parsed.scheme}")
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise NetworkHarnessError(f"不允许的域名：{parsed.hostname}")
    return url


def fetch_url(url: str) -> str:
    validated = validate_url(url)
    request = Request(validated, headers={"User-Agent": "HarnessLab/1.0"})
    with urlopen(request, timeout=10) as response:
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type and "text" not in content_type:
            raise NetworkHarnessError(f"不允许的响应类型：{content_type}")
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise NetworkHarnessError("响应内容超过大小限制")
        return body.decode("utf-8", errors="replace")
