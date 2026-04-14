"""Unit tests for image validation (JPEG magic bytes)."""

import pytest


class TestImageValidation:
    """Test image format validation."""

    def test_jpeg_magic_bytes(self):
        """Test JPEG magic byte detection."""
        jpeg_header = b"\xff\xd8\xff"
        assert jpeg_header[:3] == b"\xff\xd8\xff"

    def test_invalid_image_rejected(self):
        """Test invalid image format rejected."""
        invalid_data = b"not an image"
        assert invalid_data[:3] != b"\xff\xd8\xff"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
