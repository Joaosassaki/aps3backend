from datetime import date

from pydantic import BaseModel, ConfigDict

from schema.participante_schema import ParticipanteResponse


class InscricaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evento_id: int
    participante_id: int
    data_inscricao: date


class InscritoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_inscricao: date
    participante: ParticipanteResponse
