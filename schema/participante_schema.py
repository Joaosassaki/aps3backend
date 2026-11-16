from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator

Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Curso = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ParticipanteBase(BaseModel):
    nome: Nome
    email: EmailStr
    curso: Curso

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower()


class ParticipanteCreate(ParticipanteBase):
    pass


class ParticipanteUpdate(ParticipanteBase):
    pass


class ParticipanteResponse(ParticipanteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
