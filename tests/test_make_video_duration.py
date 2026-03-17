import ast
from pathlib import Path


def load_calculate_video_duration():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    trailing_buffer_sec = None

    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TRAILING_BUFFER_SEC":
                    trailing_buffer_sec = ast.literal_eval(node.value)

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "calculate_video_duration":
            extracted = ast.Module(body=[node], type_ignores=[])
            namespace = {"TRAILING_BUFFER_SEC": trailing_buffer_sec}
            exec(compile(extracted, str(source_path), "exec"), namespace)
            return namespace["calculate_video_duration"]

    raise AssertionError("calculate_video_duration not found")


def test_video_duration_tracks_audio_with_short_buffer():
    calculate_video_duration = load_calculate_video_duration()

    assert calculate_video_duration(8.5) == 8.85
    assert calculate_video_duration(0.0) == 0.35


def test_video_duration_caps_at_35_seconds():
    calculate_video_duration = load_calculate_video_duration()

    assert calculate_video_duration(34.0) == 34.35
    assert calculate_video_duration(40.0) == 35.0
