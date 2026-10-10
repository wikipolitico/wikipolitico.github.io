"""Monta a Linha do tempo a partir dos itens datados de todas as páginas.

O marcador <!-- linha-do-tempo --> na página linha-do-tempo.md é trocado pela
lista. Entram os itens de lista que começam com a data em negrito, no padrão das
páginas:

    - **DD/MM/AAAA — título:** texto
    - **DD/MM/AAAA:** texto
    - **DD/MM/AAAA (STF):** texto

Cada item vira uma linha com a data, a página de origem (com link para a seção
onde ele está) e o título, ou o começo do texto quando não há título. Nada é
escrito à mão: o que entra numa página entra na linha do tempo no build seguinte.
"""

import re
from collections import defaultdict
from pathlib import Path

from markdown.extensions.toc import slugify, unique

MARCADOR = "<!-- linha-do-tempo -->"
DOCS = Path(__file__).resolve().parent.parent / "docs"
IGNORAR = {"index.md", "linha-do-tempo.md"}

RE_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
RE_ITEM = re.compile(
    r"^- \*\*(\d{2})/(\d{2})/(\d{4})"           # data
    r"(?:\s*\(([^)]*)\))?"                       # (STF), (TSE)...
    r"(?:\s*[—–-]\s*(.*?))?"                     # — título
    r":?\*\*:?\s*(.*)$"                          # resto do texto
)
RE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
RE_FONTE = re.compile(r"\s*\(\[[^\]]*\]\([^)]*\)(?:[;,]\s*\[[^\]]*\]\([^)]*\))*\)")
LIMITE = 170


def _limpar(texto):
    texto = RE_FONTE.sub("", texto)
    texto = RE_LINK.sub(r"\1", texto)
    texto = texto.replace("**", "").replace("*", "").strip()
    return texto.rstrip(":").strip()


def _resumo(texto):
    texto = _limpar(texto)
    corte = re.search(r"(?<=[a-zà-ú0-9\"”)])\.\s", texto)
    if corte and corte.start() < LIMITE:
        texto = texto[: corte.start()]
    elif len(texto) > LIMITE:
        texto = texto[:LIMITE].rsplit(" ", 1)[0] + "…"
    return texto


def _coletar():
    itens = []
    for md in sorted(DOCS.rglob("*.md")):
        relativo = md.relative_to(DOCS).as_posix()
        if relativo in IGNORAR:
            continue
        titulo_pagina, ancora, ids = md.stem, "", set()
        for linha in md.read_text(encoding="utf-8").splitlines():
            m = RE_TITULO.match(linha)
            if m:
                texto = _limpar(m.group(2))
                slug = unique(slugify(texto, "-"), ids)
                if m.group(1) == "#":
                    titulo_pagina = texto
                else:
                    ancora = slug
                continue
            m = RE_ITEM.match(linha)
            if not m:
                continue
            dia, mes, ano, orgao, titulo, resto = m.groups()
            if not (1 <= int(dia) <= 31 and 1 <= int(mes) <= 12):
                continue
            frase = _limpar(titulo) if titulo else _resumo(resto)
            if orgao:
                frase = f"({orgao}) {frase}"
            destino = relativo + (f"#{ancora}" if ancora else "")
            itens.append((int(ano), int(mes), int(dia), titulo_pagina, destino, frase))
    return itens


def on_page_markdown(markdown, page, config, files):
    if MARCADOR not in markdown:
        return markdown
    itens = _coletar()
    por_ano = defaultdict(list)
    for item in itens:
        por_ano[item[0]].append(item)
    paginas = len({i[4].split("#")[0] for i in itens})
    partes = [f"São {len(itens)} fatos datados de {paginas} páginas, dos mais recentes aos mais antigos."]
    for ano in sorted(por_ano, reverse=True):
        partes.append(f"\n## {ano}\n")
        for a, m, d, pagina, destino, frase in sorted(por_ano[ano], key=lambda i: (-i[1], -i[2], i[3])):
            partes.append(f"- **{d:02d}/{m:02d}/{a}** · [{pagina}]({destino}): {frase}")
    return markdown.replace(MARCADOR, "\n".join(partes))
