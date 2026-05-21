"""
Unit tests for the Google Sheets export API endpoint (/sheets/export).
Mocks gspread to prevent real external API calls during testing.
"""

import pytest
from unittest.mock import patch, MagicMock
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
@patch("app.services.sheets.upload_attachment_to_drive")
@patch("gspread.service_account_from_dict")
@patch("gspread.service_account")
async def test_sheets_export_success(mock_service_account, mock_service_account_from_dict, mock_upload_drive, client: AsyncClient):
    """
    Test successful export of multiple tasks to Google Sheets.
    Verifies that rows are properly structured and append_rows is called.
    """
    # Setup mocks
    mock_gc = MagicMock()
    mock_sh = MagicMock()
    mock_worksheet = MagicMock()
    
    mock_service_account.return_value = mock_gc
    mock_service_account_from_dict.return_value = mock_gc
    mock_gc.open_by_key.return_value = mock_sh
    mock_sh.get_worksheet.return_value = mock_worksheet
    mock_worksheet.row_values.return_value = ["Timestamp ", "Requester ", "Task ", "Doer ", "Due date"]
    mock_upload_drive.return_value = "https://drive.google.com/file/d/mocked_file_id/view"

    # Payload matching the schema
    payload = {
        "tasks": [
            {
                "created_at": "2026-05-21 12:00:00",
                "requester_name": "Mukesh",
                "doer_name": "Rahul",
                "doer_department": "HR",
                "due_date": "2026-04-25",
                "task_description": "Submit documents to HR department",
                "attachment": "/static/attachments/123_docs.pdf",
                "requires_confirmation": False
            },
            {
                "created_at": None,  # Test fallback current time
                "requester_name": None,
                "doer_name": "Simran",
                "doer_department": "Production",
                "due_date": None,
                "task_description": "Prepare production report",
                "attachment": None,
                "requires_confirmation": True
            }
        ]
    }

    # Call endpoint
    response = await client.post("/sheets/export", json=payload)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["exported_count"] == 2

    # Verify Mock interactions
    assert mock_service_account.called or mock_service_account_from_dict.called
    mock_gc.open_by_key.assert_called_once_with("1qNj25TWKLScZUoh9GsQRBUAZEYPWW3toI8xL8KdVBOA")
    mock_sh.get_worksheet.assert_called_once_with(0)
    mock_upload_drive.assert_called_once_with("/static/attachments/123_docs.pdf")
    
    # Verify append_rows was called with exactly 2 rows
    called_args, called_kwargs = mock_worksheet.append_rows.call_args
    rows = called_args[0]
    
    assert len(rows) == 2
    # Check 1st row mapping with attachment URL resolved
    assert rows[0] == ["2026-05-21 12:00:00", "Mukesh", "Submit documents to HR department", "Rahul", "2026-04-25", "https://drive.google.com/file/d/mocked_file_id/view"]
    # Check 2nd row mapping with None mappings (attachment should be "Null")
    assert rows[1][1] == ""  # Requester is empty string
    assert rows[1][2] == "Prepare production report"
    assert rows[1][3] == "Simran"
    assert rows[1][4] == ""  # Due date is empty string
    assert rows[1][5] == "Null"  # Attachment is "Null" string
    assert len(rows[1][0]) > 0  # Timestamp generated automatically


@pytest.mark.anyio
async def test_sheets_export_empty_tasks(client: AsyncClient):
    """
    Exporting empty list of tasks should return a 400 bad request error.
    """
    response = await client.post("/sheets/export", json={"tasks": []})
    assert response.status_code == 400
    data = response.json()
    assert "Task list cannot be empty" in data["detail"]


@pytest.mark.anyio
@patch("gspread.service_account_from_dict")
@patch("gspread.service_account")
async def test_sheets_export_api_error(mock_service_account, mock_service_account_from_dict, client: AsyncClient):
    """
    If the Sheets API returns an error, the endpoint should return 500.
    """
    # Mocking authentication or API failure
    mock_service_account.side_effect = Exception("Authentication failed - Invalid Credentials")
    mock_service_account_from_dict.side_effect = Exception("Authentication failed - Invalid Credentials")

    payload = {
        "tasks": [
            {
                "task_description": "Test failure task"
            }
        ]
    }

    response = await client.post("/sheets/export", json=payload)
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Authentication failed" in data["detail"]

