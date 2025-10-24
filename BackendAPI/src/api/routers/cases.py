from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import TestCase, TestScript

router = APIRouter()


class TestCaseIn(BaseModel):
    test_script_id: int = Field(..., description="Parent script ID")
    name: str = Field(..., description="Case name")
    description: Optional[str] = Field(None, description="Description")
    variables: Optional[dict] = Field(None, description="Variables mapping")


class TestCaseOut(BaseModel):
    id: int
    script_id: int
    name: str
    description: Optional[str]
    variables: Optional[dict]

    class Config:
        from_attributes = True


@router.post("", response_model=dict, status_code=201, summary="Create a new test case")
def create_case(
    payload: TestCaseIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    if not db.query(TestScript).get(payload.test_script_id):
        raise HTTPException(status_code=400, detail="Invalid test_script_id")
    tc = TestCase(
        script_id=payload.test_script_id,
        name=payload.name,
        description=payload.description,
        variables=payload.variables,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return {"success": True, "data": TestCaseOut.model_validate(tc), "error": None}


@router.get("", response_model=dict, summary="List all test cases (with filtering)")
def list_cases(
    test_script_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    q = db.query(TestCase)
    if test_script_id:
        q = q.filter(TestCase.script_id == test_script_id)
    if name:
        q = q.filter(TestCase.name.ilike(f"%{name}%"))
    total = q.count()
    items = q.order_by(TestCase.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [TestCaseOut.model_validate(i) for i in items], "total": total, "page": page, "page_size": page_size}


@router.get("/{case_id}", response_model=TestCaseOut, summary="Retrieve details of a specific test case")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    tc = db.query(TestCase).get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Not found")
    return tc


@router.put("/{case_id}", response_model=dict, summary="Update a test case")
def update_case(
    case_id: int,
    payload: TestCaseIn,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester")),
):
    tc = db.query(TestCase).get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Not found")
    if not db.query(TestScript).get(payload.test_script_id):
        raise HTTPException(status_code=400, detail="Invalid test_script_id")
    tc.script_id = payload.test_script_id
    tc.name = payload.name
    tc.description = payload.description
    tc.variables = payload.variables
    db.commit()
    db.refresh(tc)
    return {"success": True, "data": TestCaseOut.model_validate(tc), "error": None}


@router.delete("/{case_id}", status_code=204, summary="Delete a test case")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin")),
):
    tc = db.query(TestCase).get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(tc)
    db.commit()
    return None
