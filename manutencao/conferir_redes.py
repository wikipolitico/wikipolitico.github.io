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
  instagram  o <title> traz o nome da conta, mas só em consulta isolada: em
             checagem de lote o Instagram passa a devolver a casca de login
             para todo mundo, então a resposta genérica vale como inconclusiva,
             nunca como prova de que o perfil caiu
  mastodon   código HTTP

Facebook e X não entram: respondem 200 até para perfil inexistente e não
expõem nada no HTML que permita distinguir. Esses ficam sob conferência humana.

O código de saída é 1 só quando há queda comprovada. Inconclusivo não derruba
a verificação, para não encher o relatório de falso positivo.

Uso:
    py manutencao/conferir_redes.py            # confere tudo e lista o que caiu
    py manutencao/conferir_redes.py --quieto    # só o resumo e o código de saída
"""
import concurrent.futures
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

CURL = "curl.exe" if os.name == "nt" else "curl"

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BLUESKY_API = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor="

RX_URL = re.compile(r"\((https?://[^)\s]+)\)")
SEM_CHECAGEM = ("facebook.com", "twitter.com", "x.com", "web.archive.org")


def rede_de(url):
    h = urlparse(url).netloc.lower().removeprefix("www.")
    if h == "bsky.app":
        return "bluesky"
    if h.endswith("youtube.com"):
        # só canal e perfil; link de vídeo o lychee já confere pelo código HTTP
        return "youtube" if re.search(r"/(channel|user|c)/|/@", urlparse(url).path) else None
    if h == "t.me":
        return "telegram"
    if h == "instagram.com":
        # só perfil: /p/, /reel/ e /tv/ são publicação, não conta
        return "instagram" if len([p for p in urlparse(url).path.split("/") if p]) == 1 else None
    if re.search(r"/@[A-Za-z0-9._]+$", url) and "mastodon" in h:
        return "mastodon"
    return None


def curl(url, so_codigo=False):
    cmd = [CURL, "-sL", "-m", "30", "--compressed", "-A", UA]
    cmd += ["-o", "/dev/null", "-w", "%{http_code}"] if so_codigo else []
    try:
        r = subprocess.run(cmd + [url], capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return ""


def checar(item):
    url, rede = item
    if rede == "bluesky":
        alvo = urlparse(url).path.split("/profile/")[-1].strip("/")
        codigo = curl(BLUESKY_API + alvo, so_codigo=True)
        return url, rede, codigo == "200", f"getProfile {codigo or 'sem resposta'}"
    if rede in ("youtube", "mastodon"):
        codigo = curl(url, so_codigo=True)
        if codigo == "429":  # limite de requisições nosso, não queda do perfil
            return url, rede, None, "HTTP 429, limite de requisições"
        return url, rede, codigo.startswith("2"), f"HTTP {codigo or 'sem resposta'}"
    corpo = curl(url)
    if rede == "telegram":
        if "tgme_page_title" in corpo:
            return url, rede, True, "tem título de canal"
        # ausência de título não prova queda: o Telegram devolve a mesma casca
        # para canal inexistente e para canal restrito na região de quem checa.
        # t.me/rtnews, por exemplo, responde aqui e não responde no runner da CI.
        return url, rede, None, "sem título de canal, inexistente ou restrito na região"
    titulo = re.search(r"<title>([^<]*)</title>", corpo)
    t = (titulo.group(1) if titulo else "").strip()
    if t and t.lower() != "instagram":
        return url, rede, True, f"título: {t[:60]}"
    return url, rede, None, "resposta genérica, inconclusivo"


def coletar():
    vistos, itens, sem_checagem = set(), [], 0
    for md in sorted(DOCS.rglob("*.md")):
        for url in RX_URL.findall(md.read_text(encoding="utf-8")):
            if url in vistos:
                continue
            vistos.add(url)
            if any(d in url for d in SEM_CHECAGEM):
                sem_checagem += 1
                continue
            rede = rede_de(url)
            if rede:
                itens.append((url, rede))
    return itens, sem_checagem


def main():
    quieto = "--quieto" in sys.argv
    itens, sem_checagem = coletar()
    if not quieto:
        print(f"conferindo {len(itens)} perfis; {sem_checagem} links do Facebook e do X "
              f"ficam de fora, porque não há como checar por robô\n")
    caidos, inconclusivos, ok_total = [], [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for url, rede, ok, detalhe in pool.map(checar, itens):
            if ok is None:
                inconclusivos.append((rede, url))
            elif ok:
                ok_total += 1
                if not quieto:
                    print(f"  ok       {rede:<9} {url}")
            else:
                caidos.append((rede, url, detalhe))
    print(f"\n{ok_total} no ar · {len(caidos)} fora do ar · "
          f"{len(inconclusivos)} inconclusivos, de {len(itens)} perfis")
    if caidos:
        print(f"\n=== fora do ar ({len(caidos)}) ===")
        for rede, url, detalhe in sorted(caidos):
            print(f"  {rede:<9} {url}\n            {detalhe}")
    if inconclusivos and not quieto:
        print(f"\n=== inconclusivos, exigem conferência humana ({len(inconclusivos)}) ===")
        for rede, url in sorted(inconclusivos):
            print(f"  {rede:<9} {url}")
    return 1 if caidos else 0


if __name__ == "__main__":
    sys.exit(main())
