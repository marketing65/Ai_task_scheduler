"""
Core task extraction service.
Uses OpenAI GPT to extract structured tasks from multilingual text input.
"""

import json
import time
from datetime import datetime
from openai import OpenAI
from app.config import settings
from app.models import TaskResponse, ProcessingResult
from app.prompts.extraction import get_system_prompt, get_user_prompt
from app.services.date_handler import validate_date_format
from app.services.normalizer import normalize_name, normalize_department
from app.services import employee_matcher as em
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-initialized OpenAI client
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client (singleton)."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def extract_tasks(input_text: str, attachment_filename: str | None = None) -> ProcessingResult:
    """
    Extract structured tasks from a multilingual text input.

    Pipeline:
        1. Send text to GPT with task extraction prompt
        2. Parse JSON response
        3. Post-process: validate dates, normalize names/departments
        4. Return structured ProcessingResult

    Args:
        input_text: Raw text input in Hindi, Hinglish, or English.
        attachment_filename: Optional name of an uploaded file to attach to tasks.

    Returns:
        ProcessingResult containing extracted tasks and metadata.

    Raises:
        RuntimeError: If GPT API call or JSON parsing fails.
    """
    start_time = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Extracting tasks from input: '{input_text[:100]}...'")

    # ── Step 1: Call GPT ────────────────────────────────────────

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": get_system_prompt(today_str),
                },
                {
                    "role": "user",
                    "content": get_user_prompt(input_text),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=2000,
        )

        raw_response = response.choices[0].message.content
        logger.debug(f"GPT raw response: {raw_response}")

    except Exception as e:
        logger.error(f"GPT API call failed: {e}")
        raise RuntimeError(f"AI extraction failed: {e}") from e

    # ── Step 2: Parse JSON ──────────────────────────────────────

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse GPT JSON response: {e}")
        logger.error(f"Raw response was: {raw_response}")
        raise RuntimeError(
            "AI returned an invalid response format. Please try again."
        ) from e

    # ── Step 3: Extract tasks and confidence ────────────────────

    raw_tasks = parsed.get("tasks", [])
    confidence = parsed.get("confidence")

    if not raw_tasks:
        logger.warning("No tasks extracted from input")
        # Return a fallback with the raw text as description
        elapsed_ms = (time.time() - start_time) * 1000
        return ProcessingResult(
            input_text=input_text,
            tasks=[
                TaskResponse(
                    requester_name=None,
                    doer_department=None,
                    doer_name=None,
                    due_date=None,
                    task_description=f"[Could not extract task] Original: {input_text}",
                    attachment=attachment_filename,
                )
            ],
            confidence=0.0,
            processing_time_ms=round(elapsed_ms, 2),
        )

    # ── Step 4: Post-process each task ──────────────────────────

    processed_tasks: list[TaskResponse] = []

    for raw_task in raw_tasks:
        # ── Normalize names from GPT ─────────────────────────────
        req_name = normalize_name(raw_task.get("requester_name"))
        doer_name = normalize_name(raw_task.get("doer_name"))
        gpt_department = normalize_department(raw_task.get("doer_department"))

        # ── Fuzzy match against employee directory ───────────────
        # Requester: match against requesters list
        matched_requester = em.match_requester(req_name)
        final_requester = matched_requester if matched_requester else req_name

        # Doer: match against doers list
        matched_doer = em.match_doer(doer_name)
        
        # Fallback: if no doer name was provided but department is specified, try matching the department as a doer
        if not doer_name and gpt_department:
            matched_doer = em.match_doer(gpt_department)
            
        final_doer = matched_doer["name"] if matched_doer else doer_name
        
        # We don't use department matching from directory anymore as it is removed
        final_department = gpt_department

        # ── Determine if there is matching confusion/ambiguity ────
        confusion = False
        
        # Requester confusion check
        if req_name:
            if not matched_requester:
                confusion = True
            elif em._normalize(req_name) != em._normalize(matched_requester):
                confusion = True
                
        # Doer confusion check
        if doer_name:
            if not matched_doer:
                confusion = True
            elif em._normalize(doer_name) != em._normalize(matched_doer["name"]):
                confusion = True

        task = TaskResponse(
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            requester_name=final_requester,
            doer_name=final_doer,
            doer_department=final_department,
            due_date=validate_date_format(raw_task.get("due_date")),
            task_description=raw_task.get("task_description", "").strip(),
            attachment=attachment_filename or raw_task.get("attachment"),
            requires_confirmation=confusion,
        )

        # Ensure task_description is not empty
        if not task.task_description:
            task.task_description = "[Task description could not be extracted]"

        processed_tasks.append(task)

        logger.info(
            f"Extracted task: doer={task.doer_name}, "
            f"dept={task.doer_department}, due={task.due_date}"
        )

    # ── Step 5: Build result ────────────────────────────────────

    elapsed_ms = (time.time() - start_time) * 1000

    result = ProcessingResult(
        input_text=input_text,
        tasks=processed_tasks,
        confidence=confidence,
        processing_time_ms=round(elapsed_ms, 2),
    )

    logger.info(
        f"Extraction complete: {len(processed_tasks)} task(s), "
        f"confidence={confidence}, time={elapsed_ms:.0f}ms"
    )

    return result
