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

- [manutencao/links-removidos.md](manutencao/links-removidos.md): links que estavam fora do ar na migração da wiki (13/09/2026), com atalho para buscar a cópia no Internet Archive.
- [manutencao/links-redirecionando.md](manutencao/links-redirecionando.md): links que redirecionam para outra página e precisam de revisão.
- Toda segunda-feira o workflow "Verificar links" confere os links do site. O resultado aparece no resumo da execução, na aba Actions.
