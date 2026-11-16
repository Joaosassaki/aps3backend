from datetime import date, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Descricao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Local = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Categoria = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class EventoBase(BaseModel):
    titulo: Titulo
    descricao: Descricao = ""
    data: date
    horario: time
    local: Local
    capacidade: int = Field(gt=0)
    categoria: Categoria


class EventoCreate(EventoBase):
    pass


class EventoUpdate(EventoBase):
    pass


class EventoResponse(EventoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
