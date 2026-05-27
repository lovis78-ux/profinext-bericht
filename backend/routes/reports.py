from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models import Report

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).order_by(Report.created_at.desc()))
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "original_filename": r.original_filename,
            "project_name": r.project_name,
            "address": r.address,
            "kwp": r.kwp,
            "report_date": r.report_date,
            "status": r.status,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await _get_or_404(db, report_id)
    return {"id": report.id, "status": report.status, "error_message": report.error_message}


@router.get("/reports/{report_id}/download/original")
async def download_original(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await _get_or_404(db, report_id)
    path = Path(report.original_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=report.original_filename,
    )


@router.get("/reports/{report_id}/download/optimized")
async def download_optimized(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await _get_or_404(db, report_id)
    if report.status != "done":
        raise HTTPException(status_code=400, detail="Verarbeitung noch nicht abgeschlossen.")
    path = Path(report.optimized_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Optimierte Datei nicht gefunden.")
    opt_name = f"Optimiert_{report.original_filename}"
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=opt_name,
    )


@router.get("/reports/{report_id}/view/optimized")
async def view_optimized(report_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the optimised PDF inline (for browser preview / iframe)."""
    report = await _get_or_404(db, report_id)
    if report.status != "done":
        raise HTTPException(status_code=400, detail="Verarbeitung noch nicht abgeschlossen.")
    path = Path(report.optimized_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Optimierte Datei nicht gefunden.")
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )


@router.delete("/reports/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await _get_or_404(db, report_id)

    # Delete files
    for file_path in (report.original_path, report.optimized_path):
        p = Path(file_path)
        if p.exists():
            p.unlink()

    await db.execute(delete(Report).where(Report.id == report_id))
    await db.commit()
    return {"message": "Vorgang gelöscht."}


async def _get_or_404(db: AsyncSession, report_id: int) -> Report:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Vorgang nicht gefunden.")
    return report
