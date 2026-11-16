from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


class ErroNegocio(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NaoEncontrado(ErroNegocio):
    status_code = 404


class Conflito(ErroNegocio):
    status_code = 409


class ErroPersistencia(ErroNegocio):
    status_code = 500

    def __init__(self):
        super().__init__("Não foi possível concluir a operação. Tente novamente mais tarde.")


def confirmar(db: Session, mensagem_conflito: str | None = None) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if mensagem_conflito:
            raise Conflito(mensagem_conflito)
        raise ErroPersistencia()
    except SQLAlchemyError:
        db.rollback()
        raise ErroPersistencia()
