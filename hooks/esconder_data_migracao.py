"""Esconde a data de atualização em páginas nunca alteradas desde a migração.

Nessas páginas o plugin git-revision-date-localized mostraria a data do commit
de migração (13/09/2026), que não representa uma revisão do conteúdo. O hook
remove as chaves de meta do plugin, e o template (partials/content.html)
simplesmente não exibe a div de atualização.
"""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_hashes_migracao = None


def _commits_da_migracao():
    """Hashes dos commits raiz do repositório (o commit de migração)."""
    global _hashes_migracao
    if _hashes_migracao is None:
        try:
            saida = subprocess.run(
                ["git", "-C", str(RAIZ), "rev-list", "--max-parents=0", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
            _hashes_migracao = set(saida.stdout.split()) if saida.returncode == 0 else set()
        except (OSError, subprocess.SubprocessError):
            _hashes_migracao = set()
    return _hashes_migracao


def on_page_context(context, page, config, nav):
    if page.meta.get("git_revision_date_localized_hash") in _commits_da_migracao():
        for chave in [c for c in page.meta if c.startswith("git_revision_date_localized")]:
            del page.meta[chave]
    return context
