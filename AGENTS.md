# Wiki Político

Site estático em **MkDocs Material** (`mkdocs.yml`), publicado no GitHub Pages via `.github/workflows/publicar.yml`.

## Fluxo de trabalho (obrigatório)

1. Ao terminar qualquer alteração, **subir o site localmente para revisão** antes de commitar:
   ```powershell
   & "C:\Users\Junior\AppData\Local\Programs\Python\Python313\python.exe" -m mkdocs serve
   ```
   - O `python` do PATH é do msys64 e **não** tem o mkdocs instalado; usar sempre o Python 3.13 do caminho acima.
   - O servidor sobe em http://127.0.0.1:8000 com recarga automática ao salvar arquivos.
2. **Nunca commitar nem publicar sem pedido explícito do usuário.** O usuário revisa em localhost primeiro.
3. Para validação sem servidor, buildar em diretório temporário (`--site-dir`), nunca sobrescrever a pasta `site/` localmente — ela é gerada pelo CI.

## Convenções de conteúdo

- **Toda afirmação precisa de fonte checável**: cada texto, parágrafo ou item de lista deve ter link para a página que permite conferir a informação.
- **Pôr em xeque as acusações do outro lado e trazer a defesa do nosso campo (esquerda petista)**:
    - Contra acusação a alguém do nosso campo, registrar as fragilidades verificáveis e a defesa do acusado.
    - Negativa genérica de adversário não entra (ex.: "nega irregularidades", "cortina de fumaça", nota de assessoria). A resposta dele só entra quando os fatos a desmentem ou quando ela confirma o fato.
    - Nenhum item é neutro: a frase de cada link deixa claro o que aquilo significa a favor do nosso campo, sem passar do que a fonte sustenta.
    - Defesa ou ataque de terceiros e coincidências entram quando favorecem o nosso campo, direta ou indiretamente, e se apoiam em fatos datados e com fonte.
- **Grande mídia corporativa (Globo/g1, Folha, Estadão, Veja, Gazeta do Povo, ND Mais etc.) é fonte a questionar**: quando a informação nascer nesses veículos, atribuir explicitamente ("segundo o Estadão", "revelado pela Folha"). **Corroboração só conta se vier de veículo listado em `docs/midias-alternativas.md` ou declaradamente pró-Lula/pró-PT** (ex.: Brasil 247, DCM, Revista Fórum, GGN, Brasil de Fato) — outro veículo da grande mídia repetindo a notícia não é corroboração. Sempre que possível, apontar o documento primário (PF, decisões, dados oficiais).

## Estrutura

- `docs/` — conteúdo em Markdown (nav definido em `mkdocs.yml`)
- `overrides/partials/` — templates que sobrescrevem o tema Material
- `hooks/` — hooks Python do MkDocs (ex.: lista "Últimas atualizações" na home)
- `manutencao/` — scripts de manutenção (links fora do ar, redes sociais)
- Data de atualização das páginas: plugin `git-revision-date-localized`, exibida pela div `.md-footer-last-updated` em `overrides/partials/content.html`; o hook `esconder_data_migracao.py` omite a data em páginas nunca alteradas desde a migração (commit raiz de 13/09/2026)
