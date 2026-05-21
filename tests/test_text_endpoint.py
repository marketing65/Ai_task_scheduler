"""
Integration tests for the /process-text endpoint.
Tests the full pipeline from text input to structured task JSON.

NOTE: These tests require a valid OPENAI_API_KEY in .env to run.
      They make actual API calls and are intended as integration tests.
      For CI/CD, mock the OpenAI client.
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


# ── Health Check ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """Health endpoint should return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "openai_key_configured" in data


@pytest.mark.anyio
async def test_root(client: AsyncClient):
    """Root endpoint should serve the frontend UI HTML."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<html" in response.text.lower()


@pytest.mark.anyio
async def test_process_text_empty_body(client: AsyncClient):
    """Empty text should return 422 validation error."""
    response = await client.post("/process-text", json={"text": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_process_text_missing_body(client: AsyncClient):
    """Missing body should return 422."""
    response = await client.post("/process-text", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_process_text_hindi_input(client: AsyncClient):
    """
    Test Hindi/Hinglish input extraction.

    NOTE: This test makes a real OpenAI API call.
    Skip if no API key is configured.
    """
    from app.config import settings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        pytest.skip("OPENAI_API_KEY not configured")

    response = await client.post(
        "/process-text",
        json={
            "text": (
                "Mukesh sir ne bola Rahul ko HR department mein "
                "documents submit karne hain aur last date 25 April hai"
            )
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "tasks" in data
    assert "input_text" in data
    assert "processing_time_ms" in data
    assert len(data["tasks"]) >= 1

    task = data["tasks"][0]
    assert "requester_name" in task
    assert "doer_name" in task
    assert "doer_department" in task
    assert "due_date" in task
    assert "task_description" in task
    assert "attachment" in task

    # Validate extracted values
    assert task["requester_name"] in ["Mukesh", "CEO - Mukesh Sharma"]
    assert task["doer_name"] == "Rahul"
    assert task["doer_department"] == "HR"
    assert task["due_date"] is not None  # Should be a date string


@pytest.mark.anyio
async def test_process_text_simple_hinglish(client: AsyncClient):
    """Test simple Hinglish input."""
    from app.config import settings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        pytest.skip("OPENAI_API_KEY not configured")

    response = await client.post(
        "/process-text",
        json={"text": "Simran ko bolo kal tak production report ready kare"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 1

    task = data["tasks"][0]
    assert task["doer_name"] == "Simran"
    assert task["task_description"]  # Should not be empty


@pytest.mark.anyio
async def test_process_text_english_input(client: AsyncClient):
    """Test pure English input."""
    from app.config import settings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        pytest.skip("OPENAI_API_KEY not configured")

    response = await client.post(
        "/process-text",
        json={
            "text": (
                "John asked Sarah from the Finance department to prepare "
                "the quarterly budget report by next Monday. "
                "The Excel file is attached."
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 1

    task = data["tasks"][0]
    assert task["requester_name"] == "John"
    assert task["doer_name"] == "Sarah"
    assert task["doer_department"] == "Finance"
    assert task["attachment"] is not None  # Should detect attachment


@pytest.mark.anyio
async def test_process_text_multi_task(client: AsyncClient):
    """Test multiple tasks in a single input."""
    from app.config import settings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        pytest.skip("OPENAI_API_KEY not configured")

    response = await client.post(
        "/process-text",
        json={
            "text": (
                "Mukesh sir ne bola Rahul ko HR mein documents submit karne hain "
                "25 April tak. Aur Simran ko bolo production report kal tak ready kare."
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 2  # Should detect 2 tasks


@pytest.mark.anyio
async def test_upload_attachment(client: AsyncClient):
    """Test file upload to /upload-attachment endpoint."""
    files = {"file": ("dummy_sheet.xlsx", b"dummy Excel bytes content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = await client.post("/upload-attachment", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "dummy_sheet.xlsx"
    assert data["url"].startswith("/static/attachments/")


@pytest.mark.anyio
async def test_process_text_with_attachment(client: AsyncClient):
    """Test process-text endpoint with an explicit attachment field."""
    from app.config import settings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-api-key-here":
        pytest.skip("OPENAI_API_KEY not configured")

    response = await client.post(
        "/process-text",
        json={
            "text": "Simran ko bolo kal tak report ready kare",
            "attachment": "/static/attachments/12345_dummy_sheet.xlsx"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 1
    assert data["tasks"][0]["attachment"] == "/static/attachments/12345_dummy_sheet.xlsx"
