from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse
from datetime import datetime
from pathlib import Path

from database.get_logs import get_logs, get_logs_by_user, get_log_stats
from models.log import LogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])


def _log_to_dict(entry: LogEntry) -> dict:
    return {
        "id": str(entry.id),
        "timestamp": entry.timestamp.isoformat(),
        "level": entry.level,
        "module": entry.module,
        "function": entry.function,
        "message": entry.message,
        "user_id": entry.user_id,
        "extra_data": entry.extra_data,
    }


@router.get("")
async def list_logs(
    level: str = Query(None, description="Filtrar por nivel: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    module: str = Query(None, description="Filtrar por módulo"),
    start_date: datetime = Query(None, description="Fecha inicio (ISO 8601)"),
    end_date: datetime = Query(None, description="Fecha fin (ISO 8601)"),
    limit: int = Query(100, le=1000),
):
    logs = get_logs(level=level, module=module, start_date=start_date, end_date=end_date, limit=limit)
    return {"logs": [_log_to_dict(entry) for entry in logs], "total": len(logs)}


@router.get("/stats")
async def log_stats():
    stats = get_log_stats()
    return stats


@router.get("/files")
async def list_log_files():
    log_dir = Path("client/logs")
    if not log_dir.exists():
        return {"files": []}

    files = sorted(
        [f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log"],
        reverse=True,
    )
    return {"files": files}


@router.get("/files/{filename}")
async def read_log_file(filename: str):
    log_dir = Path("client/logs")
    file_path = log_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo de log no encontrado")

    if not file_path.is_relative_to(log_dir.resolve()):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    content = file_path.read_text(encoding="utf-8")
    return PlainTextResponse(content=content)


@router.get("/{user_id}")
async def user_logs(user_id: str, limit: int = Query(50, le=500)):
    logs = get_logs_by_user(user_id=user_id, limit=limit)
    return {"logs": [_log_to_dict(entry) for entry in logs], "total": len(logs)}
