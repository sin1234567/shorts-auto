import json
import importlib.util
from pathlib import Path


def load_mark_posted_module():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "mark_posted.py"
    spec = importlib.util.spec_from_file_location("mark_posted", source_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_metadata(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_title": title}, ensure_ascii=False), encoding="utf-8")


def test_appends_source_title_from_metadata(tmp_path, monkeypatch):
    mark_posted = load_mark_posted_module()
    metadata = tmp_path / "out" / "metadata.json"
    posted = tmp_path / "data" / "posted_facts.txt"
    write_metadata(metadata, "風は気圧差で生まれる")

    monkeypatch.setattr(mark_posted, "METADATA", metadata)
    monkeypatch.setattr(mark_posted, "POSTED", posted)

    mark_posted.main()

    assert posted.read_text(encoding="utf-8") == "風は気圧差で生まれる\n"


def test_does_not_append_duplicates(tmp_path, monkeypatch):
    mark_posted = load_mark_posted_module()
    metadata = tmp_path / "out" / "metadata.json"
    posted = tmp_path / "data" / "posted_facts.txt"
    write_metadata(metadata, "風は気圧差で生まれる")
    posted.parent.mkdir(parents=True, exist_ok=True)
    posted.write_text("風は気圧差で生まれる\n", encoding="utf-8")

    monkeypatch.setattr(mark_posted, "METADATA", metadata)
    monkeypatch.setattr(mark_posted, "POSTED", posted)

    mark_posted.main()

    assert posted.read_text(encoding="utf-8") == "風は気圧差で生まれる\n"


def test_creates_parent_directory_if_needed(tmp_path, monkeypatch):
    mark_posted = load_mark_posted_module()
    metadata = tmp_path / "out" / "metadata.json"
    posted = tmp_path / "nested" / "data" / "posted_facts.txt"
    write_metadata(metadata, "松ぼっくりは湿ると閉じやすい")

    monkeypatch.setattr(mark_posted, "METADATA", metadata)
    monkeypatch.setattr(mark_posted, "POSTED", posted)

    assert not posted.parent.exists()

    mark_posted.main()

    assert posted.parent.exists()
    assert posted.read_text(encoding="utf-8") == "松ぼっくりは湿ると閉じやすい\n"


def test_record_posted_fact_returns_false_for_duplicates(tmp_path, monkeypatch):
    mark_posted = load_mark_posted_module()
    posted = tmp_path / "data" / "posted_facts.txt"
    posted.parent.mkdir(parents=True, exist_ok=True)
    posted.write_text("風は気圧差で生まれる\n", encoding="utf-8")

    monkeypatch.setattr(mark_posted, "POSTED", posted)

    assert mark_posted.record_posted_fact("風は気圧差で生まれる") is False
