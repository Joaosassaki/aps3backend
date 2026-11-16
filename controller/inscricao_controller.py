from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schema.inscricao_schema import InscricaoResponse, InscritoResponse
from service import inscricao_service

router = APIRouter(prefix="/eventos", tags=["Inscrições"])


@router.post(
    "/{evento_id}/inscricoes/{participante_id}",
    response_model=InscricaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def inscrever_participante(evento_id: int, participante_id: int, db: Session = Depends(get_db)):
    return inscricao_service.inscrever(db, evento_id, participante_id)


@router.get("/{evento_id}/inscricoes", response_model=list[InscritoResponse])
def listar_inscritos(evento_id: int, db: Session = Depends(get_db)):
    return inscricao_service.listar_inscritos(db, evento_id)
