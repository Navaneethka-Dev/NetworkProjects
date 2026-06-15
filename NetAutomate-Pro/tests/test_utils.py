"""
Tests for netautomate.utils — utility functions
"""
import os
import tempfile
import pytest
from pathlib import Path

from netautomate.utils import (
    validate_ip,
    format_bytes,
    get_timestamp,
    render_template,
    setup_logging,
)


class TestValidateIp:
    def test_valid_ipv4(self):
        assert validate_ip("192.168.1.1") is True

    def test_valid_broadcast(self):
        assert validate_ip("255.255.255.255") is True

    def test_valid_loopback(self):
        assert validate_ip("127.0.0.1") is True

    def test_invalid_out_of_range(self):
        assert validate_ip("256.0.0.1") is False

    def test_invalid_too_few_octets(self):
        assert validate_ip("192.168.1") is False

    def test_invalid_letters(self):
        assert validate_ip("abc.def.ghi.jkl") is False

    def test_invalid_empty(self):
        assert validate_ip("") is False


class TestFormatBytes:
    def test_bytes(self):
        result = format_bytes(512)
        assert "B" in result

    def test_kilobytes(self):
        result = format_bytes(2048)
        assert "KB" in result

    def test_megabytes(self):
        result = format_bytes(2 * 1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = format_bytes(3 * 1024 ** 3)
        assert "GB" in result


class TestGetTimestamp:
    def test_returns_string(self):
        ts = get_timestamp()
        assert isinstance(ts, str)

    def test_format(self):
        ts = get_timestamp()
        # Basic sanity: contains a dash (date separator)
        assert "-" in ts
        assert ":" in ts


class TestRenderTemplate:
    def test_renders_variable(self, tmp_path):
        template_file = tmp_path / "test.j2"
        template_file.write_text("hostname {{ hostname }}")

        result = render_template(str(template_file), {"hostname": "router1"})
        assert "router1" in result

    def test_renders_conditional(self, tmp_path):
        template_file = tmp_path / "test.j2"
        template_file.write_text(
            "{% if ntp is defined %}ntp server {{ ntp }}{% endif %}"
        )
        result = render_template(str(template_file), {"ntp": "10.0.0.1"})
        assert "10.0.0.1" in result

    def test_renders_loop(self, tmp_path):
        template_file = tmp_path / "test.j2"
        template_file.write_text(
            "{% for item in items %}{{ item }}\n{% endfor %}"
        )
        result = render_template(str(template_file), {"items": ["a", "b", "c"]})
        assert "a" in result and "b" in result and "c" in result

    def test_missing_template_raises(self):
        with pytest.raises(FileNotFoundError):
            render_template("/nonexistent/path/template.j2", {})

    def test_default_filter(self, tmp_path):
        template_file = tmp_path / "test.j2"
        template_file.write_text("{{ value | default('fallback') }}")
        result = render_template(str(template_file), {})
        assert "fallback" in result


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "netautomate"

    def test_no_duplicate_handlers(self):
        logger1 = setup_logging()
        count1 = len(logger1.handlers)
        logger2 = setup_logging()
        count2 = len(logger2.handlers)
        # Handler count should not grow on repeated calls
        assert count1 == count2
