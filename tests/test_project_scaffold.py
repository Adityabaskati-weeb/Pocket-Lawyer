from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_docs_exist() -> None:
    assert (ROOT / "README.md").exists()
    assert (ROOT / "docs" / "PRD.md").exists()
    assert (ROOT / "docs" / "ROADMAP.md").exists()


def test_package_metadata_exists() -> None:
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.exists()
    assert "pocket-lawyer" in pyproject.read_text(encoding="utf-8")
