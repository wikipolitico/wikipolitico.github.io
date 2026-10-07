"""Liga as menções a termos importantes às páginas próprias deles.

Regra do site (AGENTS.md): toda menção a um termo que tem página própria
(mensalão, Lava Jato, 8 de janeiro, caso Master, os ministros do STF, as
eleições e os outros da lista TERMOS) leva link para essa página. Na prática,
o script liga a primeira menção de cada seção. As seguintes, na mesma seção,
ficam sem link para o texto não virar um mar de azul, e a seção que já tem
link para a página do termo fica como está.

A caixa Resumo também recebe os links (decisão do usuário em 28/09/2026: ela
continua sem links de fonte, mas os termos com página própria são ligados).
Ficam de fora a própria página do termo, os títulos, o texto e o endereço de
links que já existem e o título em negrito dos itens de linha do tempo.

Uso:
    py manutencao/linkar_termos.py            # lista o que falta ligar
    py manutencao/linkar_termos.py --aplicar  # grava os links
"""
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

ANOS_ELEICAO = ["1989", "1994", "1998", "2002", "2006", "2010", "2014", "2018", "2022", "2026"]

# (expressão, página de destino relativa a docs/, âncora)
TERMOS = [
    (r"[Mm]ensal[ãa]o(?: (?:tucano|mineiro))?", "temas/farsa-do-mensalao.md", ""),
    (r"(?:Operação )?[Ll]ava[- ][Jj]ato", "temas/farsa-da-lava-jato.md", ""),
    (r"8 de [Jj]aneiro", "temas/8-de-janeiro.md", ""),
    (r"(?:[Cc]aso|Banco) Master", "temas/banco-master.md", ""),
    (r"Lulinha", "temas/caso-lulinha.md", ""),
    (r"(?:escândalo|fraudes?|roubo|farra) (?:do|no|nos|dos|das aposentadorias do) INSS"
     r"|Operação Sem Desconto", "temas/escandalo-do-inss.md", ""),
    (r"[Ff]ila do INSS", "temas/fila-do-inss.md", ""),
    (r"Hondurasgate", "temas/hondurasgate.md", ""),
    (r"(?<!Instituto )[Ll]awfare(?!:)", "temas/lawfare.md", ""),
    (r"CPMI das Fake News", "temas/cpmi-das-fake-news-2020.md", ""),
    (r"ditadura militar|golpe (?:militar )?de (?:19)?64", "temas/ditadura-militar-de-64.md", ""),
    (r"(?:Donald )?Trump", "temas/donald-trump.md", ""),
    (r"(?:Nicolás )?Maduro", "temas/maduro-e-a-venezuela.md", ""),
    (r"[Cc]orrupção no governo Bolsonaro", "temas/corrupcao-no-governo-bolsonaro.md", ""),
    (r"Estado laico", "temas/bolsonarismo-contra-o-estado-laico.md", ""),
    (r"Nossa Senhora Aparecida", "temas/bolsonarismo-contra-o-estado-laico.md",
     "#nossa-senhora-aparecida-na-campanha-de-2026"),
    (r"Flávio Bolsonaro", "temas/flavio-bolsonaro.md", ""),
    (r"Jones Manoel", "temas/jones-manoel.md", ""),
    # Ministros e ex-ministros do STF. Parentes com o mesmo sobrenome (a mulher de Moraes,
    # os filhos de Fux, a mulher de Zanin) e homônimos ficam de fora pelas exclusões.
    (r"Gilmar(?: Mendes)?", "temas/stf/gilmar-mendes.md", ""),
    (r"C[áa]rmen L[úu]cia", "temas/stf/carmen-lucia.md", ""),
    (r"(?:Dias )?Toffoli", "temas/stf/dias-toffoli.md", ""),
    (r"(?<!Rodrigo )(?<!Marianna )(?:Luiz )?Fux", "temas/stf/luiz-fux.md", ""),
    (r"(?:Edson )?Fachin", "temas/stf/edson-fachin.md", ""),
    (r"(?<!Vinicius de )(?<!Machado de )(?<!Barci de )(?:Alexandre de )?Moraes(?! Neto| Mourão)",
     "temas/stf/alexandre-de-moraes.md", ""),
    (r"(?:Kassio )?Nunes Marques|Kassio", "temas/stf/kassio-nunes-marques.md", ""),
    (r"(?<!Duda )(?<!Danielle )(?:André )?Mendonça(?! (?:de Barros|Filho))", "temas/stf/andre-mendonca.md", ""),
    (r"(?<!Teixeira )(?:Cristiano )?Zanin", "temas/stf/cristiano-zanin.md", ""),
    (r"(?:Flávio )?Dino", "temas/stf/flavio-dino.md", ""),
    (r"Celso de Mello", "temas/stf/celso-de-mello.md", ""),
    (r"Joaquim Barbosa", "temas/stf/joaquim-barbosa.md", ""),
    (r"(?:Ricardo )?Lewandowski", "temas/stf/ricardo-lewandowski.md", ""),
    (r"Rosa Weber", "temas/stf/rosa-weber.md", ""),
    (r"Teori(?: Zavascki)?", "temas/stf/teori-zavascki.md", ""),
    (r"(?:Luís Roberto )?Barroso", "temas/stf/luis-roberto-barroso.md", ""),
] + [
    (rf"[Ee]lei(?:ção|ções) (?:presidencia(?:l|is) )?(?:de )?{ano}", f"temas/eleicoes-{ano}.md", "")
    for ano in ANOS_ELEICAO
]

COMPILADOS = [(re.compile(rf"(?<![\w-])(?:{exp})(?![\w-])"), destino, ancora)
              for exp, destino, ancora in TERMOS]

RE_TITULO = re.compile(r"^#{1,6}\s")
RE_URL = re.compile(r"<?https?://[^\s)>\]]+>?")
RE_CODIGO = re.compile(r"`[^`]*`")
RE_HTML = re.compile(r"<[^>]+>")
RE_NEGRITO_ITEM = re.compile(r"^\s*[-*]\s+\*\*.*?\*\*")


def links(linha):
    """Trechos [texto](endereço) da linha, com colchetes aninhados: (início, fim, endereço)."""
    achados, i = [], 0
    while i < len(linha):
        if linha[i] == "[":
            prof, j = 0, i
            while j < len(linha):
                if linha[j] == "[":
                    prof += 1
                elif linha[j] == "]":
                    prof -= 1
                    if prof == 0:
                        break
                j += 1
            if j < len(linha) - 1 and linha[j + 1] == "(":
                prof, k = 0, j + 1
                while k < len(linha):
                    if linha[k] == "(":
                        prof += 1
                    elif linha[k] == ")":
                        prof -= 1
                        if prof == 0:
                            break
                    k += 1
                achados.append((i, k + 1, linha[j + 2:k]))
                i = k + 1
                continue
        i += 1
    return achados


def bloqueados(linha):
    trechos = [(a, b) for a, b, _ in links(linha)]
    for exp in (RE_URL, RE_CODIGO, RE_HTML):
        trechos += [m.span() for m in exp.finditer(linha)]
    m = RE_NEGRITO_ITEM.match(linha)
    if m:
        trechos.append(m.span())
    return trechos


def destino_do_link(endereco, arquivo):
    """Caminho do link, relativo a docs/, sem âncora; None se for externo."""
    endereco = endereco.split()[0].split("#")[0] if endereco.strip() else ""
    if not endereco or re.match(r"[a-z]+:", endereco):
        return None
    alvo = (arquivo.parent / endereco).resolve()
    try:
        return alvo.relative_to(DOCS.resolve()).as_posix()
    except ValueError:
        return None


def secoes(linhas):
    """Divide o arquivo em seções pelos títulos: listas de índices de linha."""
    atual, todas = [], []
    for i, linha in enumerate(linhas):
        if RE_TITULO.match(linha):
            todas.append(atual)
            atual = []
        else:
            atual.append(i)
    todas.append(atual)
    return todas


def processar(arquivo):
    rel = arquivo.relative_to(DOCS).as_posix()
    linhas = arquivo.read_text(encoding="utf-8").split("\n")
    cerca = False
    ignorar = set()
    for i, linha in enumerate(linhas):
        if linha.lstrip().startswith("```"):
            cerca = not cerca
            ignorar.add(i)
        elif cerca:
            ignorar.add(i)
    feitos = []
    for secao in secoes(linhas):
        ja_ligados = set()
        for i in secao:
            for _, _, endereco in links(linhas[i]):
                dest = destino_do_link(endereco, arquivo)
                if dest:
                    ja_ligados.add(dest)
        for exp, destino, ancora in COMPILADOS:
            if destino == rel or destino in ja_ligados:
                continue
            for i in secao:
                if i in ignorar:
                    continue
                linha = linhas[i]
                trechos = bloqueados(linha)
                achou = next((m for m in exp.finditer(linha)
                              if not any(a < m.end() and m.start() < b for a, b in trechos)), None)
                if not achou:
                    continue
                caminho = os.path.relpath(DOCS / destino, arquivo.parent).replace("\\", "/")
                texto = achou.group(0)
                linhas[i] = f"{linha[:achou.start()]}[{texto}]({caminho}{ancora}){linha[achou.end():]}"
                ja_ligados.add(destino)
                feitos.append((i + 1, texto, destino))
                break
    return linhas, feitos


def main():
    aplicar = "--aplicar" in sys.argv
    total = 0
    for arquivo in sorted(DOCS.rglob("*.md")):
        linhas, feitos = processar(arquivo)
        if not feitos:
            continue
        total += len(feitos)
        print(f"{arquivo.relative_to(RAIZ).as_posix()}: {len(feitos)}")
        for n, texto, destino in feitos:
            print(f"    linha {n}: {texto} -> {destino}")
        if aplicar:
            arquivo.write_text("\n".join(linhas), encoding="utf-8", newline="\n")
    verbo = "ligadas" if aplicar else "sem link"
    print(f"{total} menções {verbo}")


if __name__ == "__main__":
    main()
