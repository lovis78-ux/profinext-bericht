import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Report
from config import ORIGINALS_DIR, OPTIMIZED_DIR
from processor.pipeline import process_report
from processor.extractor import extract_project_data, ProjectData

router = APIRouter(prefix="/api", tags=["upload"])


# ── Schema for the confirmed/edited project data ─────────────────────────────

class PreviewResponse(BaseModel):
    file_id: str
    original_filename: str
    project_name: str
    date: str
    plz: str
    city: str
    street: str
    kwp: str


class ConfirmRequest(BaseModel):
    file_id: str
    original_filename: str
    project_name: str
    date: str
    plz: str
    city: str
    street: str
    kwp: str


# ── Step 1: upload + extract (no processing yet) ─────────────────────────────

@router.post("/upload/preview", response_model=PreviewResponse)
async def upload_preview(file: UploadFile = File(...)):
    """
    Save the uploaded PDF and return the auto-extracted project data for
    the user to review and correct before processing starts.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien erlaubt.")

    uid = uuid.uuid4().hex[:12]
    orig_filename = f"{uid}_original_{file.filename}"
    orig_path = ORIGINALS_DIR / orig_filename

    with open(orig_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        data = extract_project_data(str(orig_path))
    except Exception as e:
        orig_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Daten konnten nicht gelesen werden: {e}")

    return PreviewResponse(
        file_id=uid,
        original_filename=file.filename,
        project_name=data.project_name,
        date=data.date,
        plz=data.plz,
        city=data.city,
        street=data.street,
        kwp=data.kwp,
    )


# ── Step 2: confirm (user-verified data) + start processing ──────────────────

@router.post("/upload/confirm")
async def upload_confirm(
    req: ConfirmRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept the confirmed (and possibly corrected) project data, create a DB
    record and start the PDF pipeline in the background.
    """
    orig_path = ORIGINALS_DIR / f"{req.file_id}_original_{req.original_filename}"
    if not orig_path.exists():
        raise HTTPException(status_code=404, detail="Temporäre Datei nicht mehr vorhanden.")

    opt_filename = f"{req.file_id}_optimized_{req.original_filename}"
    opt_path = OPTIMIZED_DIR / opt_filename

    # Build confirmed ProjectData from the request
    confirmed = ProjectData(
        project_name=req.project_name,
        date=req.date,
        plz=req.plz,
        city=req.city,
        street=req.street,
        kwp=req.kwp,
    )

    # Create DB record
    report = Report(
        original_filename=req.original_filename,
        status="processing",
        original_path=str(orig_path),
        optimized_path=str(opt_path),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    background_tasks.add_task(
        _run_pipeline, report.id, str(orig_path), str(opt_path), confirmed
    )

    return {"id": report.id, "status": "processing"}


# ── Legacy single-step upload (kept for API compatibility) ───────────────────

@router.post("/upload")
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien erlaubt.")

    uid = uuid.uuid4().hex[:12]
    orig_filename = f"{uid}_original_{file.filename}"
    orig_path = ORIGINALS_DIR / orig_filename

    with open(orig_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    opt_filename = f"{uid}_optimized_{file.filename}"
    opt_path = OPTIMIZED_DIR / opt_filename

    report = Report(
        original_filename=file.filename,
        status="processing",
        original_path=str(orig_path),
        optimized_path=str(opt_path),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    background_tasks.add_task(_run_pipeline, report.id, str(orig_path), str(opt_path), None)

    return {"id": report.id, "status": "processing"}


# ── Shared background task ────────────────────────────────────────────────────

async def _run_pipeline(
    report_id: int,
    orig_path: str,
    opt_path: str,
    override_data: ProjectData | None,
):
    """Background task: run PDF pipeline and update DB record."""
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return

        try:
            data = process_report(orig_path, opt_path, override_data)
            report.status = "done"
            report.project_name = data.project_name
            report.address = data.address_full
            report.kwp = data.kwp
            report.report_date = data.date
        except Exception as e:
            report.status = "error"
            report.error_message = str(e)[:900]

        await db.commit()
