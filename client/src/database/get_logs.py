from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, func

from .DB import get_engine
from models.log import LogEntry


def get_logs(
    level: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> list[LogEntry]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(LogEntry)

        if level:
            statement = statement.where(LogEntry.level == level.upper())
        if module:
            statement = statement.where(LogEntry.module == module)
        if start_date:
            statement = statement.where(LogEntry.timestamp >= start_date)
        if end_date:
            statement = statement.where(LogEntry.timestamp <= end_date)

        statement = statement.order_by(LogEntry.timestamp.desc()).limit(limit)
        results = list(session.exec(statement).all())
        return results


def get_logs_by_user(user_id: str, limit: int = 50) -> list[LogEntry]:
    engine = get_engine()
    with Session(engine) as session:
        statement = (
            select(LogEntry)
            .where(LogEntry.user_id == user_id)
            .order_by(LogEntry.timestamp.desc())
            .limit(limit)
        )
        results = list(session.exec(statement).all())
        return results


def get_log_stats() -> dict:
    engine = get_engine()
    with Session(engine) as session:
        level_counts = {}
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            count = session.exec(
                select(func.count()).where(LogEntry.level == level)
            ).one()
            level_counts[level] = count

        total = session.exec(select(func.count()).select_from(LogEntry)).one()

        daily_counts = session.exec(
            select(
                func.date(LogEntry.timestamp).label("day"),
                func.count().label("count"),
            )
            .group_by(func.date(LogEntry.timestamp))
            .order_by(func.date(LogEntry.timestamp).desc())
            .limit(30)
        ).all()

        return {
            "total": total,
            "by_level": level_counts,
            "by_day": [{"date": str(row.day), "count": row.count} for row in daily_counts],
        }
