from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import TestScript

router = APIRouter()


class TestScriptIn(BaseModel):
    name: str = Field(..., description="Test script name")
    description: Optional[str] = Field(None, description="Description")
    metadata: Optional[dict] = Field(None, description="Arbitrary metadata")


class TestScriptOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


@router.post("", response_model=dict, status_code=201, summary="Create a new test script")
def create_test_script(
    payload: TestScriptIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    if db.query(TestScript).filter(TestScript.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Test script with this name already exists")
    ts = TestScript(name=payload.name, description=payload.description, metadata=payload.metadata)
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return {"success": True, "data": TestScriptOut.model_validate(ts), "error": None}


@router.get("", response_model=dict, summary="List all test scripts")
def list_test_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    q = db.query(TestScript)
    total = q.count()
    items = q.order_by(TestScript.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [TestScriptOut.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}


@router.get("/{test_id}", response_model=TestScriptOut, summary="Retrieve details of a specific test script")
def get_test_script(
    test_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    ts = db.query(TestScript).get(test_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Not found")
    return ts


@router.put("/{test_id}", response_model=dict, summary="Update a test script")
def update_test_script(
    test_id: int,
    payload: TestScriptIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    ts = db.query(TestScript).get(test_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Not found")
    ts.name = payload.name
    ts.description = payload.description
    ts.metadata = payload.metadata
    db.commit()
    db.refresh(ts)
    return {"success": True, "data": TestScriptOut.model_validate(ts), "error": None}


@router.delete("/{test_id}", status_code=204, summary="Delete a test script")
def delete_test_script(
    test_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin")),
):
    ts = db.query(TestScript).get(test_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ts)
    db.commit()
    return None
