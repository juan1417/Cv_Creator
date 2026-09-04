from .DB import get_engine, validate_database_connection
from sqlmodel import Session, select
from ..models.user import User
from argon2 import PasswordHasher, VerifyMismatchError

DUMMY_HASH="$argon2id$v=19$m=65536,t=3,p=4$Wm9uZQ$Wm9uZQ"  # Dummy hash for timing attack prevention

def validate_seccion(email: str, password: str) -> bool:
    if not validate_database_connection():
        return False
        
    engine = get_engine()
    ph = PasswordHasher()
    
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        # Asignamos el hash real si el usuario existe, o el DUMMY si no
        hash_to_verify = user.hashed_password if user else DUMMY_HASH
        
        try:
            # Siempre se ejecuta esta línea y consume el mismo tiempo de CPU
            is_valid = ph.verify(hash_to_verify, password)
            
            # Retorna True SOLO si la contraseña coincidió Y el usuario realmente existía
            return is_valid and user is not None
        except VerifyMismatchError:
            return False
        except Exception:
            return False
        
def get_user_by_email(email: str) -> User:
    if not validate_database_connection():
        return None
    engine = get_engine()
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        return user

