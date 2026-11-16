# API de Eventos Acadêmicos — APS 3

API RESTful em **FastAPI** para gerenciar eventos acadêmicos, participantes e inscrições. Nesta versão os dados são persistidos em **SQLite** via **SQLAlchemy ORM** e a API oferece três relatórios de consolidação.

## Tecnologias

Python 3.10+, FastAPI, SQLite, SQLAlchemy 2.x (ORM), Pydantic v2, Uvicorn, Pytest.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

As tabelas são criadas automaticamente na inicialização da aplicação.

## Estrutura do projeto

```
projeto/
├── main.py                      # aplicação, handlers de erro e registro das rotas
├── database.py                  # engine, sessões, Base e criação das tabelas
├── controller/                  # rotas HTTP
│   ├── evento_controller.py
│   ├── participante_controller.py
│   ├── inscricao_controller.py
│   └── relatorio_controller.py
├── model/                       # entidades SQLAlchemy e relacionamentos
│   ├── evento.py
│   ├── participante.py
│   └── inscricao.py
├── schema/                      # validação e respostas (Pydantic)
│   ├── evento_schema.py
│   ├── participante_schema.py
│   ├── inscricao_schema.py
│   └── relatorio_schema.py
├── service/                     # regras de negócio, persistência e consultas
│   ├── evento_service.py
│   ├── participante_service.py
│   ├── inscricao_service.py
│   ├── relatorio_service.py
│   └── excecoes.py              # erros de negócio e commit seguro
├── tests/                       # testes automatizados (pytest)
├── requirements.txt
└── README.md
```

## Configuração do banco de dados

- Banco: SQLite. O arquivo **`eventos.db` é criado na raiz do projeto** na primeira execução (ao lado de `main.py`).
- Para usar outro local, defina a variável de ambiente `DATABASE_URL` (ex.: `sqlite:///./outro.db`).
- `database.py` configura o `engine`, o `SessionLocal`, a `Base` declarativa e a dependência `get_db`, que abre uma sessão por requisição e a fecha ao final.
- As chaves estrangeiras do SQLite são ativadas (`PRAGMA foreign_keys=ON`) a cada conexão.
- Para zerar os dados, pare a aplicação e apague o `eventos.db`.

### Modelo de dados

| Tabela | Colunas principais | Restrições |
|---|---|---|
| `eventos` | id, titulo, descricao, data, horario, local, capacidade, categoria | — |
| `participantes` | id, nome, email, curso | `email` único |
| `inscricoes` | id, evento_id, participante_id, data_inscricao | FKs com `ON DELETE CASCADE`; único (`evento_id`, `participante_id`) |

Relacionamentos: `Evento 1—N Inscrição N—1 Participante`.

### Integridade

- **Exclusão:** excluir um evento ou participante remove também as inscrições vinculadas (cascata), sem deixar registros órfãos.
- **Atualização de capacidade:** não é permitido reduzir a capacidade de um evento abaixo do número de inscritos (409).
- **E-mail:** normalizado para minúsculas; unicidade garantida por consulta prévia e pela restrição do banco.
- **Inscrição duplicada:** verificada no serviço e protegida pela restrição única.
- **Falhas de persistência:** retornam mensagem genérica (500), sem detalhes técnicos.

## Principais rotas

| Método | Rota | Descrição |
|---|---|---|
| POST | `/eventos` | Cadastrar evento (201) |
| GET | `/eventos` | Listar eventos |
| GET | `/eventos/{id}` | Consultar evento |
| PUT | `/eventos/{id}` | Atualizar evento |
| DELETE | `/eventos/{id}` | Excluir evento (204) |
| POST | `/participantes` | Cadastrar participante (201) |
| GET | `/participantes` | Listar participantes |
| GET | `/participantes/{id}` | Consultar participante |
| PUT | `/participantes/{id}` | Atualizar participante |
| DELETE | `/participantes/{id}` | Excluir participante (204) |
| POST | `/eventos/{evento_id}/inscricoes/{participante_id}` | Inscrever participante (201) |
| GET | `/eventos/{evento_id}/inscricoes` | Listar inscritos do evento |
| GET | `/relatorios/eventos/ocupacao` | Relatório de ocupação |
| GET | `/relatorios/eventos/categorias` | Eventos por categoria |
| GET | `/relatorios/participantes/cursos` | Participação por curso |

### Validações (422)

Título, local, categoria, nome e curso não podem ser vazios; e-mail deve ser válido; capacidade deve ser maior que zero; data (`AAAA-MM-DD`) e horário (`HH:MM`) devem ser válidos. A descrição é opcional.

### Erros de negócio

| Situação | Código | Corpo |
|---|---|---|
| Evento inexistente | 404 | `{"detail": "Evento não encontrado."}` |
| Participante inexistente | 404 | `{"detail": "Participante não encontrado."}` |
| Já inscrito | 409 | `{"detail": "Participante já está inscrito neste evento."}` |
| Sem vagas | 409 | `{"detail": "Não existem vagas disponíveis para este evento."}` |
| E-mail repetido | 409 | `{"detail": "Já existe um participante cadastrado com este e-mail."}` |
| Capacidade menor que inscritos | 409 | `{"detail": "A capacidade não pode ser menor que a quantidade de inscritos no evento."}` |

## Relatórios

Todos são calculados dinamicamente com consultas SQLAlchemy (`JOIN`, `GROUP BY`, `COUNT`, `SUM`) e retornam `[]` quando não há registros.

- **Ocupação** (`/relatorios/eventos/ocupacao`): por evento, capacidade, inscritos, vagas disponíveis e percentual de ocupação. Usa `LEFT JOIN`, então eventos sem inscrições aparecem com 0%. O percentual é protegido contra divisão por zero.
- **Categorias** (`/relatorios/eventos/categorias`): por categoria, total de eventos, capacidade total e total de inscrições. As inscrições são contadas em uma subconsulta por evento para não multiplicar a capacidade.
- **Cursos** (`/relatorios/participantes/cursos`): por curso, participantes distintos (`COUNT DISTINCT`, sem contar duas vezes quem tem várias inscrições) e total de inscrições.

## Exemplos de uso

Cadastrar evento:

```bash
curl -X POST http://127.0.0.1:8000/eventos -H "Content-Type: application/json" -d '{
  "titulo": "Workshop de Python",
  "descricao": "Introdução prática",
  "data": "2026-12-10",
  "horario": "14:00",
  "local": "Laboratório 3",
  "capacidade": 40,
  "categoria": "Workshop"
}'
```

Resposta (201):

```json
{
  "titulo": "Workshop de Python",
  "descricao": "Introdução prática",
  "data": "2026-12-10",
  "horario": "14:00:00",
  "local": "Laboratório 3",
  "capacidade": 40,
  "categoria": "Workshop",
  "id": 1
}
```

Cadastrar participante:

```bash
curl -X POST http://127.0.0.1:8000/participantes -H "Content-Type: application/json" -d '{
  "nome": "Ana Souza", "email": "ana@email.com", "curso": "Engenharia de Software"
}'
```

Inscrever e consultar:

```bash
curl -X POST http://127.0.0.1:8000/eventos/1/inscricoes/1
curl http://127.0.0.1:8000/eventos/1/inscricoes
```

```json
{ "id": 1, "evento_id": 1, "participante_id": 1, "data_inscricao": "2026-11-16" }
```

Relatório de ocupação:

```json
[
  {
    "evento_id": 1,
    "titulo": "Workshop de Python",
    "capacidade": 40,
    "total_inscritos": 1,
    "vagas_disponiveis": 39,
    "percentual_ocupacao": 2.5
  }
]
```

Relatório por categoria:

```json
[{ "categoria": "Workshop", "total_eventos": 1, "capacidade_total": 40, "total_inscricoes": 1 }]
```

Relatório por curso:

```json
[{ "curso": "Engenharia de Software", "total_participantes": 1, "total_inscricoes": 1 }]
```

## Como reproduzir os testes

### Automatizados

```bash
pytest -v
```

Os testes usam um banco temporário próprio e não alteram o `eventos.db`. Cobrem CRUD, validações, inscrições (sucesso, duplicada, inexistente, sem vagas), exclusão em cascata, os três relatórios (inclusive após inserir, atualizar e excluir registros) e a persistência após reinicializar a aplicação.

### Manuais pelo Swagger (`/docs`)

1. Cadastre e consulte eventos (`POST`/`GET /eventos`) e participantes (`POST`/`GET /participantes`).
2. Atualize (`PUT`) e exclua (`DELETE`) registros.
3. Inscreva um participante: `POST /eventos/1/inscricoes/1` → 201.
4. Repita a mesma requisição → 409 (inscrição duplicada).
5. Use um `evento_id` inexistente (ex.: 999) → 404.
6. Crie um evento com capacidade 1, inscreva dois participantes → o segundo recebe 409 (sem vagas).
7. Pare o Uvicorn (`Ctrl+C`), inicie novamente e consulte `GET /eventos` e `GET /eventos/1/inscricoes` → os dados continuam lá.
8. Consulte os três relatórios, altere dados (inscrever, atualizar capacidade/categoria/curso, excluir) e consulte de novo para ver os valores mudarem.
