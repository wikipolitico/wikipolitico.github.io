"""Monta a lista "Por onde começar" a partir das entradas marcadas com estrela.

A marca fica na própria entrada do veículo, que é a fonte da verdade:

    - ⭐ **Carta Capital** — revista semanal. [Site](...) · [Facebook](...)

O bloco entre <!-- destaques:inicio --> e <!-- destaques:fim --> sai do texto da
página, e o marcador <!-- destaques:lista --> é trocado pela lista gerada. Assim
o destaque não duplica o link: repetir a entrada criaria dois lugares para
atualizar e um para envelhecer.

Sem nenhuma entrada marcada, o bloco inteiro é removido, em vez de deixar um
título com nada embaixo.
"""

import re

INICIO = "<!-- destaques:inicio -->"
LISTA = "<!-- destaques:lista -->"
FIM = "<!-- destaques:fim -->"

# - ⭐ **Nome** — resto    ou    - ⭐ [Nome](url) · resto
RE_ENTRADA = re.compile(r"^- ⭐ (?:\*\*(?P<negrito>[^*]+)\*\*|\[(?P<rotulo>[^\]]+)\]\((?P<url>[^)]+)\))")
RE_PRIMEIRO_LINK = re.compile(r"\[[^\]]*\]\((?P<url>https?://[^)]+)\)")


def _destaques(markdown):
    """Nome e endereço de cada entrada marcada, na ordem em que aparecem."""
    itens = []
    for linha in markdown.split("\n"):
        m = RE_ENTRADA.match(linha)
        if not m:
            continue
        nome = m.group("negrito") or m.group("rotulo")
        url = m.group("url")
        if not url:
            link = RE_PRIMEIRO_LINK.search(linha[m.end():])
            url = link.group("url") if link else ""
        itens.append(f"- [{nome.strip()}]({url})" if url else f"- {nome.strip()}")
    return itens


def on_page_markdown(markdown, page, config, files):
    if INICIO not in markdown or FIM not in markdown:
        return markdown
    itens = _destaques(markdown)
    if not itens:
        return re.sub(re.escape(INICIO) + r".*?" + re.escape(FIM) + r"\n*", "",
                      markdown, flags=re.DOTALL)
    return (markdown
            .replace(LISTA, "\n".join(itens))
            .replace(INICIO + "\n", "")
            .replace(FIM + "\n", ""))
