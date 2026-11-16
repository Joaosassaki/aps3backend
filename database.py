import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'eventos.db')}",
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def ativar_chaves_estrangeiras(conexao, _registro):
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    from model import evento, inscricao, participante  # noqa: F401

    Base.metadata.create_all(bind=engine)
