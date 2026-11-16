from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from model.inscricao import Inscricao


class Participante(Base):
    __tablename__ = "participantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    curso: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    inscricoes: Mapped[list["Inscricao"]] = relationship(
        back_populates="participante",
        cascade="all, delete-orphan",
    )
