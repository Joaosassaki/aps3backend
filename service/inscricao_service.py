from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from model.evento import Evento
from model.inscricao import Inscricao
from model.participante import Participante
from service.excecoes import Conflito, NaoEncontrado, confirmar

MENSAGEM_JA_INSCRITO = "Participante já está inscrito neste evento."
MENSAGEM_SEM_VAGAS = "Não existem vagas disponíveis para este evento."


def _buscar_evento_ou_404(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise NaoEncontrado("Evento não encontrado.")
    return evento


def inscrever(db: Session, evento_id: int, participante_id: int) -> Inscricao:
    evento = _buscar_evento_ou_404(db, evento_id)

    if db.get(Participante, participante_id) is None:
        raise NaoEncontrado("Participante não encontrado.")

    ja_inscrito = db.scalar(
        select(Inscricao.id).where(
            Inscricao.evento_id == evento_id,
            Inscricao.participante_id == participante_id,
        )
    )
    if ja_inscrito is not None:
        raise Conflito(MENSAGEM_JA_INSCRITO)

    total_inscritos = db.scalar(
        select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
    )
    if total_inscritos >= evento.capacidade:
        raise Conflito(MENSAGEM_SEM_VAGAS)

    inscricao = Inscricao(evento_id=evento_id, participante_id=participante_id)
    db.add(inscricao)
    confirmar(db, MENSAGEM_JA_INSCRITO)
    db.refresh(inscricao)
    return inscricao


def listar_inscritos(db: Session, evento_id: int) -> list[Inscricao]:
    _buscar_evento_ou_404(db, evento_id)
    consulta = (
        select(Inscricao)
        .options(joinedload(Inscricao.participante))
        .where(Inscricao.evento_id == evento_id)
        .order_by(Inscricao.id)
    )
    return list(db.scalars(consulta))
