"""
Employee management API router.
Provides CRUD endpoints for requesters and doers lists.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import employee_matcher as em

router = APIRouter(prefix="/employees", tags=["Employees"])


# ── Request schemas ───────────────────────────────────────────────

class RequesterCreate(BaseModel):
    name: str


class RequesterUpdate(BaseModel):
    new_name: str


class DoerCreate(BaseModel):
    name: str


class DoerUpdate(BaseModel):
    new_name: str


# ── Requesters endpoints ──────────────────────────────────────────

@router.get("/requesters", summary="List all requesters")
async def list_requesters():
    return {"requesters": em.load_requesters()}


@router.post("/requesters", summary="Add a requester")
async def add_requester(body: RequesterCreate):
    try:
        entry = em.add_requester(body.name)
        return {"message": "Requester added", "requester": entry}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/requesters/{name}", summary="Edit a requester name")
async def update_requester(name: str, body: RequesterUpdate):
    try:
        entry = em.update_requester(name, body.new_name)
        return {"message": "Requester updated", "requester": entry}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/requesters/{name}", summary="Delete a requester")
async def delete_requester(name: str):
    deleted = em.delete_requester(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Requester '{name}' not found.")
    return {"message": f"Requester '{name}' deleted."}


# ── Doers endpoints ───────────────────────────────────────────────

@router.get("/doers", summary="List all doers")
async def list_doers():
    return {"doers": em.load_doers()}


@router.post("/doers", summary="Add a doer")
async def add_doer(body: DoerCreate):
    try:
        entry = em.add_doer(body.name)
        return {"message": "Doer added", "doer": entry}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/doers/{name}", summary="Edit a doer name")
async def update_doer(name: str, body: DoerUpdate):
    try:
        entry = em.update_doer(name, body.new_name)
        return {"message": "Doer updated", "doer": entry}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/doers/{name}", summary="Delete a doer")
async def delete_doer(name: str):
    deleted = em.delete_doer(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Doer '{name}' not found.")
    return {"message": f"Doer '{name}' deleted."}
