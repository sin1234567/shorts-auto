import ast
from pathlib import Path


def load_functions():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    names = {"sanitize_tts_text", "build_narration_text", "to_tts_text", "has_kanji"}
    selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]

    namespace = {"__builtins__": __builtins__}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


def test_display_text_keeps_original_japanese():
    funcs = load_functions()
    funcs["random"] = type(
        "RandomStub",
        (),
        {"choice": staticmethod(lambda seq: seq[0])},
    )()
    funcs["HOOK_PATTERNS"] = ["{title}"]
    funcs["CATEGORY_ANALYSIS"] = {"generic": ["くわしい話です"]}
    funcs["ANALYSIS_LINES"] = ["くわしい話です"]
    funcs["ENDINGS"] = ["おぼえておくと便利です。"]

    narration_text = funcs["build_narration_text"]("風は気圧差で生まれる", "気圧で風が起きる。", "generic")

    assert "風は気圧差で生まれる" in narration_text
    assert "気圧で風が起きる" in narration_text
    assert "かぜはきあつさでうまれる" not in narration_text


def test_tts_text_keeps_long_phrases_natural():
    funcs = load_functions()
    funcs["KAKASI"] = type(
        "KakasiStub",
        (),
        {
            "convert": staticmethod(
                lambda text: [
                    {"orig": "風は気圧差で生まれる", "hira": "かぜはきあつさでうまれる"},
                    {"orig": " ", "hira": " "},
                    {"orig": "気圧で風が起きる。", "hira": "きあつでかぜがおきる。"},
                ]
            )
        },
    )()

    tts_text = funcs["to_tts_text"]("風は気圧差で生まれる 気圧で風が起きる。")

    assert tts_text == "風は気圧差で生まれる 気圧で風が起きる。"


def test_only_tts_input_is_converted_for_audio():
    funcs = load_functions()
    funcs["random"] = type(
        "RandomStub",
        (),
        {"choice": staticmethod(lambda seq: seq[0])},
    )()
    funcs["HOOK_PATTERNS"] = ["{title}"]
    funcs["CATEGORY_ANALYSIS"] = {"generic": ["くわしい話です"]}
    funcs["ANALYSIS_LINES"] = ["くわしい話です"]
    funcs["ENDINGS"] = ["おぼえておくと便利です。"]
    funcs["KAKASI"] = type(
        "KakasiStub",
        (),
        {
            "convert": staticmethod(
                lambda text: [
                    {"orig": "風は気圧差で生まれる", "hira": "かぜはきあつさでうまれる"},
                    {"orig": " ", "hira": " "},
                    {"orig": "気圧で風が起きる。", "hira": "きあつでかぜがおきる。"},
                    {"orig": " ", "hira": " "},
                    {"orig": "くわしい話です。", "hira": "くわしいはなしです。"},
                    {"orig": " ", "hira": " "},
                    {"orig": "おぼえておくと便利です。", "hira": "おぼえておくとべんりです。"},
                ]
            )
        },
    )()

    narration_text = funcs["build_narration_text"]("風は気圧差で生まれる", "気圧で風が起きる。", "generic")
    tts_text = funcs["to_tts_text"](narration_text)

    assert narration_text != tts_text
    assert "風は気圧差で生まれる" in narration_text
    assert "風は気圧差で生まれる" in tts_text
