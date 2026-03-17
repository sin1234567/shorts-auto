import ast
import re
import unicodedata
from pathlib import Path


def load_functions():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    max_narration_chars = None
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "MAX_NARRATION_CHARS":
                    max_narration_chars = ast.literal_eval(node.value)

    names = {"normalize_narration_line", "split_narration_line"}
    selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]

    namespace = {
        "__builtins__": __builtins__,
        "MAX_NARRATION_CHARS": max_narration_chars,
        "re": re,
        "unicodedata": unicodedata,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


def test_normalize_narration_line_rewrites_banned_forms():
    funcs = load_functions()

    assert funcs["normalize_narration_line"]("そうですね") == "そうですね。意外です。"
    assert funcs["normalize_narration_line"]("うわーーー") == "うわー。"
    assert funcs["normalize_narration_line"]("えっと...") == "えっと。"


def test_split_narration_line_limits_long_text():
    funcs = load_functions()

    chunks = funcs["split_narration_line"]("これはとても長い説明です。でもこのままだと読み上げが伸びやすいです。")

    assert len(chunks) >= 2
    assert all(chunk.endswith(("。", "！", "？")) for chunk in chunks)
    assert all(len(chunk) <= funcs["MAX_NARRATION_CHARS"] + 2 for chunk in chunks)
