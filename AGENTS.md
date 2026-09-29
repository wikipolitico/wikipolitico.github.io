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
4. Para publicar, só com pedido do usuário:
   - Commitar com a mensagem num arquivo (`git commit -F arquivo`), porque mensagem de várias linhas com acento quebra quando passada direto pelo terminal.
   - O push na `main` só funciona com a conta dona do repositório: `gh auth switch --user wikipolitico`, `git push origin main` e depois `gh auth switch --user ajsjunior`, mesmo se o push falhar.
   - Acompanhar o workflow "Publicar site" do commit até o fim.

## Convenções de conteúdo

- **Toda afirmação precisa de fonte checável**: cada texto, parágrafo ou item de lista deve ter link para a página que permite conferir a informação.
- **Pôr em xeque as acusações do outro lado e trazer a defesa do nosso campo (esquerda petista)**:
    - Contra acusação a alguém do nosso campo, registrar as fragilidades verificáveis e a defesa do acusado.
    - Negativa genérica de adversário não entra (ex.: "nega irregularidades", "cortina de fumaça", nota de assessoria). A resposta dele só entra quando os fatos a desmentem ou quando ela confirma o fato.
    - Nenhum item é neutro: a frase de cada link deixa claro o que aquilo significa a favor do nosso campo, sem passar do que a fonte sustenta.
    - Defesa ou ataque de terceiros e coincidências entram quando favorecem o nosso campo, direta ou indiretamente, e se apoiam em fatos datados e com fonte.
- **Tom combativo em todo item**: cada frase confronta uma narrativa, dizendo o que o fato desmente, expõe ou prova, com verbo direto e contraste explícito. Exemplo: "Flávio dizia que nunca tinha entrado em avião de Vorcaro, mas voou com a família num jato em que a empresa do banqueiro tinha um terço". Vale também para títulos, resumos e descrições na página inicial.
    - O tom não afrouxa a checagem: citação literal, nada além do que a fonte sustenta, e a ressalva factual essencial continua, em poucas palavras. Adjetivo só quando o fato o sustenta. Quem combate com um fato errado entrega a vitória ao outro lado.
    - O site não se declara pró-Lula ou pró-PT com todas as letras: o lado aparece pelo combate às mentiras, não por rótulo.
- **Formatos de item**:
    - Lista de links: `[título curto – Veículo, DD/MM/AAAA](url): o que isso desmente ou prova`.
    - Linha do tempo: `- **DD/MM/AAAA — título curto:** texto ([Veículo, DD/MM/AAAA](url))`.
- **Páginas de pessoas e de casos** (ministros, políticos, escândalos): caixa `!!! abstract "Resumo"` logo depois do título, com um ou dois parágrafos sem links de fonte (só os termos com página própria levam link), e cada fato do resumo com fonte numa seção abaixo. Havendo investigação em curso, caixa `!!! warning "Caso em andamento"` com a data de atualização. Links herdados da wiki antiga ficam distribuídos pelas seções do tema a que pertencem, em subseções de lista de links (ex.: "Mais sobre o tríplex", "A Operação Gedeon (2020)"), sem seção "Acervo antigo". Cada um segue o formato de lista de links, com o título original encurtado, o veículo ou canal e a data no texto do link, para que o material possa ser buscado de novo se sair do ar, e a frase depois dos dois-pontos diz por que o item está ali, atribuindo ao blog ou post a afirmação que só ele sustenta. Termina em "Ver também", sem seção de conclusão.
- **Termos com página própria levam link**: toda menção ao mensalão, à Lava Jato, ao 8 de janeiro, ao caso Master, aos ministros do STF, às eleições e aos outros termos que têm página no site aponta para essa página. Na prática, a primeira menção de cada seção. `manutencao/linkar_termos.py` lista o que falta e grava com `--aplicar`; ao criar uma página nova de pessoa ou de caso, acrescentar o termo à lista TERMOS do script.
- **Links fora do ar nunca saem**: ficam no lugar, com `· *fora do ar em DD/MM/AAAA, motivo* · [buscar cópia no Internet Archive](https://web.archive.org/web/*/URL)`. Depois de marcar ou recuperar um link, rodar `manutencao/gerar_links_fora_do_ar.py`, que regrava o `.lycheeignore`. Não criar lista, página ou seção que agrupe os links fora do ar. Ao mudar um link de página, levar o aviso junto.
- **Checagem antes de citar**:
    - Ler a matéria inteira antes de usá-la; título e resumo de busca não bastam.
    - Conferir frases atribuídas a alguém na fonte original, porque circulam citações falsas (ex.: a frase "não tenho prova cabal contra Dirceu", atribuída a Rosa Weber, não está no voto dela).
    - Pegar a data de publicação nos metadados da página (`article:published_time`) quando ela não aparece no texto.
    - Em período eleitoral, a Agência Brasil e o gov.br tiram do ar conteúdos que citam candidatos: a página responde normalmente, mas com um aviso no lugar do texto. Conferir se há conteúdo e, se não houver, usar outra fonte.
- **Grande mídia corporativa (Globo/g1, Folha, Estadão, Veja, Gazeta do Povo, ND Mais etc.) é fonte a questionar**: quando a informação nascer nesses veículos, atribuir explicitamente ("segundo o Estadão", "revelado pela Folha"). **Corroboração só conta se vier de veículo listado em `docs/midias-alternativas.md` ou declaradamente pró-Lula/pró-PT** (ex.: Brasil 247, DCM, Revista Fórum, GGN, Brasil de Fato) — outro veículo da grande mídia repetindo a notícia não é corroboração. Sempre que possível, apontar o documento primário (PF, decisões, dados oficiais).

## Estrutura

- `docs/` — conteúdo em Markdown (nav definido em `mkdocs.yml`)
- `overrides/partials/` — templates que sobrescrevem o tema Material
- `hooks/` — hooks Python do MkDocs (ex.: lista "Últimas atualizações" na home)
- `manutencao/` — scripts de manutenção (links fora do ar, redes sociais)
- Data de atualização das páginas: plugin `git-revision-date-localized`, exibida pela div `.md-footer-last-updated` em `overrides/partials/content.html`; o hook `esconder_data_migracao.py` omite a data em páginas nunca alteradas desde a migração (commit raiz de 13/09/2026)
