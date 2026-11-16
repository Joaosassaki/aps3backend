import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

ARQUIVO_BANCO = os.path.join(tempfile.mkdtemp(), "teste.db")
os.environ["DATABASE_URL"] = f"sqlite:///{ARQUIVO_BANCO}"

import pytest
from fastapi.testclient import TestClient

from database import Base, criar_tabelas, engine
from main import app


@pytest.fixture
def client():
    criar_tabelas()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


@pytest.fixture
def evento_payload():
    return {
        "titulo": "Workshop de Python",
        "descricao": "Introdução prática a Python",
        "data": "2026-12-10",
        "horario": "14:00",
        "local": "Laboratório 3",
        "capacidade": 2,
        "categoria": "Workshop",
    }


@pytest.fixture
def criar_evento(client, evento_payload):
    def _criar(**alteracoes):
        resposta = client.post("/eventos", json={**evento_payload, **alteracoes})
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def criar_participante(client):
    contador = {"n": 0}

    def _criar(curso="Engenharia de Software", **alteracoes):
        contador["n"] += 1
        n = contador["n"]
        dados = {"nome": f"Aluno {n}", "email": f"aluno{n}@email.com", "curso": curso}
        dados.update(alteracoes)
        resposta = client.post("/participantes", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar
