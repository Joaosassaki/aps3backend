from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.evento import Evento
from model.inscricao import Inscricao
from model.participante import Participante


def ocupacao_eventos(db: Session) -> list[dict]:
    consulta = (
        select(
            Evento.id,
            Evento.titulo,
            Evento.capacidade,
            func.count(Inscricao.id).label("total_inscritos"),
        )
        .outerjoin(Inscricao, Inscricao.evento_id == Evento.id)
        .group_by(Evento.id, Evento.titulo, Evento.capacidade)
        .order_by(Evento.id)
    )

    resultado = []
    for evento_id, titulo, capacidade, total_inscritos in db.execute(consulta):
        percentual = round(total_inscritos * 100 / capacidade, 2) if capacidade > 0 else 0.0
        resultado.append(
            {
                "evento_id": evento_id,
                "titulo": titulo,
                "capacidade": capacidade,
                "total_inscritos": total_inscritos,
                "vagas_disponiveis": max(capacidade - total_inscritos, 0),
                "percentual_ocupacao": percentual,
            }
        )
    return resultado


def eventos_por_categoria(db: Session) -> list[dict]:
    inscricoes_por_evento = (
        select(
            Inscricao.evento_id.label("evento_id"),
            func.count(Inscricao.id).label("total"),
        )
        .group_by(Inscricao.evento_id)
        .subquery()
    )

    consulta = (
        select(
            Evento.categoria,
            func.count(Evento.id),
            func.coalesce(func.sum(Evento.capacidade), 0),
            func.coalesce(func.sum(inscricoes_por_evento.c.total), 0),
        )
        .outerjoin(inscricoes_por_evento, inscricoes_por_evento.c.evento_id == Evento.id)
        .group_by(Evento.categoria)
        .order_by(Evento.categoria)
    )

    return [
        {
            "categoria": categoria,
            "total_eventos": total_eventos,
            "capacidade_total": int(capacidade_total),
            "total_inscricoes": int(total_inscricoes),
        }
        for categoria, total_eventos, capacidade_total, total_inscricoes in db.execute(consulta)
    ]


def participacao_por_curso(db: Session) -> list[dict]:
    consulta = (
        select(
            Participante.curso,
            func.count(func.distinct(Participante.id)),
            func.count(Inscricao.id),
        )
        .outerjoin(Inscricao, Inscricao.participante_id == Participante.id)
        .group_by(Participante.curso)
        .order_by(Participante.curso)
    )

    return [
        {
            "curso": curso,
            "total_participantes": total_participantes,
            "total_inscricoes": total_inscricoes,
        }
        for curso, total_participantes, total_inscricoes in db.execute(consulta)
    ]
