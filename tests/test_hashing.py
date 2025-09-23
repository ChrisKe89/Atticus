from pathlib import Path


def test_sha256_text_and_file(tmp_path: Path):
    from atticus.utils.hashing import sha256_text, sha256_file

    text = "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert sha256_text(text) == expected

    f = tmp_path / "sample.txt"
    f.write_text(text, encoding="utf-8")
    assert sha256_file(f) == expected
