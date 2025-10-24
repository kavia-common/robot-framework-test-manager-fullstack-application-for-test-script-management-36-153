import io
import logging
import threading
import time
from datetime import datetime

from sqlalchemy.orm import Session

from .database import SessionLocal
from .minio_client import get_minio_client
from .models import ExecutionQueue, RunHistory

logger = logging.getLogger("BackendWorker")

_worker_started = False


def _process_item(db: Session, item: ExecutionQueue):
    """Simulate executing a test case: create RunHistory, write a simple log to Minio, mark done."""
    # Create run history or set running
    run = RunHistory(case_id=item.case_id, status="running", start_time=datetime.utcnow())
    db.add(run)
    db.flush()

    # Simulate work
    time.sleep(0.1)

    # Write a simple log to Minio
    client, bucket = get_minio_client()
    object_name = f"logs/run_{run.id}.txt"
    data = io.BytesIO(f"Run {run.id} for case {item.case_id} finished successfully.\n".encode("utf-8"))
    data.seek(0)
    client.put_object(bucket, object_name, data, length=len(data.getvalue()), content_type="text/plain")

    # Update run history
    run.status = "success"
    run.end_time = datetime.utcnow()
    run.log_path = object_name

    # Remove/mark queue item
    db.delete(item)

    db.commit()
    logger.info("Processed case_id=%s run_id=%s", item.case_id, run.id)


def _worker_loop():
    while True:
        try:
            db = SessionLocal()
            try:
                item = (
                    db.query(ExecutionQueue)
                    .filter(ExecutionQueue.status == "queued")
                    .order_by(ExecutionQueue.priority.asc(), ExecutionQueue.id.asc())
                    .first()
                )
                if not item:
                    time.sleep(0.5)
                else:
                    item.status = "running"
                    db.commit()
                    _process_item(db, item)
            finally:
                db.close()
        except Exception as e:
            logger.error("Worker error: %s", e)
            time.sleep(1)


# PUBLIC_INTERFACE
def start_background_worker():
    """Start a single background worker thread once."""
    global _worker_started
    if _worker_started:
        return
    t = threading.Thread(target=_worker_loop, name="exec-worker", daemon=True)
    t.start()
    _worker_started = True
