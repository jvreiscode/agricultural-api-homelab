# Guia de instalação — Termux / Android

Este guia cobre a instalação específica para rodar o projeto inteiramente
dentro do [Termux](https://termux.dev/) (recomendado: instalar via
[F-Droid](https://f-droid.org/), não pela Play Store, que distribui uma
versão desatualizada e sem suporte).

Também documenta os problemas de ambiente enfrentados durante o
desenvolvimento e suas soluções — vale a leitura mesmo se você não vai
reproduzir exatamente esse setup, pois vários desses problemas são comuns
a qualquer projeto Python rodando em Termux.

## 1. Preparar o Termux

```bash
pkg update && pkg upgrade
pkg install python postgresql
```

## 2. Inicializar o PostgreSQL

```bash
initdb $PREFIX/var/lib/postgresql
pg_ctl -D $PREFIX/var/lib/postgresql start
createuser -s -P seu_usuario
createdb -O seu_usuario nome_do_banco
```

## 3. Instalar o projeto

**Importante:** instale o projeto na home real do Termux
(`/data/data/com.termux/files/home/...`), não em `~/storage/shared/...`
(armazenamento compartilhado do Android). Veja o motivo na seção de
gotchas abaixo.

```bash
cd ~
git clone <url-do-repositorio> api_agricola
cd api_agricola
pip install -r requirements.txt
```

## 4. Configurar

```bash
cp .env.example .env
nano .env   # preencha com suas credenciais reais
```

## 5. Carregar o schema

```bash
psql -U seu_usuario -d nome_do_banco -f schema_exemplo.sql
```

## 6. Rodar

```bash
python main.py
```

Ou, pra rodar em segundo plano com log:

```bash
chmod +x iniciar.sh
./iniciar.sh
```

## 7. Manter rodando (opcional)

Para a API sobreviver ao fechamento do Termux ou a um reboot do celular,
use o app complementar **Termux:Boot** (também pela F-Droid):

1. Instale o Termux:Boot e abra ele uma vez (concede a permissão necessária)
2. Copie o script de inicialização:
   ```bash
   mkdir -p ~/.termux/boot
   cp iniciar.sh ~/.termux/boot/start-agricola.sh
   ```
3. Instale também o Termux:API (`pkg install termux-api`, mais o app
   correspondente na F-Droid) — necessário para o `termux-wake-lock` usado
   no script, que evita que o Android mate o processo em segundo plano
4. Nas configurações do Android, desative a otimização de bateria para o
   Termux e o Termux:Boot

## Problemas de ambiente conhecidos (e soluções)

Esta seção documenta problemas reais enfrentados rodando este tipo de
projeto em Termux. Se você está adaptando este projeto para outro ambiente
Android, é bem provável que esbarre em algum destes.

### FastAPI + Pydantic não funciona neste tipo de ambiente

O projeto foi originalmente escrito com FastAPI, mas isso se mostrou
inviável em Termux/Android:

- **Pydantic v2** depende do `pydantic-core`, escrito em Rust. Não existe
  wheel pré-compilada para a arquitetura Android/Termux no PyPI, então o
  `pip install` tenta compilar do zero — o que exige uma toolchain Rust
  completa e pode não funcionar mesmo assim (o `maturin`, usado para o
  build, tenta baixar um Rust via `rustup`, que não suporta o target
  triple `arm-linux-androideabi`).
- **Pydantic v1** (Python puro, sem Rust) parecia ser a solução, mas quebra
  em Python 3.12+ com `ConfigError: unable to infer type for attribute` —
  e o Termux normalmente distribui uma versão bem recente do Python.

**Solução adotada:** reescrever a API em **Flask**, que não depende de
Pydantic. Combinado com `pg8000` (driver PostgreSQL 100% Python), o projeto
não tem nenhuma dependência compilada.

### Armazenamento compartilhado do Android não suporta permissão de execução

Arquivos dentro de `~/storage/shared/...` (que mapeia para
`/storage/emulated/0`, o armazenamento compartilhado do Android) ficam num
sistema de arquivos que não respeita corretamente permissões Unix como
`chmod +x`. Scripts `.sh` precisam estar fisicamente dentro da home privada
do Termux (`/data/data/com.termux/files/home/...`) para serem executáveis
de verdade.

Se você usa alguma ferramenta de transferência de arquivos que grava no
armazenamento compartilhado (como um servidor de arquivos rodando no
próprio Termux), copie os arquivos para a home real antes de dar
`chmod +x`:

```bash
cp -r ~/storage/shared/api_agricola ~/api_agricola
chmod +x ~/api_agricola/iniciar.sh
```

### `sh` do Android exige `./` explícito para arquivos no diretório atual

O shell padrão do Termux (`sh`, geralmente `dash` ou `ash`) trata `. .env`
(sem barra) como uma busca no `$PATH`, não no diretório atual — resultando
em erro "not found" mesmo com o arquivo presente. A forma correta é:

```sh
. ./.env
```

### Arquivos de outros sistemas operacionais podem quebrar o shebang

Se um script `.sh` passar por Windows (ou qualquer editor que use `\r\n`
em vez de `\n`), o shebang (`#!/bin/sh`) pode quebrar com erro do tipo
`bad interpreter`. Corrige com:

```bash
sed -i 's/\r$//' script.sh
```

### Carregar `.env` com comentários quebra `export $(cat ...)`

O padrão comum `export $(cat .env | xargs)` falha se o arquivo tiver
linhas de comentário (`# ...`), porque tenta interpretar o `#` como nome
de variável. Use, ao invés disso:

```sh
set -a
. ./.env
set +a
```

Isso ignora comentários e linhas vazias corretamente.

### Apps complementares (Termux:Boot, Termux:API) precisam ser da mesma fonte

Se o Termux foi instalado pela F-Droid, os apps complementares
(Termux:Boot, Termux:API, etc.) também precisam ser da F-Droid — versões
da Play Store têm assinatura diferente e não se conectam ao Termux
instalado por outra fonte.
