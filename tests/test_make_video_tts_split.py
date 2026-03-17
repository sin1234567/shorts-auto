import ast
from pathlib import Path


def load_split_tts_sentences():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    names = {"sanitize_tts_text", "split_tts_sentences"}
    selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in names]

    namespace = {"__builtins__": __builtins__}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace["split_tts_sentences"]


def test_split_tts_sentences_breaks_on_sentence_boundaries():
    split_tts_sentences = load_split_tts_sentences()

    chunks = split_tts_sentences("これは長い説明です。次の文です。最後です。")

    assert chunks == ["これは長い説明です。", "次の文です。", "最後です。"]


def test_split_tts_sentences_breaks_long_clause_at_commas():
    split_tts_sentences = load_split_tts_sentences()

    chunks = split_tts_sentences("これはとても長い説明で、途中で区切って、最後まで読みます。")

    assert len(chunks) >= 2
    assert all(chunk.endswith("、") or chunk.endswith("。") for chunk in chunks)
