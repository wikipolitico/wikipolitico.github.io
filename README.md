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

- [manutencao/links-fora-do-ar.md](manutencao/links-fora-do-ar.md): links que estavam fora do ar na migração da wiki (13/09/2026). Eles continuam no site, marcados como fora do ar e com atalho para buscar a cópia no Internet Archive. Ao recuperar um link, troque o endereço no tema, retire o aviso e apague a linha dele em `.lycheeignore`.
- [manutencao/links-redirecionando.md](manutencao/links-redirecionando.md): links que redirecionam para outra página e precisam de revisão.
- Toda segunda-feira o workflow "Verificar links" confere os links do site. O resultado aparece no resumo da execução, na aba Actions. Os links já conhecidos como fora do ar ficam listados em `.lycheeignore`, para o relatório mostrar só os que quebraram depois.
- As visitas são medidas pelo [GoatCounter](https://wikipolitico.goatcounter.com), que não usa cookies nem guarda dados pessoais. O código da conta fica em `mkdocs.yml` (`extra.analytics.property`), e o script, em `overrides/partials/integrations/analytics/custom.html`.
