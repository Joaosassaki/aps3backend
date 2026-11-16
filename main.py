from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from controller import (
    evento_controller,
    inscricao_controller,
    participante_controller,
    relatorio_controller,
)
from database import criar_tabelas
from service.excecoes import ErroNegocio, ErroPersistencia


@asynccontextmanager
async def lifespan(_app: FastAPI):
    criar_tabelas()
    yield


app = FastAPI(
    title="API de Eventos Acadêmicos",
    description="APS 3 - Persistência e consolidação de dados com SQLite e SQLAlchemy.",
    version="3.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ErroNegocio)
async def tratar_erro_negocio(_request: Request, erro: ErroNegocio):
    return JSONResponse(status_code=erro.status_code, content={"detail": erro.detail})


@app.exception_handler(SQLAlchemyError)
async def tratar_erro_banco(_request: Request, _erro: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"detail": ErroPersistencia().detail})


app.include_router(evento_controller.router)
app.include_router(participante_controller.router)
app.include_router(inscricao_controller.router)
app.include_router(relatorio_controller.router)
