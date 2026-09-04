from sqlmodel import Session, create_engine, select
import os
import dotenv

dotenv.load_dotenv()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"), echo=True)

def validate_database_connection() -> bool:
    engine = get_engine()
    with Session(engine) as session:
        try:
            session.execute(select(1))
            return True
        except Exception as e:
            return False
