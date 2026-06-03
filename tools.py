from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"written:{path.name}"


def append_text(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(content)
    return f"appended:{path.name}"


def list_files(path: Path) -> list[str]:
    if not path.exists():
        return []
    if path.is_file():
        return [path.name]
    return sorted(item.name for item in path.iterdir())
