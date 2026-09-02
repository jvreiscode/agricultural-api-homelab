# 🌾 API Agrícola — Self-hosted em Termux

Uma API REST genérica em **Flask + PostgreSQL**, com interface web
autoadaptável, relatórios com JOIN e um console SQL embutido. Projetada
para rodar em ambientes com dependências limitadas — foi desenvolvida e
testada rodando inteiramente dentro do **Termux**, num dispositivo Android
comum, sem exigir nenhuma dependência compilada (C/Rust).

## Índice

- [Sobre o projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Stack tecnológica](#stack-tecnológica)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Interface web](#interface-web)
- [Segurança](#segurança)
- [Documentação adicional](#documentação-adicional)
- [Licença](#licença)

## Sobre o projeto

Este projeto nasceu da necessidade de expor um banco PostgreSQL através de
uma API HTTP simples, capaz de rodar em hardware modesto e ambientes com
restrições de compilação — como um dispositivo Android via Termux. Em vez
de depender de frameworks com dependências nativas pesadas (Rust, C), a
API foi construída inteiramente com bibliotecas **100% Python puro**.

O projeto é genérico o suficiente pra funcionar com **qualquer schema
PostgreSQL** — ele introspecciona o banco em tempo real (via
`information_schema`) pra descobrir tabelas e colunas, tanto pra gerar os
endpoints de CRUD quanto pra montar o formulário web automaticamente.

## Funcionalidades

- ✅ **CRUD genérico** — funciona com qualquer tabela do schema `public`, sem precisar escrever código novo pra cada uma
- ✅ **Introspecção de schema** — lista tabelas e colunas automaticamente via `information_schema`
- ✅ **Interface web** — formulário HTML/JS que se adapta à tabela selecionada, sem frameworks front-end
- ✅ **Relatórios com JOIN** — endpoints específicos que combinam múltiplas tabelas
- ✅ **Visão geral do banco** — contagem de linhas/colunas por tabela
- ✅ **Console SQL** — execução de comandos SQL livres direto pela interface web
- ✅ **Autenticação simples** — via header `X-API-Key`, opcional
- ✅ **Proteção contra SQL injection** — whitelist dinâmica de tabelas/colunas nos endpoints de CRUD, valores sempre parametrizados
- ✅ **Zero dependências compiladas** — todas as bibliotecas usadas são Python puro

## Stack tecnológica

| Camada | Tecnologia | Motivo |
|---|---|---|
| API | [Flask](https://flask.palletsprojects.com/) | Framework web leve, sem dependências nativas |
| Banco | PostgreSQL | Robusto, suporta bem schemas relacionais |
| Driver do banco | [pg8000](https://github.com/tlocke/pg8000) | Driver PostgreSQL 100% Python (sem C/Rust) |
| Frontend | HTML/CSS/JS vanilla | Sem build step, sem dependências de Node |

> **Por que não FastAPI + Pydantic?** Testamos originalmente, mas o
> `pydantic-core` (Pydantic v2) depende de um binário compilado em Rust sem
> build disponível para algumas arquiteturas/ambientes restritos, e o
> Pydantic v1 (Python puro) não é compatível com Python 3.12+. Ver
> [`docs/TERMUX-SETUP.md`](docs/TERMUX-SETUP.md) para o histórico completo.

## Estrutura do projeto

```
.
├── main.py                 # API Flask (todas as rotas)
├── requirements.txt        # flask, pg8000
├── .env.example             # modelo de variáveis de ambiente
├── iniciar.sh               # script de inicialização (Postgres + API)
├── schema_exemplo.sql       # schema de exemplo (fazendas, funcionários, máquinas...)
├── static/
│   └── index.html            # interface web (formulário + visão geral + console SQL)
└── docs/
    ├── API.md                # referência completa dos endpoints
    └── TERMUX-SETUP.md        # guia de instalação específico para Termux/Android
```

## Pré-requisitos

- Python 3.9+
- PostgreSQL (local ou remoto)
- `pip`

## Instalação

```bash
git clone <url-do-repositorio>
cd <pasta-do-projeto>
pip install -r requirements.txt
```

Crie o banco de dados e carregue o schema de exemplo (ou o seu próprio):

```bash
createdb -O seu_usuario nome_do_banco
psql -U seu_usuario -d nome_do_banco -f schema_exemplo.sql
```

## Configuração

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nome_do_banco

# Nome da coluna usada como chave primária nos endpoints /<table>/<id>
DEFAULT_PK_COLUMN=id

# Opcional: exige o header X-API-Key em toda requisição
API_KEY=uma-chave-secreta-forte
```

> **Convenção do schema:** os endpoints de item único (`GET/PUT/DELETE
> /<table>/<id>`) assumem que toda tabela tem uma coluna de chave primária
> com o mesmo nome (configurável via `DEFAULT_PK_COLUMN`, padrão `id`).

## Uso

Suba a API:

```bash
python main.py
```

Por padrão, sobe em `http://0.0.0.0:8000`. Acesse a raiz
(`http://localhost:8000`) e você é redirecionado automaticamente para a
interface web.

Exemplo de uso via `curl`:

```bash
# Listar tabelas
curl -H "X-API-Key: sua-chave" http://localhost:8000/tables

# Listar registros de uma tabela
curl -H "X-API-Key: sua-chave" http://localhost:8000/fazendas

# Criar um registro
curl -X POST http://localhost:8000/fazendas \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave" \
  -d '{"data": {"nome": "Fazenda Exemplo", "cidade": "Exemplo - SP", "area_hectares": 100}}'
```

Referência completa de todos os endpoints em [`docs/API.md`](docs/API.md).

## Interface web

Acessível em `/ui/` (ou na raiz `/`, que redireciona pra lá). Não exige
nenhuma configuração adicional — ela mesma detecta o endereço da API
(baseado na URL atual) e permite configurar a `API_KEY` diretamente pelo
navegador, salva localmente no dispositivo.

Inclui três seções:
1. **Formulário de cadastro** — gerado dinamicamente a partir do schema da tabela selecionada
2. **Visão geral do banco** — contagem de linhas/colunas por tabela
3. **Console SQL** — execução de comandos SQL livres, com resultado exibido como tabela

## Segurança

- Os endpoints de **CRUD genérico** validam nomes de tabela/coluna contra
  o `information_schema` antes de montar qualquer SQL, e todos os valores
  são passados via parâmetros nomeados (nunca concatenados na query) —
  proteção padrão contra SQL injection.
- O endpoint **`/sql`** é uma exceção deliberada: ele executa qualquer
  comando SQL enviado, sem sanitização, incluindo `DROP`, `DELETE` sem
  `WHERE`, etc. É pensado como ferramenta de administração para o próprio
  dono do banco — **não exponha esse endpoint publicamente sem controle de
  acesso adequado**.
- A autenticação via `API_KEY` é simples (comparação direta de string) e
  não substitui HTTPS/TLS em produção. Para uso pessoal/doméstico atrás de
  uma VPN (ex: Tailscale, WireGuard), é suficiente; para exposição pública
  na internet, recomenda-se colocar atrás de um proxy reverso com HTTPS.

## Documentação adicional

- [`docs/API.md`](docs/API.md) — referência completa de todos os endpoints, com exemplos
- [`docs/TERMUX-SETUP.md`](docs/TERMUX-SETUP.md) — guia de instalação específico para Termux/Android, incluindo os problemas de ambiente resolvidos durante o desenvolvimento

## Licença

Este projeto é disponibilizado livremente para uso pessoal e educacional.
Adapte conforme sua necessidade.
