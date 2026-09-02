"""
API genérica (CRUD) em Flask para acessar um banco PostgreSQL.
Pensada para rodar no Termux (Android) com o mínimo de dependências nativas
(Flask e pg8000 são 100% Python puro — nada de compilar C ou Rust).

Endpoints:
  GET    /tables                        -> lista as tabelas do schema "public"
  GET    /tables/<table>/schema         -> lista as colunas da tabela
  GET    /<table>                       -> lista registros (paginação: ?limit=&offset=)
  GET    /<table>/<id>                  -> busca um registro pela PK
  POST   /<table>                       -> cria um registro (body: {"data": {...}})
  PUT    /<table>/<id>                  -> atualiza um registro (body: {"data": {...}})
  DELETE /<table>/<id>                  -> remove um registro

  GET    /relatorios/ordens-servico     -> ordens de serviço com nome da fazenda/operação
  GET    /relatorios/abastecimentos     -> abastecimentos com nome do funcionário/máquina
  GET    /relatorios/maquinas           -> máquinas com nome da fazenda
  GET    /relatorios/funcionarios       -> funcionários com nome da fazenda

  GET    /ui/                           -> formulário web (interface)
  GET    /                              -> redireciona para /ui/

Segurança básica:
  - Nomes de tabela/coluna são validados contra o information_schema
    (whitelist dinâmica) antes de entrar em qualquer SQL, evitando injeção.
  - Valores sempre vão via parâmetros nomeados, nunca concatenados na query.
  - Uma API key simples pode ser exigida via header "X-API-Key" (opcional).
"""

import os
from contextlib import contextmanager

import pg8000.native
from flask import Flask, abort, jsonify, redirect, request, send_from_directory

# --------------------------------------------------------------------------
# Configuração (via variáveis de ambiente, veja .env.example)
# --------------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "postgres")
API_KEY = os.getenv("API_KEY")  # se vazio/None, a checagem de API key fica desativada

DEFAULT_PK = os.getenv("DEFAULT_PK_COLUMN", "id")

app = Flask(__name__, static_folder="static", static_url_path="/ui")


# --------------------------------------------------------------------------
# Conexão com o banco
# --------------------------------------------------------------------------
@contextmanager
def get_conn():
    conn = pg8000.native.Connection(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    try:
        yield conn
    finally:
        conn.close()


def check_api_key():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="API key inválida ou ausente")


# --------------------------------------------------------------------------
# Whitelist dinâmica de tabelas/colunas (proteção contra SQL injection)
# --------------------------------------------------------------------------
def valid_table_names(conn) -> set:
    rows = conn.run(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    return {r[0] for r in rows}


def valid_column_names(conn, table: str) -> set:
    rows = conn.run(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t",
        t=table,
    )
    return {r[0] for r in rows}


def assert_valid_table(conn, table: str):
    if table not in valid_table_names(conn):
        abort(404, description=f"Tabela '{table}' não existe")


def assert_valid_columns(conn, table: str, columns: list):
    valid = valid_column_names(conn, table)
    invalid = [c for c in columns if c not in valid]
    if invalid:
        abort(400, description=f"Coluna(s) inválida(s): {invalid}")


# --------------------------------------------------------------------------
# Tratamento de erros (formato JSON consistente, como antes)
# --------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
def handle_error(e):
    return jsonify({"detail": getattr(e, "description", str(e))}), e.code


# --------------------------------------------------------------------------
# Página inicial / interface web
# --------------------------------------------------------------------------
@app.route("/")
def home():
    return redirect("/ui/")


@app.route("/ui/")
def ui_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "message": "API rodando no Termux 🎉"})


# --------------------------------------------------------------------------
# Metadados (tabelas e schema)
# --------------------------------------------------------------------------
@app.route("/tables")
def list_tables():
    check_api_key()
    with get_conn() as conn:
        return jsonify({"tables": sorted(valid_table_names(conn))})


@app.route("/overview")
def overview():
    """Visão geral: nome, quantidade de linhas e de colunas de cada tabela."""
    check_api_key()
    with get_conn() as conn:
        tables = sorted(valid_table_names(conn))
        resumo = []
        for t in tables:
            linhas = conn.run(f'SELECT COUNT(*) FROM "{t}"')[0][0]
            colunas = conn.run(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t",
                t=t,
            )[0][0]
            resumo.append({"table": t, "rows": linhas, "columns": colunas})
        return jsonify({"tables": resumo})


@app.route("/tables/<table>/schema")
def table_schema(table):
    check_api_key()
    with get_conn() as conn:
        assert_valid_table(conn, table)
        rows = conn.run(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t "
            "ORDER BY ordinal_position",
            t=table,
        )
        return jsonify(
            {
                "table": table,
                "columns": [
                    {"name": r[0], "type": r[1], "nullable": r[2] == "YES"}
                    for r in rows
                ],
            }
        )


# --------------------------------------------------------------------------
# Relatórios (endpoints com JOIN, específicos do schema agro_estudo)
# --------------------------------------------------------------------------
@app.route("/relatorios/ordens-servico")
def relatorio_ordens_servico():
    """Ordens de serviço já com o nome da fazenda e da operação, em vez dos IDs."""
    check_api_key()
    with get_conn() as conn:
        rows = conn.run(
            """
            SELECT os.id, f.nome AS fazenda, o.descricao AS operacao,
                   os.data_abertura, os.data_fechamento, os.status
            FROM ordens_servico os
            JOIN fazendas f ON f.id = os.id_fazenda
            JOIN operacoes o ON o.id = os.id_operacao
            ORDER BY os.data_abertura DESC
            """
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify({"data": [dict(zip(columns, row)) for row in rows]})


@app.route("/relatorios/abastecimentos")
def relatorio_abastecimentos():
    """Abastecimentos já com o nome do funcionário e da máquina, em vez dos IDs."""
    check_api_key()
    with get_conn() as conn:
        rows = conn.run(
            """
            SELECT a.id, fn.nome AS funcionario, m.descricao AS maquina,
                   m.patrimonio, a.data_abastecimento, a.litros, a.horimetro
            FROM abastecimentos a
            JOIN funcionarios fn ON fn.id = a.id_funcionario
            JOIN maquinas m ON m.id = a.id_maquina
            ORDER BY a.data_abastecimento DESC
            """
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify({"data": [dict(zip(columns, row)) for row in rows]})


@app.route("/relatorios/maquinas")
def relatorio_maquinas():
    """Máquinas já com o nome da fazenda, em vez do ID."""
    check_api_key()
    with get_conn() as conn:
        rows = conn.run(
            """
            SELECT m.id, m.patrimonio, m.descricao, m.tipo, f.nome AS fazenda, m.ativo
            FROM maquinas m
            JOIN fazendas f ON f.id = m.id_fazenda
            ORDER BY f.nome, m.descricao
            """
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify({"data": [dict(zip(columns, row)) for row in rows]})


@app.route("/relatorios/funcionarios")
def relatorio_funcionarios():
    """Funcionários já com o nome da fazenda, em vez do ID."""
    check_api_key()
    with get_conn() as conn:
        rows = conn.run(
            """
            SELECT fn.id, fn.nome, fn.cargo, f.nome AS fazenda, fn.ativo
            FROM funcionarios fn
            JOIN fazendas f ON f.id = fn.id_fazenda
            ORDER BY f.nome, fn.nome
            """
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify({"data": [dict(zip(columns, row)) for row in rows]})


@app.route("/sql", methods=["POST"])
def run_sql():
    """
    Executa uma query SQL livre, digitada pelo usuário no console web.
    ATENÇÃO: aceita qualquer comando (SELECT, INSERT, UPDATE, DELETE, DDL...).
    Não há confirmação extra — o que for digitado, roda de verdade.
    """
    check_api_key()
    body = request.get_json(force=True, silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        abort(400, description="Informe uma query SQL no campo 'query'")

    with get_conn() as conn:
        try:
            rows = conn.run(query)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        if not rows:
            return jsonify({"message": "Comando executado com sucesso.", "rows": []})

        columns = [c["name"] for c in conn.columns] if conn.columns else []
        return jsonify(
            {"columns": columns, "rows": [dict(zip(columns, row)) for row in rows]}
        )


# --------------------------------------------------------------------------
# CRUD genérico
# --------------------------------------------------------------------------
@app.route("/<table>", methods=["GET"])
def list_records(table):
    check_api_key()
    limit = min(request.args.get("limit", 50, type=int), 500)
    offset = max(request.args.get("offset", 0, type=int), 0)
    with get_conn() as conn:
        assert_valid_table(conn, table)
        rows = conn.run(
            f'SELECT * FROM "{table}" LIMIT :limit OFFSET :offset',
            limit=limit,
            offset=offset,
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify({"data": [dict(zip(columns, row)) for row in rows]})


@app.route("/<table>/<record_id>", methods=["GET"])
def get_record(table, record_id):
    check_api_key()
    with get_conn() as conn:
        assert_valid_table(conn, table)
        assert_valid_columns(conn, table, [DEFAULT_PK])
        rows = conn.run(
            f'SELECT * FROM "{table}" WHERE "{DEFAULT_PK}" = :id',
            id=record_id,
        )
        if not rows:
            abort(404, description="Registro não encontrado")
        columns = [c["name"] for c in conn.columns]
        return jsonify(dict(zip(columns, rows[0])))


@app.route("/<table>", methods=["POST"])
def create_record(table):
    check_api_key()
    body = request.get_json(force=True, silent=True) or {}
    data = body.get("data", {})
    if not data:
        abort(400, description="Corpo precisa ter o formato {'data': {...}}")

    with get_conn() as conn:
        assert_valid_table(conn, table)
        assert_valid_columns(conn, table, list(data.keys()))

        cols = list(data.keys())
        col_list = ", ".join(f'"{c}"' for c in cols)
        placeholder_list = ", ".join(f":{c}" for c in cols)

        rows = conn.run(
            f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholder_list}) RETURNING *',
            **data,
        )
        columns = [c["name"] for c in conn.columns]
        return jsonify(dict(zip(columns, rows[0]))), 201


@app.route("/<table>/<record_id>", methods=["PUT"])
def update_record(table, record_id):
    check_api_key()
    body = request.get_json(force=True, silent=True) or {}
    data = body.get("data", {})
    if not data:
        abort(400, description="Corpo precisa ter o formato {'data': {...}}")

    with get_conn() as conn:
        assert_valid_table(conn, table)
        assert_valid_columns(conn, table, list(data.keys()) + [DEFAULT_PK])

        set_clause = ", ".join(f'"{c}" = :{c}' for c in data.keys())
        params = dict(data)
        params["__id"] = record_id

        rows = conn.run(
            f'UPDATE "{table}" SET {set_clause} WHERE "{DEFAULT_PK}" = :__id RETURNING *',
            **params,
        )
        if not rows:
            abort(404, description="Registro não encontrado")
        columns = [c["name"] for c in conn.columns]
        return jsonify(dict(zip(columns, rows[0])))


@app.route("/<table>/<record_id>", methods=["DELETE"])
def delete_record(table, record_id):
    check_api_key()
    with get_conn() as conn:
        assert_valid_table(conn, table)
        assert_valid_columns(conn, table, [DEFAULT_PK])
        rows = conn.run(
            f'DELETE FROM "{table}" WHERE "{DEFAULT_PK}" = :id RETURNING *',
            id=record_id,
        )
        if not rows:
            abort(404, description="Registro não encontrado")
        return jsonify({"deleted": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
