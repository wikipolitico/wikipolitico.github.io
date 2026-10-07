"""Faz a busca do site ignorar acentos: "eleicoes" acha "eleições", e vice-versa.

A busca do Material roda o lunr num web worker, e o worker carrega o arquivo de
português (lunr.pt.min.js) para montar o pipeline. Este hook acrescenta ao fim
desse arquivo, já copiado para o site, um trecho que tira os acentos em dois
pontos:

- no índice, antes do stemmer, para cada palavra das páginas;
- na consulta, no QueryLexer do lunr, antes de a busca interpretar o texto
  digitado. Tirar o acento só no índice não basta: o Material compara os termos
  digitados com os termos do índice para marcar os que "faltam" no resultado, e
  marcaria como faltando toda palavra digitada com acento.

O trecho vai no arquivo gerado, e não numa cópia em overrides/, para continuar
valendo quando o Material atualizar o lunr. Se o arquivo sumir (por exemplo, se
a busca deixar de usar português), o hook avisa, e o build com --strict falha.
"""

import logging
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.busca_sem_acento")

MARCA = "/* wikipolitico: busca sem acento */"

JS = MARCA + r"""
(function (lunr) {
  if (!lunr || !lunr.pt || lunr.pt.semAcento) return;
  var tirar = function (s) { return String(s).normalize("NFD").replace(/[̀-ͯ]/g, ""); };
  var semAcento = function (token) { return token.update(tirar); };
  lunr.Pipeline.registerFunction(semAcento, "semAcento-pt");

  var original = lunr.pt;
  var pt = function () {
    original.call(this);
    this.pipeline.before(lunr.pt.stemmer, semAcento);
    if (this.searchPipeline) this.searchPipeline.before(lunr.pt.stemmer, semAcento);
  };
  Object.keys(original).forEach(function (k) { pt[k] = original[k]; });
  pt.semAcento = true;
  lunr.pt = pt;

  var Lexer = lunr.QueryLexer;
  var LexerSemAcento = function (str) { Lexer.call(this, tirar(str)); };
  LexerSemAcento.prototype = Lexer.prototype;
  Object.keys(Lexer).forEach(function (k) { LexerSemAcento[k] = Lexer[k]; });
  lunr.QueryLexer = LexerSemAcento;
})(self.lunr);
"""


def on_post_build(config, **kwargs):
    alvo = Path(config["site_dir"]) / "assets" / "javascripts" / "lunr" / "min" / "lunr.pt.min.js"
    if not alvo.exists():
        log.warning("Arquivo %s não encontrado: a busca vai diferenciar acentos.", alvo)
        return
    texto = alvo.read_text(encoding="utf-8")
    if MARCA not in texto:
        alvo.write_text(texto.rstrip() + "\n" + JS, encoding="utf-8")
