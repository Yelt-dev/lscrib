"""Tests del catálogo de modelos (R5) y la detección de descarga (R2)."""

from lscrib.models import registry
from lscrib.models.registry import (
    CATALOG,
    CATALOG_BY_NAME,
    catalog_with_status,
    is_downloaded,
)


def test_catalog_names_unique_and_indexed():
    names = [m.name for m in CATALOG]
    assert len(names) == len(set(names))
    assert set(CATALOG_BY_NAME) == set(names)


def test_catalog_covers_expected_models():
    assert {"tiny", "base", "small", "medium", "large-v3"} <= set(CATALOG_BY_NAME)


def test_every_model_has_tradeoff_fields():
    """R5: siempre peso, velocidad y calidad para una decisión informada."""
    for m in CATALOG:
        assert m.size_label and m.speed and m.quality


def test_catalog_with_status_mirrors_catalog():
    status = catalog_with_status()
    assert [s.name for s in status] == [m.name for m in CATALOG]
    assert all(isinstance(s.downloaded, bool) for s in status)


def test_is_downloaded_true_when_cache_dir_present(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    snap = hub / "models--Systran--faster-whisper-small" / "snapshots" / "abc123"
    snap.mkdir(parents=True)
    monkeypatch.setenv("HF_HUB_CACHE", str(hub))
    assert is_downloaded("small") is True


def test_is_downloaded_false_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty"))
    assert is_downloaded("large-v3") is False


def test_is_downloaded_false_when_snapshot_empty(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    (hub / "models--Systran--faster-whisper-base" / "snapshots").mkdir(parents=True)
    monkeypatch.setenv("HF_HUB_CACHE", str(hub))
    assert is_downloaded("base") is False


def test_hub_cache_dir_respects_hf_home(tmp_path, monkeypatch):
    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    monkeypatch.delenv("HUGGINGFACE_HUB_CACHE", raising=False)
    monkeypatch.setenv("HF_HOME", str(tmp_path))
    assert registry._hub_cache_dir() == tmp_path / "hub"
