"""Chequeo de CPU: sin SSE4.2 el motor muere con SIGILL, así que hay que avisar.

Los flags se parsean de un /proc/cpuinfo falso: los tests corren igual en
cualquier máquina (y en el CI, que sí tiene SSE4.2).
"""

import pytest

from lscrib.system import cpu
from lscrib.system.cpu import CpuSupport, UnsupportedCpu, ensure_cpu_supported

# Un AMD Athlon II X3 (K10, 2010): SSE4a pero ni SSE4.1 ni SSE4.2 ni AVX.
K10 = """\
processor\t: 0
model name\t: AMD Athlon(tm) II X3 455 Processor
flags\t\t: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr sse sse2 sse4a
"""

MODERN = """\
processor\t: 0
model name\t: Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz
flags\t\t: fpu vme de pse tsc msr sse sse2 ssse3 sse4_1 sse4_2 popcnt avx avx2
"""


@pytest.fixture(autouse=True)
def _clear_cache():
    """`check_cpu` cachea el veredicto: limpiar entre tests."""
    cpu.check_cpu.cache_clear()
    yield
    cpu.check_cpu.cache_clear()


def _fake_host(monkeypatch, cpuinfo: str | None, machine: str = "x86_64") -> None:
    monkeypatch.delenv("LSCRIB_IGNORE_CPU_CHECK", raising=False)
    monkeypatch.setattr(cpu.platform, "machine", lambda: machine)
    monkeypatch.setattr(cpu, "_read_cpuinfo", lambda: cpuinfo)


def test_parses_flags_and_model():
    flags, model = cpu._parse_cpuinfo(K10)
    assert "sse4a" in flags and "sse4_2" not in flags
    assert model == "AMD Athlon(tm) II X3 455 Processor"


def test_cpu_without_sse42_is_unsupported(monkeypatch):
    _fake_host(monkeypatch, K10)
    support = cpu.check_cpu()
    assert support.supported is False
    assert support.missing == ["sse4_2"]
    assert "Athlon" in support.cpu_model


def test_modern_cpu_is_supported(monkeypatch):
    _fake_host(monkeypatch, MODERN)
    assert cpu.check_cpu().supported is True


def test_non_x86_skips_the_check(monkeypatch):
    """En arm64 (Apple Silicon) no hay baseline que fallar: no se comprueba."""
    _fake_host(monkeypatch, K10, machine="arm64")
    assert cpu.check_cpu().supported is True


def test_unreadable_cpuinfo_assumes_supported(monkeypatch):
    """Ante la duda no se bloquea una máquina que quizá sí sirve."""
    _fake_host(monkeypatch, None)
    assert cpu.check_cpu().supported is True


def test_env_var_overrides_the_check(monkeypatch):
    """Escape hatch: un entorno que enmascare los flags no debe bloquear al usuario."""
    _fake_host(monkeypatch, K10)
    monkeypatch.setenv("LSCRIB_IGNORE_CPU_CHECK", "1")
    assert cpu.check_cpu().supported is True


def test_message_names_the_cpu_and_the_missing_flag():
    msg = CpuSupport(supported=False, cpu_model="AMD Athlon II X3", missing=["sse4_2"]).message()
    assert "AMD Athlon II X3" in msg
    assert "SSE4.2" in msg
    assert CpuSupport(supported=True).message() == ""


def test_ensure_raises_on_unsupported_cpu(monkeypatch):
    _fake_host(monkeypatch, K10)
    with pytest.raises(UnsupportedCpu, match="SSE4.2"):
        ensure_cpu_supported()


def test_ensure_is_silent_on_supported_cpu(monkeypatch):
    _fake_host(monkeypatch, MODERN)
    ensure_cpu_supported()  # no lanza
