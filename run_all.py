#!/usr/bin/env python3
"""
run_all.py — Orquestrador de scripts

- Executa uma sequência de scripts Python em ordem.
- Salva logs (stdout + stderr) em uma pasta "logs" ao lado deste arquivo.
- Para no primeiro erro e retorna o mesmo código de saída do script que falhou.

Uso:
  python3 /caminho/para/run_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Define o diretório raiz do workspace
workspace_root = Path(__file__).resolve().parent.parent

SCRIPTS = [
    str(workspace_root / "00_Boletim_Diario" / "Boletim_NYSE_1.1.py"),
    str(workspace_root / "00_Boletim_Diario" / "Boletim_B3_1.2.py"),
    str(workspace_root / "00_Drawdown" / "drawdown_monitor.py"),
    str(workspace_root / "00_MACD" / "MACD_diario.py"),
    str(workspace_root / "00_MACD" / "MACD_semanal.py"),
]


def _resolve_python() -> str:
    # Prioriza override explícito via variável de ambiente.
    py_from_env = Path(os.environ["FINANCAS_PYTHON"]).expanduser() if "FINANCAS_PYTHON" in os.environ else None
    if py_from_env and py_from_env.exists():
        return str(py_from_env)

    # Fallback padrão para venv fora do OneDrive (Ubuntu com PEP 668).
    tmp_venv_python = Path("/tmp/financas-venv/bin/python")
    if tmp_venv_python.exists():
        return str(tmp_venv_python)

    return sys.executable


def slug_name(path: str) -> str:
    p = Path(path)
    # ex: Boletim_NYSE_1.1.py -> Boletim_NYSE_1_1
    return p.stem.replace(".", "_").replace(" ", "_")


def run_script(script_path: str, logs_dir: Path, ts: str) -> int:
    script = Path(script_path)

    if not script.exists():
        print(f"[ERRO] Script não encontrado: {script}", file=sys.stderr)
        return 2

    log_file = logs_dir / f"{ts}__{slug_name(script_path)}.log"

    print(f"\n=== Rodando: {script} ===")
    print(f"Log: {log_file}")

    with log_file.open("w", encoding="utf-8") as f:
        f.write(f"Timestamp: {ts}\n")
        f.write(f"Script: {script}\n")
        selected_python = _resolve_python()
        f.write(f"Python: {selected_python}\n")
        f.write("-" * 80 + "\n")

        cmd = [selected_python, str(script)]

        proc = subprocess.run(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(script.parent),  # roda com cwd no diretório do script
        )

    if proc.returncode == 0:
        print(f"[OK] Finalizado: {script.name}")
    else:
        print(f"[FALHOU] {script.name} (exit code {proc.returncode})", file=sys.stderr)

    return proc.returncode


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    print("Orquestrador iniciado")
    print(f"Python selecionado: {_resolve_python()}")
    print(f"Logs: {logs_dir}")

    for script_path in SCRIPTS:
        code = run_script(script_path, logs_dir, ts)
        if code != 0:
            print("\nInterrompido por erro.", file=sys.stderr)
            return code

    print("\nTudo concluído com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
