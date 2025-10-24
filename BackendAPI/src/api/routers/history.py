from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import RunHistory

router = APIRouter()


class RunHistoryOut(BaseModel):
    id: int
    case_id: Optional[int]
    status: str
    start_time: str
    end_time: Optional[str]
    log_path: Optional[str]

    class Config:
        from_attributes = True


@router.get("", summary="List run history (with filtering and pagination)", response_model=dict)
def list_history(
    case_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    q = db.query(RunHistory)
    if case_id:
        q = q.filter(RunHistory.case_id == case_id)
    if status_filter:
        q = q.filter(RunHistory.status == status_filter)
    total = q.count()
    items = q.order_by(RunHistory.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [RunHistoryOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{run_id}", response_model=RunHistoryOut, summary="Retrieve details and logs for a specific run")
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    rh = db.query(RunHistory).get(run_id)
    if not rh:
        raise HTTPException(status_code=404, detail="Not found")
    return rh
