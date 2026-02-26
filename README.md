# Financas

Repositorio pessoal para estudos, automacoes e relatorios de mercado (B3, NYSE, IBOV, S&P 500, BTC e estrategias quantitativas).

## Estrutura principal

- `00_Automacoes`: scripts de orquestracao e setup de ambiente.
  - `run_all.py`: executa a sequencia de scripts Python diarios/semanais e salva logs em `00_Automacoes/logs`.
  - `executar_boletins.py`: executa uma lista fixa de notebooks via `papermill`.
  - `setup_financas_env.sh`: prepara venv em `/tmp/financas-venv` com `papermill` e `ipykernel`.
- `00_Boletim_Diario`: geracao de boletins diarios (B3 e NYSE), notebooks e scripts.
- `00_Drawdown`: monitor de drawdown (script/notebook, caches e historico).
- `00_MACD`: monitoramentos MACD diario e semanal para B3.
- `00_Rentatibilidade_Historica`: notebook de rentabilidade historica e arquivos de apoio.
- `00_Relatorios`: saida principal dos PDFs diarios/semanais (boletins e relatorios).
- `01_*`: estudos/rotinas por estrategia (BB signal, NHNL, RSI, CGAR, BTC loan, etc.).
- `99_*`: analises exploratorias e estudos especiais.
- `Long_Short`: app Streamlit para consulta de operacoes Long & Short (com README proprio).
- `CORRIGIR`: area de testes, reescritas e versoes em correcao de estrategias antigas.
- `Relatorios`: pasta adicional com relatorios gerados em execucoes anteriores.

## Convencao de pastas

- `00_`: fluxos mais operacionais/recorrentes (automacoes e relatorios).
- `01_`: estrategias e monitores especificos.
- `99_`: estudos pontuais ou experimentais.
- `CORRIGIR`: material em revisao, refatoracao ou comparacao de versoes.

## Execucao rapida

1. Preparar ambiente (macOS/Linux):

```bash
bash 00_Automacoes/setup_financas_env.sh
```

2. Rodar orquestrador de scripts:

```bash
python3 00_Automacoes/run_all.py
```

3. Rodar notebooks via papermill:

```bash
python3 00_Automacoes/executar_boletins.py
```

Opcoes uteis:

- Listar notebooks sem executar: `python3 00_Automacoes/executar_boletins.py --list`
- Verbose + parar no primeiro erro: `python3 00_Automacoes/executar_boletins.py --verbose --stop-on-error`

## Observacoes

- Ha ambientes virtuais locais (`.venv`, `venv`) e caches em algumas subpastas.
- O projeto contem muitos arquivos de saida (`.pdf`, `.xlsx`, `.png`) gerados pelas rotinas.
- A configuracao padrao do `executar_boletins.py` no macOS usa `00_Automacoes/executar_boletins_mac.ini`.
