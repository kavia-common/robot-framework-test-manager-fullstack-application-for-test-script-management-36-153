from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import ExecutionQueue, RunHistory, TestCase

router = APIRouter()


class ExecuteIn(BaseModel):
    case_ids: List[int] = Field(..., description="Case IDs to execute")
    run_type: str = Field(..., description="ad_hoc or queued")


@router.post("", response_model=dict, status_code=202, summary="Execute one or more test cases (ad hoc or queued)")
def execute_cases(
    payload: ExecuteIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    if payload.run_type not in ("ad_hoc", "queued"):
        raise HTTPException(status_code=400, detail="Invalid run_type")

    if payload.run_type == "queued":
        # Just add to queue
        added = []
        for cid in payload.case_ids:
            if not db.query(TestCase).get(cid):
                continue
            q = ExecutionQueue(case_id=cid, status="queued")
            db.add(q)
            added.append(cid)
        db.commit()
        return {"success": True, "data": {"queued": added}, "error": None}

    # ad_hoc: create run history records immediately; worker will pick them up or simulated success
    runs = []
    for cid in payload.case_ids:
        if not db.query(TestCase).get(cid):
            continue
        run = RunHistory(case_id=cid, status="running")
        db.add(run)
        db.flush()
        runs.append(run.id)
    db.commit()
    return {"success": True, "data": {"runs": runs}, "error": None}
