#!/bin/sh
# Crea la base de tests junto a la de desarrollo, solo la primera vez que se
# inicializa el volumen de Postgres.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "CREATE DATABASE \"${POSTGRES_TEST_DB}\" OWNER \"${POSTGRES_USER}\";"
