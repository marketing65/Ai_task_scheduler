"""
Integration tests for the /process-audio endpoint.
Tests audio upload validation and pipeline.

NOTE: Actual transcription tests require a valid OPENAI_API_KEY
      and real audio files. These tests focus on validation logic.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_process_audio_no_file(client: AsyncClient):
    """Request without audio file should return 422."""
    response = await client.post("/process-audio")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_process_audio_unsupported_format(client: AsyncClient):
    """Unsupported audio format should return 400."""
    response = await client.post(
        "/process-audio",
        files={"audio": ("test.txt", b"not audio data", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


@pytest.mark.anyio
async def test_process_audio_empty_file(client: AsyncClient):
    """Empty audio file should return 400."""
    response = await client.post(
        "/process-audio",
        files={"audio": ("test.mp3", b"", "audio/mpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
