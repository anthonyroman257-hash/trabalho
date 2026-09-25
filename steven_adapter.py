"""Ponte entre a governança Stiven e a equipe CrewAI.

Stiven é uma skill de governança, não uma biblioteca Python. Por isso, o
orquestrador que a invoca deve registrar sua decisão no evento antes de chamar
esta ponte. Assim, nenhuma equipe é iniciada sem a autorização correspondente.
"""

from __future__ import annotations

from typing import Any

from gerente_crew import executar


DECISOES_AUTORIZADAS = {
    "autorizado automaticamente",
    "autorizado com controles",
}


def processar_solicitacao_steven(evento: dict[str, Any]) -> dict[str, Any]:
    """Executa a equipe somente após a decisão registrada pelo Stiven.

    Evento esperado:
    {
      "objetivo": "...",
      "profissao_1": "...",
      "profissao_2": "...",
      "contexto": "...",  # opcional
      "governanca_stiven": {
        "decisao": "autorizado automaticamente",
        "classificacao": "leitura",
        "controles": ["preservar alterações existentes"]
      }
    }

    Para decisões ``requer confirmação do usuário`` ou ``bloqueado``, a ponte
    não chama a CrewAI e devolve a decisão ao orquestrador.
    """
    governanca = evento.get("governanca_stiven")
    if not isinstance(governanca, dict):
        return {
            "status": "aguardando_governanca_stiven",
            "mensagem": "Execute a skill Stiven e anexe sua decisão antes de iniciar a equipe.",
        }

    decisao = str(governanca.get("decisao", "")).strip().lower()
    if decisao not in DECISOES_AUTORIZADAS:
        return {
            "status": "execucao_nao_autorizada",
            "decisao_stiven": decisao or "decisão ausente",
            "governanca_stiven": governanca,
        }

    resposta = executar(evento)
    return {
        "status": "concluido",
        "governanca_stiven": governanca,
        **resposta,
    }
