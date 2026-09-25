"""Executa a equipe a partir de um payload JSON informado pela linha de comando."""

from __future__ import annotations

import json
import sys

from steven_adapter import processar_solicitacao_steven


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python run.py '{\"objetivo\": \"...\", ...}'")
    print(
        json.dumps(
            processar_solicitacao_steven(json.loads(sys.argv[1])),
            ensure_ascii=False,
            indent=2,
        )
    )
