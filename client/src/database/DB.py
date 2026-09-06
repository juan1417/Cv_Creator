from sqlmodel import Session, SQLModel, create_engine, select
import os
import dotenv

dotenv.load_dotenv()

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
    return _engine

def create_all_tables():
    engine = get_engine()
    import models.cv
    import models.user
    import models.experience
    import models.skill
    import models.education
    import models.chat
    import models.log
    SQLModel.metadata.create_all(engine)

def validate_database_connection() -> bool:
    engine = get_engine()
    with Session(engine) as session:
        try:
            session.execute(select(1))
            return True
        except Exception as e:
            return False
