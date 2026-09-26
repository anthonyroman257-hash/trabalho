"""Equipe local CrewAI para planejamento e desenvolvimento de software.

Esta versão usa Ollama localmente. Não usa chave nem créditos da OpenAI API.
Antes de executar, instale o Ollama e baixe um modelo local, por exemplo:
``ollama pull qwen2.5:7b``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task


@dataclass(frozen=True)
class Solicitacao:
    """Entrada estável para iniciar o fluxo local."""

    objetivo: str
    profissao_1: str = "Arquiteto de Software"
    profissao_2: str = "Desenvolvedor Full Stack"
    contexto: str = ""
    decisoes_confirmadas: str = ""


RESTRICOES = (
    "Não invente estabelecimentos, endereços, telefones, números de WhatsApp, "
    "dados pessoais ou resultados de pesquisa. Não acesse produção, bancos remotos, "
    "credenciais, arquivos fora do projeto ou serviços externos sem autorização humana explícita."
)

PROTOCOLO_GRILL_ME = """
Você aplica o protocolo Grill Me antes da implementação. Mapeie o pedido como
uma árvore de decisões. Em cada rodada, pergunte somente decisões cuja base já
esteja resolvida; informe uma recomendação para cada pergunta. Fatos que possam
ser verificados no projeto são responsabilidade sua, não perguntas ao usuário.
Não transforme hipóteses em requisitos e não inicie implementação enquanto o
usuário não confirmar que as decisões foram entendidas e registradas.
""".strip()


def _modelo() -> LLM:
    """Cria um LLM servido pelo Ollama em ``localhost``."""
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip()
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    if not model:
        raise RuntimeError("Defina OLLAMA_MODEL com um modelo local já baixado.")
    return LLM(model=f"ollama/{model}", base_url=base_url, temperature=0.2)


def _agente(role: str, goal: str, backstory: str, llm: LLM, *, delega: bool = False) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=f"{backstory}\n\n{RESTRICOES}",
        llm=llm,
        allow_delegation=delega,
        verbose=True,
    )


def criar_equipe(solicitacao: Solicitacao) -> Crew:
    """Monta a equipe após a fase de descoberta Grill Me confirmada."""
    llm = _modelo()
    contexto = solicitacao.contexto or "Nenhum contexto adicional foi informado."

    gerente = _agente(
        "Gerente de Produto e Engenharia de Software",
        "Transformar uma solicitação de produto em uma entrega segura, verificável e priorizada.",
        "Você coordena especialistas, esclarece lacunas, revisa as entregas e consolida critérios de aceitação, riscos, testes e próximos passos.",
        llm,
        delega=True,
    )
    entrevistador = _agente(
        "Facilitador de Descoberta Grill Me",
        "Eliminar ambiguidades e transformar intenção em decisões confirmadas antes do desenvolvimento.",
        f"{PROTOCOLO_GRILL_ME}\nVocê é direto, construtivo e não presume respostas.",
        llm,
    )
    arquiteto = _agente("Arquiteto de Software", "Definir uma arquitetura simples, sustentável e justificável.", "Você decompõe sistemas em componentes, fluxos de dados e decisões técnicas.", llm)
    frontend = _agente("Desenvolvedor Front-End", "Projetar uma interface acessível, responsiva e clara.", "Você entrega componentes, comportamento de busca e estados vazios.", llm)
    backend = _agente("Desenvolvedor Back-End e APIs", "Definir uma camada de dados e APIs segura e testável quando necessária.", "Você propõe contratos de API, validações e tratamento de erros sem chamar serviços reais.", llm)
    banco = _agente("Especialista em Banco de Dados", "Modelar dados mínimos, privados e fáceis de validar.", "Você projeta schemas e regras de qualidade sem conectar a banco remoto.", llm)
    qa = _agente("Engenheiro de QA", "Verificar critérios de aceitação e cenários de falha antes da entrega.", "Você cria casos de teste claros, identifica lacunas e evita alegar testes não executados.", llm)
    seguranca = _agente("Especialista em Segurança", "Revisar privacidade, exposição de dados e riscos de segurança.", "Você aplica minimização de dados e não recomenda expor números pessoais sem validação.", llm)

    briefing_confirmado = Task(
        description=(
            f"Revise o objetivo: {solicitacao.objetivo}\n\nContexto: {contexto}\n\n"
            f"Decisões confirmadas pelo usuário: {solicitacao.decisoes_confirmadas}\n\n"
            "Converta somente as decisões confirmadas em um briefing de desenvolvimento. "
            "Marque qualquer lacuna restante como pendência; não a preencha por suposição."
        ),
        expected_output="Briefing confirmado com objetivo, escopo, restrições, critérios de aceitação, pendências e itens fora de escopo.",
        agent=entrevistador,
    )
    analise = Task(
        description=(f"Analise a solicitação: {solicitacao.objetivo}\n\nContexto: {contexto}\n\n"
                     "Defina escopo, ambiguidades, critérios de aceitação, módulos, dados a validar e itens que exigem aprovação humana."),
        expected_output="Documento de análise com escopo, critérios de aceitação, premissas e riscos.", agent=gerente, context=[briefing_confirmado])
    arquitetura = Task(
        description="Com base na análise, proponha componentes, fluxo de dados, tecnologias e decisões arquiteturais justificadas.",
        expected_output="Arquitetura textual com componentes, fluxo e riscos técnicos.", agent=arquiteto, context=[analise])
    interface = Task(
        description="Projete a interface com layout, componentes, acessibilidade, responsividade, busca e estado vazio. Mostre contato somente se estiver marcado como verificado.",
        expected_output="Especificação de interface e componentes sem dados reais inventados.", agent=frontend, context=[analise, arquitetura])
    api = Task(
        description="Defina endpoints, validações, contratos e erros. Não realize chamadas de rede nem use segredos.",
        expected_output="Contrato de API seguro e testável, ou justificativa para uma primeira versão sem back-end.", agent=backend, context=[analise, arquitetura])
    dados = Task(
        description="Modele os dados e regras de verificação. Para contatos, separe valor, origem, data de verificação e status; não inclua exemplos que pareçam dados reais.",
        expected_output="Modelo de dados e regras de qualidade/validação sem conexão externa.", agent=banco, context=[analise, arquitetura])
    testes = Task(
        description="Crie testes de aceitação, unidade e integração no formato Dado/Quando/Então. Liste o que não foi executado.",
        expected_output="Plano de QA com casos, lacunas e critérios de aprovação.", agent=qa, context=[interface, api, dados])
    revisao_seguranca = Task(
        description="Revise privacidade, dados de contato, validação, exposição em logs e riscos OWASP pertinentes.",
        expected_output="Checklist de segurança com riscos, severidade e mitigação.", agent=seguranca, context=[interface, api, dados])
    consolidacao = Task(
        description="Consolide o trabalho em relatório final com entregáveis, critérios atendidos e pendentes, riscos, testes, segurança, dados a validar e próximo passo.",
        expected_output="Relatório final em Markdown, objetivo e pronto para revisão humana.", agent=gerente, context=[testes, revisao_seguranca])

    return Crew(
        agents=[gerente, entrevistador, arquiteto, frontend, backend, banco, qa, seguranca],
        tasks=[briefing_confirmado, analise, arquitetura, interface, api, dados, testes, revisao_seguranca, consolidacao],
        manager_agent=gerente,
        process=Process.hierarchical,
        planning=False,
        verbose=True,
        max_rpm=10,
    )


def iniciar_grill_me(payload: dict[str, Any]) -> dict[str, Any]:
    """Executa somente a rodada de descoberta, sem iniciar o desenvolvimento."""
    objetivo = str(payload.get("objetivo", "")).strip()
    if not objetivo:
        raise ValueError("O campo obrigatório 'objetivo' está ausente.")
    contexto = str(payload.get("contexto", "")).strip() or "Nenhum contexto adicional foi informado."
    entrevistador = _agente(
        "Facilitador de Descoberta Grill Me",
        "Conduzir uma rodada de decisões antes de qualquer planejamento ou implementação.",
        f"{PROTOCOLO_GRILL_ME}\nNão escreva código, plano técnico completo nem instruções de execução.",
        _modelo(),
    )
    rodada = Task(
        description=(
            f"Pedido a esclarecer: {objetivo}\n\nContexto disponível: {contexto}\n\n"
            "Produza a primeira fronteira de decisões. Use perguntas numeradas no formato "
            "'❓ Qn — título' e, abaixo de cada pergunta, '➡️ Recomendação'. "
            "Inclua apenas decisões que podem ser respondidas agora."
        ),
        expected_output="Uma rodada objetiva de perguntas e recomendações, sem iniciar a implementação.",
        agent=entrevistador,
    )
    resultado = Crew(agents=[entrevistador], tasks=[rodada], process=Process.sequential, verbose=True).kickoff(inputs=payload)
    return {
        "status": "aguardando_decisoes_do_grill_me",
        "perguntas": str(resultado),
        "proxima_acao": "Responda às perguntas e execute novamente com decisoes_confirmadas e modo='executar'.",
    }


def executar(payload: dict[str, Any]) -> dict[str, Any]:
    """Recebe JSON e retorna o resultado serializável para o orquestrador local."""
    objetivo = str(payload.get("objetivo", "")).strip()
    if not objetivo:
        raise ValueError("O campo obrigatório 'objetivo' está ausente.")
    modo = str(payload.get("modo", "grill")).strip().lower()
    if modo in {"grill", "descoberta", "grill-me"}:
        return iniciar_grill_me(payload)
    decisoes_confirmadas = str(payload.get("decisoes_confirmadas", "")).strip()
    if not decisoes_confirmadas:
        return {
            "status": "bloqueado_por_decisoes_nao_confirmadas",
            "mensagem": "Inicie com modo='grill'. A equipe só planeja ou implementa após decisões confirmadas.",
        }
    solicitacao = Solicitacao(
        objetivo=objetivo,
        profissao_1=str(payload.get("profissao_1", "Arquiteto de Software")),
        profissao_2=str(payload.get("profissao_2", "Desenvolvedor Full Stack")),
        contexto=str(payload.get("contexto", "")),
        decisoes_confirmadas=decisoes_confirmadas,
    )
    resultado = criar_equipe(solicitacao).kickoff(inputs=payload)
    return {"resultado": str(resultado), "uso_de_tokens": getattr(resultado, "token_usage", None)}
