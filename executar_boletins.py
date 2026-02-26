"""
Script para execução automática de notebooks Jupyter
Autor: Charles Lima
"""

from pathlib import Path
import os
import subprocess
import tempfile
import platform
import configparser
import sys
import argparse
import traceback
from typing import Iterable


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p))).resolve()


def _expand_no_resolve(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def _add_local_site_packages() -> None:
    """
    Add local .venv site-packages path (if present) to sys.path.
    Useful when this script is run with /bin/python3.
    """
    venv_lib = Path(__file__).with_name(".venv") / "lib"
    py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    sp = venv_lib / py_ver / "site-packages"
    if sp.exists():
        sp_s = str(sp)
        if sp_s not in sys.path:
            sys.path.insert(0, sp_s)


def _import_papermill():
    _add_local_site_packages()
    try:
        import papermill as pm
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Modulo 'papermill' nao encontrado.\n"
            "Opcao 1 (recomendada): use um venv fora do OneDrive, ex. /tmp:\n"
            "  /bin/python3 -m venv /tmp/financas-venv\n"
            "  /tmp/financas-venv/bin/pip install papermill\n"
            "  /tmp/financas-venv/bin/python Financas/00_Automacoes/executar_boletins.py\n"
            "Opcao 2: /bin/python3 -m pip install --user --break-system-packages papermill"
        ) from e
    return pm


def _resolve_runner_python() -> Path | None:
    py_from_env = os.environ.get("FINANCAS_PYTHON")
    if py_from_env:
        p = _expand_no_resolve(py_from_env)
        if p.exists():
            return p

    tmp_venv_python = Path("/tmp/financas-venv/bin/python")
    if tmp_venv_python.exists():
        return tmp_venv_python

    return None


def _maybe_reexec_with_runner_python() -> None:
    if os.environ.get("FINANCAS_REEXEC") == "1":
        return

    preferred = _resolve_runner_python()
    if not preferred:
        return

    # Nao usar resolve(): em venv, /tmp/.../python pode resolver para /usr/bin/python3.X.
    # O que importa aqui e o launcher (path do executavel), pois ele define o contexto do venv.
    current = Path(sys.executable).absolute()
    preferred_abs = preferred.absolute()
    if preferred_abs == current:
        return

    env = dict(os.environ)
    env["FINANCAS_REEXEC"] = "1"
    cmd = [str(preferred_abs), str(Path(__file__).resolve()), *sys.argv[1:]]
    proc = subprocess.run(cmd, env=env)
    raise SystemExit(proc.returncode)


def _validate_kernel(kernel_name: str) -> None:
    try:
        from jupyter_client.kernelspec import KernelSpecManager
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Dependencia 'jupyter_client' nao encontrada no ambiente atual."
        ) from e

    specs = KernelSpecManager().find_kernel_specs()
    if kernel_name in specs:
        return

    available = ", ".join(sorted(specs)) if specs else "(nenhum)"
    py = Path(sys.executable)
    raise RuntimeError(
        f"Kernel '{kernel_name}' nao encontrado. Kernels disponiveis: {available}\n"
        "Instale e registre um kernel no ambiente em uso:\n"
        f"  {py} -m pip install ipykernel\n"
        f"  {py} -m ipykernel install --prefix {Path(sys.prefix)} --name {kernel_name} --display-name \"{kernel_name}\""
    )


def _default_config_path() -> Path:
    system = platform.system().lower()
    if system.startswith("darwin") or system.startswith("mac"):
        name = "executar_boletins_mac.ini"
    elif system.startswith("linux"):
        name = "executar_boletins_linux.ini"
    else:
        name = "executar_boletins_linux.ini"
    return Path(__file__).with_name(name)


def _load_config() -> dict:
    # prioridade: env CONFIG_PATH > arquivo padrão por SO
    cfg_path = _expand(os.environ.get("BOLETINS_CONFIG", str(_default_config_path())))

    cfg = configparser.ConfigParser()
    if cfg_path.exists():
        cfg.read(cfg_path)

    section = cfg["boletins"] if "boletins" in cfg else {}

    base_dir = os.environ.get("BOLETINS_BASE_DIR") or section.get("base_dir")
    kernel_name = os.environ.get("KERNEL_NAME") or section.get("kernel_name", "python3")

    if not base_dir:
        # fallback sem config
        system = platform.system().lower()
        base_dir = (
            "~/Library/CloudStorage/OneDrive-Pessoal/Python/Financas"
            if (system.startswith("darwin") or system.startswith("mac"))
            else "~/OneDrive/Python/Financas"
        )

    base_dir = _expand(base_dir)
    if not base_dir.exists():
        raise FileNotFoundError(
            "Diretorio base nao encontrado: "
            f"{base_dir} (config={cfg_path})"
        )

    return {"base_dir": base_dir, "kernel_name": kernel_name, "config_path": cfg_path}


def _build_notebook_list(base_dir: Path) -> list[Path]:
    return [
        base_dir / "00_Boletim_Diario/Setups_Diarios_B3.ipynb",
        base_dir / "00_Boletim_Diario/Setups_Diarios_Fix_v5.ipynb",
        base_dir / "00_Drawdown/drawdown_monitor.ipynb",
        base_dir / "00_MACD/MACD_diario_B3.ipynb",
        base_dir / "00_MACD/MACD_semanal_B3.ipynb",
        base_dir / "00_Rentatibilidade_Historica/rentabilidade_historica.ipynb",
    ]

def executar_notebooks(
    notebooks: Iterable[Path],
    *,
    kernel_name: str,
    verbose: bool = False,
    stop_on_error: bool = False,
) -> int:
    pm = _import_papermill()
    _validate_kernel(kernel_name)
    diretorio_original = os.getcwd()
    rc = 0

    for nb in notebooks:
        if not nb.exists():
            print(f"❌ Notebook não encontrado: {nb}")
            rc = 2
            continue

        dir_notebook = nb.parent
        if not dir_notebook.exists():
            print(f"❌ Diretório do notebook não existe: {dir_notebook}")
            rc = 2
            continue

        with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False) as tmp_nb:
            output_nb = Path(tmp_nb.name)

        print(f"▶ Executando: {nb.name}")
        print(f"  📁 Diretório: {dir_notebook}")

        try:
            os.chdir(dir_notebook)
            pm.execute_notebook(
                input_path=nb,
                output_path=output_nb,
                kernel_name=kernel_name,
                log_output=verbose,
            )
            print(f"✔ Concluído: {output_nb.name}\n")
        except Exception as e:
            print(f"❌ Erro ao executar {nb.name}: {e}\n")
            if verbose:
                print(traceback.format_exc())
            rc = 1
            if stop_on_error:
                return rc
        finally:
            try:
                output_nb.unlink(missing_ok=True)
            except Exception:
                pass
            os.chdir(diretorio_original)

    return rc


def main() -> int:
    _maybe_reexec_with_runner_python()

    parser = argparse.ArgumentParser(description="Executa uma lista fixa de notebooks via papermill.")
    parser.add_argument("--list", action="store_true", help="Lista os notebooks e sai sem executar.")
    parser.add_argument("--dry-run", action="store_true", help="Alias de --list.")
    parser.add_argument("--verbose", action="store_true", help="Mostra traceback e log de output das celulas.")
    parser.add_argument("--stop-on-error", action="store_true", help="Para na primeira falha.")
    args = parser.parse_args()

    try:
        cfg = _load_config()
    except Exception as e:
        print(f"❌ Falha ao carregar config/base_dir: {e}", file=sys.stderr)
        return 2

    base_dir: Path = cfg["base_dir"]
    kernel_name: str = cfg["kernel_name"]
    notebooks = _build_notebook_list(base_dir)

    if args.list or args.dry_run:
        for nb in notebooks:
            print(("OK  " if nb.exists() else "MISS") + f" {nb}")
        return 0
    try:
        return executar_notebooks(
            notebooks,
            kernel_name=kernel_name,
            verbose=args.verbose,
            stop_on_error=args.stop_on_error,
        )
    except (ModuleNotFoundError, RuntimeError) as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
