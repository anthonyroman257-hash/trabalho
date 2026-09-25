# Agente Gerente Local (CrewAI + Ollama)

Equipe local com sete agentes: gerente, arquiteto, front-end, back-end, banco de dados, QA e segurança. Ela executa no computador usando um modelo baixado no Ollama; não usa `OPENAI_API_KEY` nem créditos da API.

## Preparação única

1. Instale o [Ollama para Windows](https://ollama.com/download).
2. Baixe um modelo local: `ollama pull qwen2.5:7b`.
3. Crie e ative um ambiente virtual Python.
4. Instale as dependências: `pip install -r requirements.txt`.
5. Opcionalmente, copie `.env.example` para `.env` e altere o modelo. O padrão é `qwen2.5:7b`.

Um modelo local não cobra por tokens, mas precisa de espaço em disco e capacidade de processamento. Não use modelos com sufixo `:cloud` se a meta for permanecer local.

## Executar

```powershell
python run.py '{"objetivo":"Criar um site simples que liste lanchonetes de Matupá-MT e exiba WhatsApp somente quando verificado.", "contexto":"Não pesquisar nem inventar estabelecimentos, endereços ou telefones."}'
```

## Conectar ao Stiven

O Stiven fornecido é uma skill de governança do Codex, e não um código Python importável. Ele deve classificar a solicitação antes da execução. A ponte só inicia a CrewAI quando receber uma decisão autorizada: `autorizado automaticamente` ou `autorizado com controles`.

No orquestrador local, importe:

```python
from steven_adapter import processar_solicitacao_steven

resposta = processar_solicitacao_steven({
    "objetivo": "Criar um catálogo local de lanchonetes",
    "contexto": "Usar dados de exemplo claramente identificados.",
    "governanca_stiven": {
        "decisao": "autorizado automaticamente",
        "classificacao": "baixo risco",
        "controles": ["preservar alterações existentes"]
    }
})
```

O evento deve conter `objetivo`, opcionalmente `profissao_1`, `profissao_2`, `contexto`, e a decisão em `governanca_stiven`. A função devolve o resultado e o uso de tokens quando a execução é autorizada.
