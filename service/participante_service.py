from sqlalchemy import select
from sqlalchemy.orm import Session

from model.participante import Participante
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate
from service.excecoes import Conflito, NaoEncontrado, confirmar

MENSAGEM_EMAIL_DUPLICADO = "Já existe um participante cadastrado com este e-mail."


def _buscar_ou_404(db: Session, participante_id: int) -> Participante:
    participante = db.get(Participante, participante_id)
    if participante is None:
        raise NaoEncontrado("Participante não encontrado.")
    return participante


def _email_em_uso(db: Session, email: str, ignorar_id: int | None = None) -> bool:
    consulta = select(Participante.id).where(Participante.email == email)
    if ignorar_id is not None:
        consulta = consulta.where(Participante.id != ignorar_id)
    return db.scalar(consulta) is not None


def criar(db: Session, dados: ParticipanteCreate) -> Participante:
    if _email_em_uso(db, dados.email):
        raise Conflito(MENSAGEM_EMAIL_DUPLICADO)

    participante = Participante(**dados.model_dump())
    db.add(participante)
    confirmar(db, MENSAGEM_EMAIL_DUPLICADO)
    db.refresh(participante)
    return participante


def listar(db: Session) -> list[Participante]:
    return list(db.scalars(select(Participante).order_by(Participante.id)))


def consultar(db: Session, participante_id: int) -> Participante:
    return _buscar_ou_404(db, participante_id)


def atualizar(db: Session, participante_id: int, dados: ParticipanteUpdate) -> Participante:
    participante = _buscar_ou_404(db, participante_id)

    if _email_em_uso(db, dados.email, ignorar_id=participante_id):
        raise Conflito(MENSAGEM_EMAIL_DUPLICADO)

    for campo, valor in dados.model_dump().items():
        setattr(participante, campo, valor)
    confirmar(db, MENSAGEM_EMAIL_DUPLICADO)
    db.refresh(participante)
    return participante


def excluir(db: Session, participante_id: int) -> None:
    participante = _buscar_ou_404(db, participante_id)
    db.delete(participante)
    confirmar(db)
