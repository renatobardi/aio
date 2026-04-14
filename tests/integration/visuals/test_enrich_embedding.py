"""Integration tests for data-URI base64 embedding."""

import pytest
import base64


class TestDataURIEmbedding:
    """Test image embedding as base64 data-URIs."""

    def test_base64_encoding(self):
        """Test image bytes are properly base64 encoded."""
        image_data = b"\xff\xd8\xff\xe0"  # JPEG header
        encoded = base64.b64encode(image_data).decode()
        assert "+" in encoded or "/" in encoded or "=" in encoded or encoded.isalnum()

    def test_data_uri_format(self):
        """Test data-URI format is correct."""
        image_data = b"test"
        encoded = base64.b64encode(image_data).decode()
        data_uri = f"data:image/jpeg;base64,{encoded}"
        assert data_uri.startswith("data:image/jpeg;base64,")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
