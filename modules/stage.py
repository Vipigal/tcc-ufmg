"""Base para estágios da pipeline com cache por estágio (Template Method).

Cada estágio (módulos 1–6) herda de `Stage` e implementa três hooks internos
— `_compute`, `_save`, `_load` — delegando aos seus próprios métodos públicos
descritivos (`build`, `project`, `apply`, ...). A orquestração de cache fica
centralizada em `Stage.run`:

- se todos os artefatos (`FILES`) já existem e `force` é falso → carrega de disco;
- senão → apaga artefatos antigos, recalcula e persiste.

Invalidação é por **existência de arquivo** (não por hash de conteúdo). Mudou o
código de um estágio? Rode com `force=True` (no notebook, via `FORCE_FROM`).
"""
from __future__ import annotations

from pathlib import Path


class Stage:
    FILES: tuple[str, ...] = ()

    def _compute(self, *inputs):
        raise NotImplementedError

    def _save(self, result, out_dir) -> None:
        raise NotImplementedError

    def _load(self, out_dir):
        raise NotImplementedError

    def run(self, *inputs, out_dir, force: bool = False):
        out = Path(out_dir)
        paths = [out / f for f in self.FILES]
        if not force and self.FILES and all(p.exists() for p in paths):
            print(f"[cache] {type(self).__name__}: hit")
            return self._load(out)
        for p in paths:
            p.unlink(missing_ok=True)
        print(f"[cache] {type(self).__name__}: {'forçado' if force else 'frio'}")
        result = self._compute(*inputs)
        self._save(result, out)
        return result
