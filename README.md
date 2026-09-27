# Wiki Político

Acervo colaborativo sobre política nacional e internacional, publicado em https://wikipolitico.github.io.

## Como editar

- O conteúdo fica em `docs/`. Cada tema é um arquivo em `docs/temas/`.
- Cada envio para a branch `main` publica o site automaticamente pelo GitHub Actions.
- Para ver o site no seu computador antes de enviar:

  ```sh
  uv run --with-requirements requirements.txt mkdocs serve
  ```

## Manutenção

- Links fora do ar continuam no lugar deles, marcados logo depois com o aviso *fora do ar em DD/MM/AAAA* e um atalho para buscar a cópia no Internet Archive. Não há lista separada: o aviso na página é o único registro. Depois de marcar ou recuperar um link, rode `manutencao/gerar_links_fora_do_ar.py`, que regrava o `.lycheeignore`.
- [manutencao/links-redirecionando.md](manutencao/links-redirecionando.md): links que redirecionam para outra página e precisam de revisão.
- Toda segunda-feira o workflow "Verificar links" confere os links do site. O resultado aparece no resumo da execução, na aba Actions. Os links já conhecidos como fora do ar ficam listados em `.lycheeignore`, para o relatório mostrar só os que quebraram depois.
- As visitas são medidas pelo [GoatCounter](https://wikipolitico.goatcounter.com), que não usa cookies nem guarda dados pessoais. O código da conta fica em `mkdocs.yml` (`extra.analytics.property`), e o script, em `overrides/partials/integrations/analytics/custom.html`.
