from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import ExecutionQueue, TestCase

router = APIRouter()


class QueueItemOut(BaseModel):
    case_id: int
    status: str
    queued_at: str

    class Config:
        from_attributes = True


class QueueAddIn(BaseModel):
    case_ids: List[int] = Field(..., description="List of case IDs to add to queue")


@router.get("", response_model=List[QueueItemOut], summary="List currently queued test cases")
def list_queue(
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    items = db.query(ExecutionQueue).order_by(ExecutionQueue.priority.asc(), ExecutionQueue.id.asc()).all()
    return [QueueItemOut(case_id=i.case_id, status=i.status, queued_at=i.queued_at.isoformat()) for i in items]


@router.post("", status_code=201, response_model=dict, summary="Add test case(s) to queue")
def add_to_queue(
    payload: QueueAddIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    if not payload.case_ids:
        raise HTTPException(status_code=400, detail="case_ids is required")
    added = []
    for cid in payload.case_ids:
        if not db.query(TestCase).get(cid):
            continue
        q = ExecutionQueue(case_id=cid, status="queued")
        db.add(q)
        added.append(cid)
    db.commit()
    return {"success": True, "data": {"added": added}, "error": None}


@router.delete("/{case_id}", status_code=204, summary="Remove a test case from queue")
def remove_from_queue(
    case_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    item = db.query(ExecutionQueue).filter(ExecutionQueue.case_id == case_id, ExecutionQueue.status == "queued").first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return None
