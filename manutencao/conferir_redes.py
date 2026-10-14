"""Confere os perfis de rede social das páginas, que o lychee não consegue checar.

O lychee valida pelo código HTTP, e algumas redes respondem 200 para qualquer
endereço, inclusive perfil que nunca existiu. Aqui cada rede é checada pelo
método que funciona nela:

  bluesky    API pública do Bluesky (getProfile); 200 existe, 400 não existe
  youtube    código HTTP; canal removido dá 404
  telegram   o HTML tem "tgme_page_title" quando o canal existe e é visível de
             onde se checa; sem o título, fica inconclusivo, porque a mesma
             casca aparece para canal inexistente e para canal restrito na
             região — o t.me/rtnews responde do Brasil e não responde na CI
  sites      o título da home tem que combinar com o nome do veículo: código 200
             não prova continuidade, porque domínio expirado é comprado por
             site de apostas e responde igual
  mastodon   código HTTP
  x          consultado como o robô de prévia de link do Facebook, o X mostra o
             nome do dono no og:title e responde 404 para perfil inexistente
  facebook,  consultados como o mesmo robô, mostram o nome do dono no og:title;
  instagram, sem ele, a resposta genérica é a mesma para perfil inexistente e
  tiktok     para consulta bloqueada, então vale como inconclusiva, nunca como
             prova de que o perfil caiu; depois de umas centenas de consultas
             seguidas, o Facebook passa a mandar para o login, e o resto da
             rodada fica inconclusivo

Na página "Além da grande mídia", o nome do dono é comparado com o nome da
entrada, porque perfil abandonado é tomado por outra pessoa e continua
respondendo: o @JucaKfouri virou conta de divulgação de acompanhantes. Conta do
X sem bio e com menos de mil seguidores também vai para conferência humana,
porque é o retrato de quem pegou o nome de usuário depois.

Link já marcado como fora do ar não é conferido de novo.

O código de saída é 1 só quando há queda comprovada. Inconclusivo e dono a
conferir não derrubam a verificação, para não encher o relatório de falso
positivo.

Uso:
    py manutencao/conferir_redes.py            # confere tudo e lista o que caiu
    py manutencao/conferir_redes.py --quieto    # só o resumo e o código de saída
"""
import concurrent.futures
import html
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

# ramos que costumam comprar domínio de veículo expirado
SEQUESTRO = re.compile(r"\b(casino|cassino|apostas|apuestas|bet|bets|slots?|"
                       r"cbd|viagra|farmacia|pharmacy|clinic)\b|"
                       r"(domínio à venda|domain for sale|this domain)", re.I)

CURL = "curl.exe" if os.name == "nt" else "curl"

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
VITRINE = DOCS / "alem-da-grande-midia.md"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# com o navegador, Facebook dá 400 e X e TikTok dão 403; o robô de prévia de
# link do Facebook recebe o og:title com o nome do dono do perfil
ROBO = "facebookexternalhit/1.1"
BLUESKY_API = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor="

RX_LINK =re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
RX_ARQUIVO = re.compile(r"\(https://web\.archive\.org/web/\*/([^)\s]+)\)")
SEM_CHECAGEM = ("web.archive.org",)
# primeiro segmento que não é perfil: vídeo, post, busca, compartilhamento
NAO_E_PERFIL = {"watch", "share", "share.php", "sharer.php", "photo", "photo.php", "story.php",
                "permalink.php", "video.php", "groups", "events", "hashtag", "intent",
                "search", "home", "i"}
# títulos que o site devolve quando não mostra perfil nenhum
GENERICO = re.compile(r"^(facebook|instagram|x|tiktok.*|visit[ea]? (o )?tiktok.*)$", re.I)
# texto de link que é só o nome da rede e não diz de quem é o perfil
ROTULOS = {"x", "facebook", "instagram", "tiktok", "youtube", "site", "bluesky",
           "telegram", "threads"}
PERFIL_POR_HOST = {"instagram.com": "instagram", "facebook.com": "facebook",
                   "twitter.com": "x", "x.com": "x", "mobile.twitter.com": "x",
                   "tiktok.com": "tiktok"}


def rede_de(url):
    caminho = urlparse(url).path
    h = urlparse(url).netloc.lower().removeprefix("www.").removeprefix("m.")
    if h == "bsky.app":
        return "bluesky"
    if h.endswith("youtube.com"):
        # só canal e perfil; link de vídeo o lychee já confere pelo código HTTP
        return "youtube" if re.search(r"/(channel|user|c)/|/@", caminho) else None
    if h == "t.me":
        return "telegram"
    if "mastodon" in h:
        return "mastodon" if re.search(r"/@[A-Za-z0-9._]+$", url) else None
    return rede_de_perfil(h, [p for p in caminho.split("/") if p])


def rede_de_perfil(host, partes):
    """Instagram, Facebook, X e TikTok: só perfil; /p/, /reel/, /status/ e /videos/ são publicação."""
    rede = PERFIL_POR_HOST.get(host)
    if not rede or len(partes) != 1 or partes[0].lower() in NAO_E_PERFIL:
        return None
    if rede == "tiktok" and not partes[0].startswith("@"):
        return None
    return rede


def curl(url, so_codigo=False, ua=UA):
    cmd = [CURL, "-sL", "-m", "30", "--compressed", "-A", ua]
    cmd += ["-o", "/dev/null", "-w", "%{http_code}"] if so_codigo else []
    try:
        r = subprocess.run(cmd + [url], capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return ""


def curl_com_codigo(url, ua):
    """Corpo, código HTTP e endereço final numa consulta só."""
    cmd = [CURL, "-sL", "-m", "30", "--compressed", "-A", ua,
           "-w", "\n@@%{http_code} %{url_effective}", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "", "", ""
    corpo, _, fim = r.stdout.decode("utf-8", "replace").rpartition("\n@@")
    codigo, _, final = fim.partition(" ")
    return corpo, codigo, final


def meta(corpo, prop):
    m = re.search(r'<meta[^>]+property="%s"[^>]+content="([^"]*)"' % prop, corpo)
    return html.unescape(m.group(1)).strip() if m else ""


def dono_do_titulo(rede, titulo):
    """O nome do dono, tirado do og:title de cada rede."""
    if rede in ("x", "instagram"):  # "Nome (@usuario) on X", "Nome (@usuario) • Instagram ..."
        return titulo.split(" (@")[0]
    if rede == "tiktok":  # "Nome on TikTok"
        return re.sub(r" (on|no) TikTok$", "", titulo)
    return titulo


def poucos_seguidores(descricao):
    """Conta do X sem bio: o X preenche a descrição com "N followers · ... Joined"."""
    m = re.match(r"([\d.,]+)([KM]?) followers · .*Joined", descricao)
    if not m:
        return None
    n = float(m.group(1).replace(",", "")) * {"": 1, "K": 1e3, "M": 1e6}[m.group(2)]
    return int(n) if n < 1000 else None


def _palavras(s):
    return {_normal(p) for p in re.split(r"\W+", s) if len(_normal(p)) >= 5}


def compativel(nome, dono):
    """Nome da entrada e nome do dono têm alguma coisa em comum?

    Prefixo de 8 letras ou uma palavra de 5 ou mais: "Ultrajano" bate com
    "José Trajano", e "Juca Kfouri" não bate com "Juca Moreno".
    """
    a, b = _normal(nome), _normal(dono)
    if len(b) < 4 or a[:8] in b or b[:8] in a:
        return True
    return any(p in b for p in _palavras(nome)) or any(p in a for p in _palavras(dono))


def pelo_robo(url, rede, nomes):
    """Facebook, Instagram, TikTok e X, consultados como o robô de prévia de link."""
    if rede == "x":
        url = "https://x.com/" + [p for p in urlparse(url).path.split("/") if p][0]
    corpo, codigo, final = curl_com_codigo(url, ROBO)
    if rede == "x" and codigo == "404":
        return False, "perfil não encontrado no X", None
    if "/login" in final:
        # depois de umas centenas de consultas seguidas o Facebook manda o
        # robô para o login; é limite de consultas, não perfil apagado
        return None, "a rede pediu login, limite de consultas", None
    titulo = meta(corpo, "og:title")
    if not titulo or GENERICO.match(titulo):
        return None, f"resposta genérica (HTTP {codigo or 'sem resposta'}), inconclusivo", None
    dono = dono_do_titulo(rede, titulo)
    # siglas curtas (MST, CUT) e rótulos de rede não servem de comparação
    nomes = [n for n in nomes if len(_normal(n)) >= 4 and _normal(n) not in ROTULOS]
    alerta = None
    if nomes and not any(compativel(n, dono) for n in nomes):
        alerta = f"o dono é {dono!r}, não {nomes[0]!r}"
    elif rede == "x" and (n := poucos_seguidores(meta(corpo, "og:description"))) is not None:
        alerta = f"conta sem bio, com {n} seguidores"
    return True, f"dono: {dono[:60]}", alerta


def checar(item):
    url, rede, nomes = item
    if rede in ("x", "facebook", "instagram", "tiktok"):
        ok, detalhe, alerta = pelo_robo(url, rede, nomes)
        return url, rede, ok, detalhe, alerta
    return checar_outras(url, rede) + (None,)


def checar_outras(url, rede):
    if rede == "bluesky":
        alvo = urlparse(url).path.split("/profile/")[-1].strip("/")
        codigo = curl(BLUESKY_API + alvo, so_codigo=True)
        return url, rede, codigo == "200", f"getProfile {codigo or 'sem resposta'}"
    if rede in ("youtube", "mastodon"):
        codigo = curl(url, so_codigo=True)
        if codigo == "429":  # limite de requisições nosso, não queda do perfil
            return url, rede, None, "HTTP 429, limite de requisições"
        return url, rede, codigo.startswith("2"), f"HTTP {codigo or 'sem resposta'}"
    # só o Telegram chega aqui
    if "tgme_page_title" in curl(url):
        return url, rede, True, "tem título de canal"
    # ausência de título não prova queda: o Telegram devolve a mesma casca
    # para canal inexistente e para canal restrito na região de quem checa.
    # t.me/rtnews, por exemplo, responde aqui e não responde no runner da CI.
    return url, rede, None, "sem título de canal, inexistente ou restrito na região"


def sites_dos_veiculos():
    """Pares (nome do veículo, site) das entradas que têm nome em negrito."""
    pares = []
    for md in sorted(DOCS.rglob("*.md")):
        for linha in md.read_text(encoding="utf-8").split("\n"):
            if not linha.startswith("- "):
                continue
            nome = re.search(r"\*\*([^*]+)\*\*", linha)
            site = re.search(r"\[Site\]\((https?://[^)]+)\)", linha)
            if nome and site:
                pares.append((nome.group(1).strip(), site.group(1)))
    return pares


def _normal(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def dono_mudou(par):
    """Se o título da home não tem nada a ver com o nome, o domínio pode ter trocado de dono.

    Código 200 não prova continuidade: domínio de veículo que expira costuma ser
    comprado por site de apostas ou farmácia, e responde 200 como qualquer outro.
    """
    nome, url = par
    corpo = curl(url)
    m = re.search(r"<title[^>]*>([^<]{0,140})", corpo)
    t = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    if not t:
        return nome, url, None, "sem título"
    if SEQUESTRO.search(t):
        return nome, url, False, f"título de outro ramo: {t[:70]}"
    if _normal(nome)[:8] in _normal(t) or _normal(t)[:8] in _normal(nome):
        return nome, url, True, t[:70]
    return nome, url, None, f"nome não bate: {t[:70]}"


def nome_da_entrada(linha):
    """Nome do veículo ou da pessoa numa entrada da vitrine: o negrito ou o primeiro link."""
    m = re.match(r"- (?:⭐ )?(?:\*\*([^*]+)\*\*|\[([^\]]+)\])", linha)
    return (m.group(1) or m.group(2)).strip() if m else None


def coletar():
    """Perfis a conferir, com os nomes contra os quais comparar o dono."""
    vistos, itens, marcados = set(), [], 0
    for md in sorted(DOCS.rglob("*.md")):
        for linha in md.read_text(encoding="utf-8").split("\n"):
            novos, ja_fora = perfis_da_linha(linha, md == VITRINE, vistos)
            itens += novos
            marcados += ja_fora
    return itens, marcados


def perfis_da_linha(linha, na_vitrine, vistos):
    """Perfis ainda não vistos na linha e quantos deles já estão marcados como fora do ar."""
    marcados = set(RX_ARQUIVO.findall(linha))
    entrada = nome_da_entrada(linha) if na_vitrine else None
    itens, ja_fora = [], 0
    for texto, url in RX_LINK.findall(linha):
        if url in vistos or any(d in url for d in SEM_CHECAGEM):
            continue
        vistos.add(url)
        rede = rede_de(url)
        if not rede:
            continue
        if url in marcados:
            ja_fora += 1
        else:
            # o texto do link também vale: "João Pedro Stédile no X" na entrada do MST
            itens.append((url, rede, (entrada, texto) if entrada else ()))
    return itens, ja_fora


def listar(titulo, linhas):
    print(f"\n=== {titulo} ({len(linhas)}) ===")
    for rede, url, *detalhe in sorted(linhas):
        print(f"  {rede:<9} {url}" + "".join(f"\n            {d}" for d in detalhe))


def main():
    quieto = "--quieto" in sys.argv
    itens, marcados = coletar()
    if not quieto:
        print(f"conferindo {len(itens)} perfis; {marcados} já marcados como fora do ar "
              f"ficam de fora\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(checar, itens))
    no_ar = [(rede, url) for url, rede, ok, _, _ in resultados if ok]
    caidos = [(rede, url, detalhe) for url, rede, ok, detalhe, _ in resultados if ok is False]
    inconclusivos = [(rede, url, detalhe) for url, rede, ok, detalhe, _ in resultados if ok is None]
    alertas = [(rede, url, alerta) for url, rede, _, _, alerta in resultados if alerta]
    if not quieto:
        for rede, url in no_ar:
            print(f"  ok       {rede:<9} {url}")
    print(f"\n{len(no_ar)} no ar · {len(caidos)} fora do ar · "
          f"{len(inconclusivos)} inconclusivos, de {len(itens)} perfis · "
          f"{len(alertas)} com dono a conferir")
    if caidos:
        listar("fora do ar", caidos)
    if alertas:
        listar("dono a conferir, pode ser conta tomada por outra pessoa", alertas)
    if inconclusivos and not quieto:
        listar("inconclusivos, exigem conferência humana", inconclusivos)
    return relatar_sites(quieto) or (1 if caidos else 0)


def relatar_sites(quieto):
    """Segundo passe: o site linkado ainda é do veículo?"""
    pares = sites_dos_veiculos()
    trocados, duvidosos = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for nome, url, ok, detalhe in pool.map(dono_mudou, pares):
            if ok is False:
                trocados.append((nome, url, detalhe))
            elif ok is None:
                duvidosos.append((nome, url, detalhe))
    print(f"\n{len(pares) - len(trocados) - len(duvidosos)} de {len(pares)} sites "
          f"seguem do veículo · {len(trocados)} trocaram de dono · {len(duvidosos)} a conferir")
    if trocados:
        print(f"\n=== domínio trocou de dono ({len(trocados)}) ===")
        for nome, url, detalhe in trocados:
            print(f"  {nome}\n            {url}\n            {detalhe}")
    if duvidosos and not quieto:
        print(f"\n=== título não bate com o nome ({len(duvidosos)}) ===")
        for nome, url, detalhe in duvidosos:
            print(f"  {nome:<26} {detalhe}")
    return 1 if trocados else 0


if __name__ == "__main__":
    sys.exit(main())
