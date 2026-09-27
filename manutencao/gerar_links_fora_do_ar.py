"""Gera o .lycheeignore a partir dos links marcados como fora do ar nas páginas.

O link fora do ar continua no lugar dele, marcado com o aviso logo depois:

    - [título](endereço) · *fora do ar em 13/09/2026, 404* · [buscar cópia no
      Internet Archive](https://web.archive.org/web/*/endereço)

Não há lista separada desses links: o aviso na página é o único registro. Deste
aviso sai o endereço que o verificador semanal de links deve ignorar, para o
relatório mostrar só o que quebrou depois. O .lycheeignore é escrito por este
script, nunca à mão.

Uso:
    py manutencao/gerar_links_fora_do_ar.py             # regrava o .lycheeignore
    py manutencao/gerar_links_fora_do_ar.py --conferir  # só acusa desatualização
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
IGNORE = RAIZ / ".lycheeignore"

RE_ARCHIVE = re.compile(r"\[[^\]]*\]\((https://web\.archive\.org/web/\*/([^)]+))\)")
RE_AVISO = re.compile(r"\*((?:site )?fora do ar em \d{2}/\d{2}/\d{4})(?:, ([^*]+))?\*")


def coletar():
    """Endereço e página de cada link marcado, na ordem das páginas."""
    marcados = []
    for md in sorted(DOCS.rglob("*.md")):
        for linha in md.read_text(encoding="utf-8").split("\n"):
            arq = RE_ARCHIVE.search(linha)
            if arq and RE_AVISO.search(linha):
                marcados.append((arq.group(2), md))
    return marcados


def montar_ignore(marcados):
    linhas = ["web\\.archive\\.org"]
    linhas += sorted({f"^{re.escape(url)}$" for url, _ in marcados})
    return "\n".join(linhas) + "\n"


def main():
    marcados = coletar()
    ignore = montar_ignore(marcados)
    if "--conferir" in sys.argv:
        if not IGNORE.exists() or IGNORE.read_text(encoding="utf-8") != ignore:
            print(f"desatualizado: {IGNORE.name}")
            print("rode: py manutencao/gerar_links_fora_do_ar.py")
            return 1
        print(f"em dia, {len(marcados)} links marcados")
        return 0
    # newline explícito: sem isso o Windows grava CRLF e o diff vira ruído
    IGNORE.write_text(ignore, encoding="utf-8", newline="\n")
    paginas = len({md for _, md in marcados})
    print(f"{len(marcados)} links marcados em {paginas} páginas")
    print(f"gravado: {IGNORE.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
