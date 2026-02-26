#!/usr/bin/env bash
set -euo pipefail

# Bootstrap do ambiente para executar_boletins.py fora do OneDrive.
# Uso:
#   bash Financas/00_Automacoes/setup_financas_env.sh
#   bash Financas/00_Automacoes/setup_financas_env.sh --test

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOLETINS_SCRIPT="${SCRIPT_DIR}/executar_boletins.py"

VENV_DIR="${FINANCAS_VENV_DIR:-/tmp/financas-venv}"
PYTHON_BIN="${PYTHON_BIN:-/bin/python3}"
RUN_TEST=0

if [[ "${1:-}" == "--test" ]]; then
  RUN_TEST=1
fi

echo "==> Preparando ambiente Financas"
echo "    VENV_DIR: ${VENV_DIR}"
echo "    PYTHON_BIN: ${PYTHON_BIN}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "ERRO: Python nao encontrado em ${PYTHON_BIN}" >&2
  exit 2
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "==> Criando venv em ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "==> Venv ja existe em ${VENV_DIR}"
fi

VENV_PY="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

if ! "${VENV_PY}" -c "import papermill" >/dev/null 2>&1; then
  echo "==> Instalando papermill"
  "${VENV_PIP}" install papermill
else
  echo "==> papermill ja instalado"
fi

if ! "${VENV_PY}" -c "import ipykernel" >/dev/null 2>&1; then
  echo "==> Instalando ipykernel"
  "${VENV_PIP}" install ipykernel
else
  echo "==> ipykernel ja instalado"
fi

echo "==> Registrando kernel python3 no prefixo do venv"
"${VENV_PY}" -m ipykernel install \
  --prefix "${VENV_DIR}" \
  --name python3 \
  --display-name "python3"

echo "==> Ambiente pronto"
echo "    Python do venv: ${VENV_PY}"
echo "    Dica: FINANCAS_PYTHON=${VENV_PY}"

if [[ "${RUN_TEST}" -eq 1 ]]; then
  echo "==> Teste rapido (--list)"
  FINANCAS_PYTHON="${VENV_PY}" /usr/bin/python3 "${BOLETINS_SCRIPT}" --list
fi

echo "==> Concluido"
