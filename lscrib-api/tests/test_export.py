"""Tests de los exports: renderizado determinista. No corren Whisper."""

from dataclasses import dataclass

import pytest

from lscrib.export import FORMATS, render
from lscrib.export.formats import _clock, to_md, to_srt, to_txt, to_vtt


@dataclass
class Seg:
    """Doble de db.models.Segment: solo lo que el render necesita (SegmentLike)."""

    index: int
    start_ms: int
    end_ms: int
    text: str


@pytest.fixture
def segments() -> list[Seg]:
    return [
        Seg(0, 0, 1500, "Hola mundo"),
        Seg(1, 1500, 3200, "  segunda línea  "),  # con espacios: deben recortarse
    ]


def test_clock_srt_uses_comma():
    assert _clock(3_661_500, ",") == "01:01:01,500"


def test_clock_vtt_uses_dot():
    assert _clock(3_661_500, ".") == "01:01:01.500"


def test_clock_zero_and_negative_clamped():
    assert _clock(0, ",") == "00:00:00,000"
    assert _clock(-5, ",") == "00:00:00,000"


def test_srt_structure(segments):
    out = to_srt(segments)
    assert out.startswith("1\n00:00:00,000 --> 00:00:01,500\nHola mundo")
    assert "2\n00:00:01,500 --> 00:00:03,200\nsegunda línea" in out


def test_vtt_has_header(segments):
    out = to_vtt(segments)
    assert out.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.500" in out


def test_txt_is_plain_lines_trimmed(segments):
    assert to_txt(segments) == "Hola mundo\nsegunda línea\n"


def test_md_has_heading_and_stamps(segments):
    out = to_md(segments)
    assert out.startswith("# Transcript")
    assert "**[00:00:00]** Hola mundo" in out
    assert "**[00:00:01]** segunda línea" in out


@pytest.mark.parametrize("fmt", list(FORMATS))
def test_render_is_deterministic(fmt, segments):
    """Mismo transcript → mismo archivo, siempre."""
    first, ext, media = render(fmt, segments)
    second, _, _ = render(fmt, segments)
    assert first == second
    assert ext == fmt or (fmt, ext) in {("srt", "srt")}
    assert media


def test_render_unknown_format_raises(segments):
    with pytest.raises(KeyError):
        render("pdf", segments)


def test_empty_transcript_does_not_crash():
    assert to_srt([]) == ""
    assert to_vtt([]).startswith("WEBVTT")
    assert to_txt([]) == "\n"
    assert to_md([]).startswith("# Transcript")
