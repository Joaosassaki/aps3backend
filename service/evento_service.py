from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.evento import Evento
from model.inscricao import Inscricao
from schema.evento_schema import EventoCreate, EventoUpdate
from service.excecoes import Conflito, NaoEncontrado, confirmar


def _buscar_ou_404(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise NaoEncontrado("Evento não encontrado.")
    return evento


def criar(db: Session, dados: EventoCreate) -> Evento:
    evento = Evento(**dados.model_dump())
    db.add(evento)
    confirmar(db)
    db.refresh(evento)
    return evento


def listar(db: Session) -> list[Evento]:
    return list(db.scalars(select(Evento).order_by(Evento.id)))


def consultar(db: Session, evento_id: int) -> Evento:
    return _buscar_ou_404(db, evento_id)


def atualizar(db: Session, evento_id: int, dados: EventoUpdate) -> Evento:
    evento = _buscar_ou_404(db, evento_id)

    total_inscritos = db.scalar(
        select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
    )
    if dados.capacidade < total_inscritos:
        raise Conflito("A capacidade não pode ser menor que a quantidade de inscritos no evento.")

    for campo, valor in dados.model_dump().items():
        setattr(evento, campo, valor)
    confirmar(db)
    db.refresh(evento)
    return evento


def excluir(db: Session, evento_id: int) -> None:
    evento = _buscar_ou_404(db, evento_id)
    db.delete(evento)
    confirmar(db)
