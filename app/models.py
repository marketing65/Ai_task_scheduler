"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional

class TaskResponse(BaseModel):
    """A single extracted task with all structured fields."""

    created_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the task was processed/created",
        examples=["2026-05-19 16:35:00"],
    )
    requester_name: Optional[str] = Field(
        default=None,
        description="Person who assigned/requested the task",
        examples=["Mukesh"],
    )
    doer_department: Optional[str] = Field(
        default=None,
        description="Department of the person performing the task",
        examples=["HR", "Production", "Finance"],
    )
    doer_name: Optional[str] = Field(
        default=None,
        description="Person who will perform the task",
        examples=["Rahul", "Simran"],
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Due date in YYYY-MM-DD format",
        examples=["2026-04-25"],
    )
    task_description: str = Field(
        description="Task description translated into clear professional English",
        examples=["Submit documents to the HR department"],
    )
    attachment: Optional[str] = Field(
        default=None,
        description="Attachment reference if mentioned, else null",
    )
    requires_confirmation: Optional[bool] = Field(
        default=False,
        description="True if the extracted names had low matching confidence and need manual confirmation",
    )


class ProcessingResult(BaseModel):
    """Complete result of processing a text or audio input."""

    input_text: str = Field(
        description="The original or transcribed input text",
    )
    tasks: list[TaskResponse] = Field(
        description="List of extracted tasks (supports multi-task input)",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Overall confidence score (0.0 - 1.0)",
    )
    processing_time_ms: float = Field(
        description="Total processing time in milliseconds",
    )


# ── Request Models ───────────────────────────────────────────────


class ProcessTextRequest(BaseModel):
    """Request body for the /process-text endpoint."""

    text: str = Field(
        description="Input text in Hindi, Hinglish, or English",
        min_length=1,
        max_length=5000,
        examples=[
            "Mukesh sir ne bola Rahul ko HR department mein documents submit karne hain aur last date 25 April hai"
        ],
    )
    attachment: Optional[str] = Field(
        default=None,
        description="Optional attachment URL or filename to associate with the tasks",
    )


class GoogleSheetsExportRequest(BaseModel):
    """Request schema for Google Sheets export."""

    tasks: list[TaskResponse] = Field(description="List of tasks to export")



# ── Error Models ─────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type")
    detail: str = Field(description="Human-readable error message")
    status_code: int = Field(description="HTTP status code")
