"""Monta a lista de páginas atualizadas recentemente a partir do histórico do Git.

O marcador <!-- ultimas-atualizacoes --> na página inicial é trocado pela lista.
Se o histórico não estiver disponível (clone raso, por exemplo), o marcador é
removido e a página fica sem a seção, em vez de quebrar a publicação.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

MARCADOR = "<!-- ultimas-atualizacoes -->"
QUANTIDADE = 8
RAIZ = Path(__file__).resolve().parent.parent


def _datas_do_git():
    """Data do último commit de cada página, da mais recente para a mais antiga."""
    try:
        saida = subprocess.run(
            ["git", "-C", str(RAIZ), "log", "--date=short",
             "--pretty=format:%ad", "--name-only", "--", "docs"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if saida.returncode != 0:
        return {}
    datas, data = {}, None
    for linha in saida.stdout.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", linha):
            data = linha
        elif linha.endswith(".md") and linha not in datas:
            datas[linha] = data
    return datas


def _titulo(caminho):
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.startswith("# "):
            return linha[2:].strip()
    return caminho.stem


def on_page_markdown(markdown, page, config, files):
    if MARCADOR not in markdown:
        return markdown
    itens = []
    for relativo, data in _datas_do_git().items():
        caminho = RAIZ / relativo
        if not caminho.exists() or caminho.name == "index.md":
            continue
        destino = relativo[len("docs/"):]
        dia = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        itens.append(f"- [{_titulo(caminho)}]({destino}): {dia}")
        if len(itens) == QUANTIDADE:
            break
    if not itens:
        return markdown.replace(MARCADOR, "")
    return markdown.replace(MARCADOR, "## Últimas atualizações\n\n" + "\n".join(itens))
