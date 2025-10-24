from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..minio_client import get_presigned_url
from ..models import RunHistory

router = APIRouter()


@router.get("/{run_id}", summary="Download or preview execution logs")
def get_log_url(
    run_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_roles("admin", "tester", "viewer")),
):
    rh = db.query(RunHistory).get(run_id)
    if not rh:
        raise HTTPException(status_code=404, detail="Not found")
    if not rh.log_path:
        raise HTTPException(status_code=404, detail="Log not available")
    url = get_presigned_url(rh.log_path)
    return {"log_url": url}
