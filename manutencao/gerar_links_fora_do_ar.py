"""Gera a lista consolidada de links fora do ar e o .lycheeignore.

A fonte da verdade é o aviso na própria página, junto do link:

    - [título](endereço) · *fora do ar em 13/09/2026, 404* · [buscar cópia no
      Internet Archive](https://web.archive.org/web/*/endereço)

Deste aviso saem o endereço, a data e o motivo. Os dois arquivos derivados são
escritos por este script, nunca à mão: escrever o mesmo fato em três lugares foi
o que fez a lista divergir das páginas antes.

Uso:
    py manutencao/gerar_links_fora_do_ar.py             # regrava os dois arquivos
    py manutencao/gerar_links_fora_do_ar.py --conferir  # só acusa desatualização
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
LISTA = RAIZ / "manutencao" / "links-fora-do-ar.md"
IGNORE = RAIZ / ".lycheeignore"

RE_ARCHIVE = re.compile(r"\[[^\]]*\]\((https://web\.archive\.org/web/\*/([^)]+))\)")
RE_AVISO = re.compile(r"\*((?:site )?fora do ar em \d{2}/\d{2}/\d{4})(?:, ([^*]+))?\*")
RE_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)]+)\)")
RE_SUBTITULO = re.compile(r"#{2,4}\s+(.+)")
RE_NEGRITO = re.compile(r"\*\*([^*]+)\*\*")

CABECALHO = """# Links fora do ar

Lista gerada por `manutencao/gerar_links_fora_do_ar.py` a partir dos avisos das
próprias páginas. **Não edite este arquivo à mão**: corrija o aviso na página e
rode o script, que regrava esta lista e o `.lycheeignore`.

Os links continuam no site, marcados como fora do ar e com atalho para buscar a
cópia no Internet Archive. Ao recuperar um link, troque o endereço na página e
retire o aviso; o script cuida do resto.
"""


def _titulo_da_pagina(caminho, linhas):
    for linha in linhas:
        if linha.startswith("# "):
            return linha[2:].strip()
    return caminho.stem


def _titulo_do_item(linha, url):
    """Como o link morto se chama, do jeito mais informativo que a linha permita."""
    titulo = next((t for t, u in RE_LINK.findall(linha) if u == url), "")
    if not titulo:
        titulo = next((t for t, u in RE_LINK.findall(linha)
                       if "web.archive.org" not in u), url)
    # em entrada de veículo o texto do link pode ser genérico
    # ("canal antigo no YouTube"), então o nome em negrito vem junto
    negrito = RE_NEGRITO.search(linha)
    if negrito and negrito.group(1).strip() not in titulo:
        titulo = f"{negrito.group(1).strip()}: {titulo}"
    return titulo.strip()


def _registro(linha, pagina, secao):
    arq = RE_ARCHIVE.search(linha)
    aviso = RE_AVISO.search(linha)
    if not arq or not aviso:
        return None
    return {
        "pagina": pagina,
        "secao": secao,
        "titulo": _titulo_do_item(linha, arq.group(2)),
        "url": arq.group(2),
        "quando": aviso.group(1),
        "motivo": (aviso.group(2) or "").strip(),
        "archive": arq.group(1),
    }


def coletar():
    """Um registro por link marcado, na ordem das páginas."""
    registros = []
    for md in sorted(DOCS.rglob("*.md")):
        linhas = md.read_text(encoding="utf-8").split("\n")
        pagina = _titulo_da_pagina(md, linhas)
        secao = ""
        for linha in linhas:
            cabecalho = RE_SUBTITULO.match(linha)
            if cabecalho:
                secao = cabecalho.group(1).strip()
                continue
            registro = _registro(linha, pagina, secao)
            if registro:
                registros.append(registro)
    return registros


def montar_lista(registros):
    por_pagina = {}
    for r in registros:
        por_pagina.setdefault(r["pagina"], []).append(r)
    partes = [CABECALHO]
    for pagina, itens in por_pagina.items():
        partes.append(f"\n## {pagina} ({len(itens)})\n")
        for r in itens:
            prefixo = f"*{r['secao']}* · " if r["secao"] else ""
            motivo = f"{r['motivo']} · " if r["motivo"] else ""
            partes.append(f"- {prefixo}[{r['titulo']}]({r['url']}) · {motivo}"
                          f"[Internet Archive]({r['archive']})")
    return "\n".join(partes) + "\n"


def montar_ignore(registros):
    linhas = ["web\\.archive\\.org"]
    linhas += sorted({f"^{re.escape(r['url'])}$" for r in registros})
    return "\n".join(linhas) + "\n"


def main():
    registros = coletar()
    lista, ignore = montar_lista(registros), montar_ignore(registros)
    if "--conferir" in sys.argv:
        desatualizados = [
            arq.name for arq, novo in ((LISTA, lista), (IGNORE, ignore))
            if not arq.exists() or arq.read_text(encoding="utf-8") != novo
        ]
        if desatualizados:
            print("desatualizado: " + ", ".join(desatualizados))
            print("rode: py manutencao/gerar_links_fora_do_ar.py")
            return 1
        print(f"em dia, {len(registros)} links marcados")
        return 0
    # newline explícito: sem isso o Windows grava CRLF e o diff vira ruído
    LISTA.write_text(lista, encoding="utf-8", newline="\n")
    IGNORE.write_text(ignore, encoding="utf-8", newline="\n")
    paginas = len({r["pagina"] for r in registros})
    print(f"{len(registros)} links marcados em {paginas} páginas")
    print(f"gravados: {LISTA.relative_to(RAIZ)} e {IGNORE.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
