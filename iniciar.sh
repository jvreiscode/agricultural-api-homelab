#!/data/data/com.termux/files/usr/bin/sh
# ------------------------------------------------------------------
# Script de inicialização: liga o Postgres + sobe a API FastAPI
# ------------------------------------------------------------------

# Evita que o Android mate o processo em segundo plano
termux-wake-lock

# Espera a rede subir (útil principalmente no boot do celular)
sleep 15

# Liga o PostgreSQL, se ainda não estiver rodando
pg_ctl -D $PREFIX/var/lib/postgresql status > /dev/null 2>&1
if [ $? -ne 0 ]; then
    pg_ctl -D $PREFIX/var/lib/postgresql start
fi

# Entra na pasta do projeto
cd ~/api_agricola || exit 1

# Carrega as variáveis do .env (ignora comentários e linhas vazias)
set -a
. ./.env
set +a

# Sobe a API em segundo plano, salvando o log num arquivo
nohup python main.py > ~/api_agricola/api.log 2>&1 &
