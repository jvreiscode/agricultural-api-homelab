# Referência da API

Todos os endpoints, exceto onde indicado, aceitam o header opcional
`X-API-Key` — obrigatório apenas se a variável `API_KEY` estiver definida
no `.env`. Se não estiver definida, a checagem é ignorada.

Todas as respostas são em JSON.

## Metadados

### `GET /tables`

Lista todas as tabelas do schema `public`.

**Resposta:**
```json
{ "tables": ["abastecimentos", "fazendas", "funcionarios"] }
```

### `GET /tables/<table>/schema`

Lista as colunas de uma tabela, com tipo e nulabilidade.

**Resposta:**
```json
{
  "table": "fazendas",
  "columns": [
    { "name": "id", "type": "integer", "nullable": false },
    { "name": "nome", "type": "character varying", "nullable": false },
    { "name": "area_hectares", "type": "numeric", "nullable": true }
  ]
}
```

**Erros:** `404` se a tabela não existir.

### `GET /overview`

Retorna, para cada tabela, a quantidade de linhas e de colunas.

**Resposta:**
```json
{
  "tables": [
    { "table": "fazendas", "rows": 5, "columns": 4 },
    { "table": "funcionarios", "rows": 7, "columns": 5 }
  ]
}
```

## CRUD genérico

Funciona para qualquer tabela existente no schema `public`. O nome da
tabela e das colunas é sempre validado contra o banco antes de qualquer
consulta ser executada.

### `GET /<table>`

Lista registros, com paginação.

**Query params:**
- `limit` (padrão `50`, máximo `500`)
- `offset` (padrão `0`)

**Exemplo:** `GET /fazendas?limit=10&offset=20`

**Resposta:**
```json
{ "data": [ { "id": 1, "nome": "Fazenda Horizonte", ... }, ... ] }
```

### `GET /<table>/<id>`

Busca um único registro pela chave primária (nome configurável via
`DEFAULT_PK_COLUMN`, padrão `id`).

**Resposta:** o objeto do registro, ou `404` se não existir.

### `POST /<table>`

Cria um novo registro.

**Corpo esperado:**
```json
{ "data": { "nome": "Fazenda Nova", "cidade": "Exemplo - SP" } }
```

**Resposta:** `201 Created`, com o registro completo (incluindo o `id`
gerado).

**Erros:**
- `400` se `data` estiver vazio ou faltando
- `400` se alguma coluna informada não existir na tabela
- `404` se a tabela não existir

### `PUT /<table>/<id>`

Atualiza um registro existente. Aceita atualização parcial — só as chaves
enviadas em `data` são alteradas.

**Corpo esperado:**
```json
{ "data": { "area_hectares": 150 } }
```

**Resposta:** o registro atualizado, ou `404` se não existir.

### `DELETE /<table>/<id>`

Remove um registro.

**Resposta:**
```json
{ "deleted": true }
```

ou `404` se o registro não existir.

## Relatórios (JOIN)

Endpoints específicos que combinam múltiplas tabelas — dependem do schema
de exemplo incluído no projeto (fazendas, funcionários, máquinas, ordens de
serviço, abastecimentos). Se você adaptar o schema, ajuste ou remova esses
endpoints em `main.py`.

### `GET /relatorios/ordens-servico`

Ordens de serviço com nome da fazenda e da operação (em vez dos IDs).

### `GET /relatorios/abastecimentos`

Abastecimentos com nome do funcionário e descrição/patrimônio da máquina.

### `GET /relatorios/maquinas`

Máquinas com nome da fazenda.

### `GET /relatorios/funcionarios`

Funcionários com nome da fazenda.

Todos retornam no formato:
```json
{ "data": [ { ... }, { ... } ] }
```

## Console SQL

### `POST /sql`

Executa uma query SQL arbitrária.

⚠️ **Sem sanitização.** Aceita qualquer comando — `SELECT`, `INSERT`,
`UPDATE`, `DELETE`, `CREATE TABLE`, `DROP TABLE`, etc. Pensado como
ferramenta de administração pessoal, não para uso com entrada não
confiável. Ver seção de segurança no README principal.

**Corpo esperado:**
```json
{ "query": "SELECT * FROM fazendas WHERE area_hectares > 1000" }
```

**Resposta (consultas que retornam linhas):**
```json
{
  "columns": ["id", "nome", "cidade", "area_hectares"],
  "rows": [ { "id": 1, "nome": "Fazenda Horizonte", ... } ]
}
```

**Resposta (comandos sem retorno de linhas, ex: `UPDATE`, `CREATE TABLE`):**
```json
{ "message": "Comando executado com sucesso.", "rows": [] }
```

**Resposta (erro de SQL):**
```json
{ "error": "mensagem de erro do PostgreSQL" }
```
(status `400`)

## Interface web e utilitários

### `GET /`

Redireciona para `/ui/`.

### `GET /ui/`

Serve a interface web (`static/index.html`).

### `GET /health`

Health check simples, sem autenticação.

**Resposta:**
```json
{ "status": "ok", "message": "..." }
```

## Códigos de status usados

| Código | Significado |
|---|---|
| `200` | Sucesso |
| `201` | Registro criado com sucesso |
| `400` | Requisição inválida (corpo malformado, coluna inexistente, erro de SQL) |
| `401` | API key ausente ou inválida |
| `404` | Tabela ou registro não encontrado |
