"""Unit tests for M2 exception classes — ChartDataError, ExtractError."""

from __future__ import annotations

from aio.exceptions import ChartDataError, ExtractError


def test_chart_data_error_message() -> None:
    exc = ChartDataError("bad input", chart_type="bar")
    assert "bar" in str(exc)
    assert "bad input" in str(exc)
    assert exc.chart_type == "bar"


def test_chart_data_error_no_chart_type() -> None:
    exc = ChartDataError("oops")
    assert exc.chart_type is None
    assert "oops" in str(exc)


def test_extract_error_with_url() -> None:
    exc = ExtractError("network fail", url="https://example.com")
    assert "example.com" in str(exc)
    assert exc.url == "https://example.com"


def test_extract_error_without_url() -> None:
    exc = ExtractError("timeout")
    assert exc.url is None
    assert "timeout" in str(exc)


def test_chart_data_error_is_aio_error() -> None:
    from aio.exceptions import AIOError

    exc = ChartDataError("x")
    assert isinstance(exc, AIOError)


def test_extract_error_is_aio_error() -> None:
    from aio.exceptions import AIOError

    exc = ExtractError("x")
    assert isinstance(exc, AIOError)
