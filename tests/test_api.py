from fastapi.testclient import TestClient

from main import app


def test_cadastro_e_consulta_de_eventos(client, evento_payload):
    criado = client.post("/eventos", json=evento_payload)
    assert criado.status_code == 201
    evento = criado.json()
    assert evento["id"] == 1
    assert evento["titulo"] == "Workshop de Python"

    assert client.get(f"/eventos/{evento['id']}").json() == evento
    assert client.get("/eventos").json() == [evento]


def test_evento_inexistente_retorna_404(client):
    resposta = client.get("/eventos/999")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Evento não encontrado."}
    assert client.put("/eventos/999", json={}).status_code in (404, 422)
    assert client.delete("/eventos/999").status_code == 404


def test_atualizacao_e_exclusao_de_evento(client, criar_evento, evento_payload):
    evento = criar_evento()
    resposta = client.put(
        f"/eventos/{evento['id']}",
        json={**evento_payload, "titulo": "Workshop Avançado", "capacidade": 10},
    )
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Workshop Avançado"
    assert resposta.json()["capacidade"] == 10

    assert client.delete(f"/eventos/{evento['id']}").status_code == 204
    assert client.get(f"/eventos/{evento['id']}").status_code == 404


def test_validacoes_de_evento(client, evento_payload):
    invalidos = [
        {"titulo": "   "},
        {"capacidade": 0},
        {"capacidade": -5},
        {"data": "2026-13-45"},
        {"horario": "25:99"},
        {"local": ""},
        {"categoria": ""},
    ]
    for alteracao in invalidos:
        resposta = client.post("/eventos", json={**evento_payload, **alteracao})
        assert resposta.status_code == 422, alteracao

    sem_campo = {k: v for k, v in evento_payload.items() if k != "titulo"}
    assert client.post("/eventos", json=sem_campo).status_code == 422


def test_cadastro_consulta_atualizacao_exclusao_de_participante(client):
    dados = {"nome": "Maria Silva", "email": "Maria@Email.com", "curso": "Engenharia de Software"}
    criado = client.post("/participantes", json=dados)
    assert criado.status_code == 201
    participante = criado.json()
    assert participante["email"] == "maria@email.com"

    assert client.get(f"/participantes/{participante['id']}").json() == participante
    assert client.get("/participantes").json() == [participante]

    atualizado = client.put(
        f"/participantes/{participante['id']}",
        json={"nome": "Maria Souza", "email": "maria@email.com", "curso": "ADS"},
    )
    assert atualizado.status_code == 200
    assert atualizado.json()["nome"] == "Maria Souza"
    assert atualizado.json()["curso"] == "ADS"

    assert client.delete(f"/participantes/{participante['id']}").status_code == 204
    resposta = client.get(f"/participantes/{participante['id']}")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Participante não encontrado."}


def test_validacoes_de_participante(client):
    base = {"nome": "João", "email": "joao@email.com", "curso": "ADS"}
    for alteracao in ({"nome": ""}, {"email": "invalido"}, {"curso": " "}):
        assert client.post("/participantes", json={**base, **alteracao}).status_code == 422


def test_email_duplicado_retorna_409(client, criar_participante):
    existente = criar_participante(email="duplicado@email.com")
    resposta = client.post(
        "/participantes",
        json={"nome": "Outro", "email": "DUPLICADO@email.com", "curso": "ADS"},
    )
    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Já existe um participante cadastrado com este e-mail."}

    outro = criar_participante()
    resposta = client.put(
        f"/participantes/{outro['id']}",
        json={"nome": outro["nome"], "email": existente["email"], "curso": outro["curso"]},
    )
    assert resposta.status_code == 409

    resposta = client.put(
        f"/participantes/{existente['id']}",
        json={"nome": "Novo Nome", "email": existente["email"], "curso": existente["curso"]},
    )
    assert resposta.status_code == 200


def test_inscricao_e_listagem_de_inscritos(client, criar_evento, criar_participante):
    evento = criar_evento()
    participante = criar_participante()

    resposta = client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")
    assert resposta.status_code == 201
    inscricao = resposta.json()
    assert inscricao["evento_id"] == evento["id"]
    assert inscricao["participante_id"] == participante["id"]
    assert inscricao["data_inscricao"]

    inscritos = client.get(f"/eventos/{evento['id']}/inscricoes")
    assert inscritos.status_code == 200
    corpo = inscritos.json()
    assert len(corpo) == 1
    assert corpo[0]["participante"]["email"] == participante["email"]


def test_inscricao_duplicada_retorna_409(client, criar_evento, criar_participante):
    evento = criar_evento()
    participante = criar_participante()
    url = f"/eventos/{evento['id']}/inscricoes/{participante['id']}"
    assert client.post(url).status_code == 201

    resposta = client.post(url)
    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Participante já está inscrito neste evento."}


def test_inscricao_com_evento_ou_participante_inexistente(client, criar_evento, criar_participante):
    evento = criar_evento()
    participante = criar_participante()

    resposta = client.post(f"/eventos/999/inscricoes/{participante['id']}")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Evento não encontrado."}

    resposta = client.post(f"/eventos/{evento['id']}/inscricoes/999")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Participante não encontrado."}

    assert client.get("/eventos/999/inscricoes").status_code == 404


def test_inscricao_sem_vagas_retorna_409(client, criar_evento, criar_participante):
    evento = criar_evento(capacidade=2)
    participantes = [criar_participante() for _ in range(3)]

    for participante in participantes[:2]:
        assert client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}").status_code == 201

    resposta = client.post(f"/eventos/{evento['id']}/inscricoes/{participantes[2]['id']}")
    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Não existem vagas disponíveis para este evento."}


def test_capacidade_nao_pode_ficar_menor_que_inscritos(
    client, criar_evento, criar_participante, evento_payload
):
    evento = criar_evento(capacidade=5)
    for _ in range(3):
        participante = criar_participante()
        client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")

    resposta = client.put(f"/eventos/{evento['id']}", json={**evento_payload, "capacidade": 2})
    assert resposta.status_code == 409

    resposta = client.put(f"/eventos/{evento['id']}", json={**evento_payload, "capacidade": 3})
    assert resposta.status_code == 200


def test_exclusao_remove_inscricoes_sem_deixar_orfaos(client, criar_evento, criar_participante):
    evento_a = criar_evento(titulo="Evento A", capacidade=5)
    evento_b = criar_evento(titulo="Evento B", capacidade=5)
    p1 = criar_participante()
    p2 = criar_participante()
    for evento in (evento_a, evento_b):
        for participante in (p1, p2):
            client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")

    assert client.delete(f"/participantes/{p1['id']}").status_code == 204
    ocupacao = {e["evento_id"]: e for e in client.get("/relatorios/eventos/ocupacao").json()}
    assert ocupacao[evento_a["id"]]["total_inscritos"] == 1
    assert ocupacao[evento_b["id"]]["total_inscritos"] == 1

    assert client.delete(f"/eventos/{evento_a['id']}").status_code == 204
    inscritos_b = client.get(f"/eventos/{evento_b['id']}/inscricoes").json()
    assert [i["participante"]["id"] for i in inscritos_b] == [p2["id"]]

    from database import SessionLocal
    from sqlalchemy import text

    with SessionLocal() as db:
        orfas = db.execute(
            text(
                "SELECT COUNT(*) FROM inscricoes "
                "WHERE evento_id NOT IN (SELECT id FROM eventos) "
                "OR participante_id NOT IN (SELECT id FROM participantes)"
            )
        ).scalar()
    assert orfas == 0


def test_relatorios_vazios(client):
    for rota in (
        "/relatorios/eventos/ocupacao",
        "/relatorios/eventos/categorias",
        "/relatorios/participantes/cursos",
    ):
        resposta = client.get(rota)
        assert resposta.status_code == 200
        assert resposta.json() == []


def test_relatorio_de_ocupacao(client, criar_evento, criar_participante):
    cheio = criar_evento(titulo="Workshop de Python", capacidade=2, categoria="Workshop")
    parcial = criar_evento(titulo="Palestra de IA", capacidade=4, categoria="Palestra")
    vazio = criar_evento(titulo="Seminário", capacidade=10, categoria="Seminário")
    p1, p2 = criar_participante(), criar_participante()

    client.post(f"/eventos/{cheio['id']}/inscricoes/{p1['id']}")
    client.post(f"/eventos/{cheio['id']}/inscricoes/{p2['id']}")
    client.post(f"/eventos/{parcial['id']}/inscricoes/{p1['id']}")

    relatorio = {e["evento_id"]: e for e in client.get("/relatorios/eventos/ocupacao").json()}
    assert len(relatorio) == 3
    assert relatorio[cheio["id"]] == {
        "evento_id": cheio["id"],
        "titulo": "Workshop de Python",
        "capacidade": 2,
        "total_inscritos": 2,
        "vagas_disponiveis": 0,
        "percentual_ocupacao": 100.0,
    }
    assert relatorio[parcial["id"]]["total_inscritos"] == 1
    assert relatorio[parcial["id"]]["vagas_disponiveis"] == 3
    assert relatorio[parcial["id"]]["percentual_ocupacao"] == 25.0
    assert relatorio[vazio["id"]]["total_inscritos"] == 0
    assert relatorio[vazio["id"]]["vagas_disponiveis"] == 10
    assert relatorio[vazio["id"]]["percentual_ocupacao"] == 0.0


def test_relatorio_de_categorias(client, criar_evento, criar_participante):
    w1 = criar_evento(titulo="W1", capacidade=10, categoria="Workshop")
    w2 = criar_evento(titulo="W2", capacidade=20, categoria="Workshop")
    p = criar_evento(titulo="P1", capacidade=100, categoria="Palestra")
    a1, a2, a3 = criar_participante(), criar_participante(), criar_participante()

    for evento, participantes in ((w1, (a1, a2)), (w2, (a1,)), (p, (a1, a2, a3))):
        for participante in participantes:
            client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")

    relatorio = {c["categoria"]: c for c in client.get("/relatorios/eventos/categorias").json()}
    assert relatorio["Workshop"] == {
        "categoria": "Workshop",
        "total_eventos": 2,
        "capacidade_total": 30,
        "total_inscricoes": 3,
    }
    assert relatorio["Palestra"] == {
        "categoria": "Palestra",
        "total_eventos": 1,
        "capacidade_total": 100,
        "total_inscricoes": 3,
    }


def test_relatorio_de_cursos_nao_duplica_participantes(client, criar_evento, criar_participante):
    e1 = criar_evento(titulo="E1", capacidade=10)
    e2 = criar_evento(titulo="E2", capacidade=10)
    e3 = criar_evento(titulo="E3", capacidade=10)
    es1 = criar_participante(curso="Engenharia de Software")
    es2 = criar_participante(curso="Engenharia de Software")
    ads = criar_participante(curso="Análise e Desenvolvimento de Sistemas")
    criar_participante(curso="Sistemas de Informação")

    for evento in (e1, e2, e3):
        client.post(f"/eventos/{evento['id']}/inscricoes/{es1['id']}")
    client.post(f"/eventos/{e1['id']}/inscricoes/{es2['id']}")
    client.post(f"/eventos/{e2['id']}/inscricoes/{ads['id']}")

    relatorio = {c["curso"]: c for c in client.get("/relatorios/participantes/cursos").json()}
    assert relatorio["Engenharia de Software"] == {
        "curso": "Engenharia de Software",
        "total_participantes": 2,
        "total_inscricoes": 4,
    }
    assert relatorio["Análise e Desenvolvimento de Sistemas"]["total_participantes"] == 1
    assert relatorio["Análise e Desenvolvimento de Sistemas"]["total_inscricoes"] == 1
    assert relatorio["Sistemas de Informação"] == {
        "curso": "Sistemas de Informação",
        "total_participantes": 1,
        "total_inscricoes": 0,
    }


def test_relatorios_refletem_alteracoes_nos_dados(
    client, criar_evento, criar_participante, evento_payload
):
    evento = criar_evento(capacidade=4, categoria="Workshop")
    participante = criar_participante(curso="ADS")
    client.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")

    ocupacao = client.get("/relatorios/eventos/ocupacao").json()[0]
    assert ocupacao["total_inscritos"] == 1
    assert ocupacao["percentual_ocupacao"] == 25.0

    client.put(f"/eventos/{evento['id']}", json={**evento_payload, "capacidade": 5, "categoria": "Minicurso"})
    ocupacao = client.get("/relatorios/eventos/ocupacao").json()[0]
    assert ocupacao["capacidade"] == 5
    assert ocupacao["percentual_ocupacao"] == 20.0
    categorias = {c["categoria"]: c for c in client.get("/relatorios/eventos/categorias").json()}
    assert "Workshop" not in categorias
    assert categorias["Minicurso"]["capacidade_total"] == 5
    assert categorias["Minicurso"]["total_inscricoes"] == 1

    client.put(
        f"/participantes/{participante['id']}",
        json={"nome": participante["nome"], "email": participante["email"], "curso": "Engenharia"},
    )
    cursos = {c["curso"]: c for c in client.get("/relatorios/participantes/cursos").json()}
    assert "ADS" not in cursos
    assert cursos["Engenharia"]["total_inscricoes"] == 1

    client.delete(f"/participantes/{participante['id']}")
    assert client.get("/relatorios/participantes/cursos").json() == []
    assert client.get("/relatorios/eventos/ocupacao").json()[0]["total_inscritos"] == 0

    client.delete(f"/eventos/{evento['id']}")
    assert client.get("/relatorios/eventos/ocupacao").json() == []
    assert client.get("/relatorios/eventos/categorias").json() == []


def test_dados_persistem_apos_reinicializar_a_aplicacao(client, evento_payload):
    with TestClient(app) as primeira_execucao:
        evento = primeira_execucao.post("/eventos", json=evento_payload).json()
        participante = primeira_execucao.post(
            "/participantes",
            json={"nome": "Ana", "email": "ana@email.com", "curso": "ADS"},
        ).json()
        primeira_execucao.post(f"/eventos/{evento['id']}/inscricoes/{participante['id']}")

    from database import engine

    engine.dispose()

    with TestClient(app) as segunda_execucao:
        assert segunda_execucao.get(f"/eventos/{evento['id']}").json() == evento
        assert segunda_execucao.get(f"/participantes/{participante['id']}").json() == participante
        inscritos = segunda_execucao.get(f"/eventos/{evento['id']}/inscricoes").json()
        assert len(inscritos) == 1
        assert segunda_execucao.get("/relatorios/eventos/ocupacao").json()[0]["total_inscritos"] == 1
