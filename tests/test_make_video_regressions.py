import ast
from pathlib import Path
import subprocess
import unicodedata


def load_functions():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    names = {"has_kanji", "to_tts_text", "normalize_display_text", "add_leading_silence"}
    selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]

    namespace = {
        "__builtins__": __builtins__,
        "LEADING_SILENCE_MS": 180,
        "Path": Path,
        "subprocess": subprocess,
        "unicodedata": unicodedata,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


def test_has_kanji_detects_kanji_correctly():
    funcs = load_functions()

    assert funcs["has_kanji"]("富士山")
    assert funcs["has_kanji"]("風は気圧差で生まれる")
    assert not funcs["has_kanji"]("ふじさん")
    assert not funcs["has_kanji"]("カタカナ")


def test_to_tts_text_converts_only_short_kanji_tokens():
    funcs = load_functions()
    funcs["KAKASI"] = type(
        "KakasiStub",
        (),
        {
            "convert": staticmethod(
                lambda text: [
                    {"orig": "富士山", "hira": "ふじさん"},
                    {"orig": "は", "hira": "は"},
                    {"orig": "日本", "hira": "にほん"},
                    {"orig": "で", "hira": "で"},
                    {"orig": "最も", "hira": "もっとも"},
                    {"orig": "高い", "hira": "たかい"},
                    {"orig": "山", "hira": "やま"},
                    {"orig": "です。", "hira": "です。"},
                ]
            )
        },
    )()

    tts_text = funcs["to_tts_text"]("富士山は日本で最も高い山です。")

    assert tts_text == "富士山はにほんでもっともたかいやまです。"


def test_normalize_display_text_removes_broken_and_control_chars():
    funcs = load_functions()

    text = "雑学\ufffdショート\x00\n今日の\t豆知識"
    normalized = funcs["normalize_display_text"](text)

    assert normalized == "雑学ショート\n今日の豆知識"


def test_add_leading_silence_uses_expected_ffmpeg_filter(monkeypatch, tmp_path):
    funcs = load_functions()
    calls = []

    def fake_run(command, check):
        calls.append((command, check))

    monkeypatch.setattr(funcs["subprocess"], "run", fake_run)
    funcs["FFMPEG"] = "ffmpeg"
    funcs["LEADING_SILENCE_MS"] = 180

    in_wav = tmp_path / "voice.wav"
    out_wav = tmp_path / "voice_padded.wav"
    funcs["add_leading_silence"](in_wav, out_wav)

    assert len(calls) == 1
    command, check = calls[0]
    assert check is True
    assert command == ["ffmpeg", "-y", "-i", str(in_wav), "-af", "adelay=180", "-c:a", "pcm_s16le", str(out_wav)]
