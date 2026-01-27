import re
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

# Tool implementation
def get_current_time(city: str) -> dict:
    """Retorna a hora atual em uma cidade específica."""
    return {"status": "success", "city": city, "time": "10:30 AM"}


# Cria o LlmAgent interno
internal_llm = LlmAgent(
    name="internal_llm",
    model="gemini-2.5-flash",
    description="Agente interno para processamento",
    instruction="""Você é um assistente brasileiro simpático.

REGRAS:
1. SEMPRE pense e responda em PORTUGUÊS DO BRASIL
2. NUNCA use inglês

Use a ferramenta 'get_current_time' quando perguntarem as horas.

Formato OBRIGATÓRIO da resposta:
PENSAMENTO: [seu raciocínio detalhado em português]
RESPOSTA: [resposta amigável para o usuário]
""",
    tools=[get_current_time],
)


class ThinkingAgent(BaseAgent):
    """
    Agente customizado que separa o pensamento da resposta em eventos distintos.
    """
    
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Executa o agente e separa pensamento da resposta em eventos distintos."""
        
        full_response = ""
        
        # Executa o LLM agent interno
        async for event in internal_llm.run_async(ctx):
            # Se é uma chamada de função (tool), passa adiante
            if event.get_function_calls():
                yield event
                continue
            
            # Se é resposta de função (tool result), passa adiante
            if event.get_function_responses():
                yield event
                continue
            
            # Acumula texto da resposta
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response = part.text  # Pega o texto completo
        
        # Processa a resposta final
        if full_response:
            pensamento = ""
            resposta = full_response
            
            # Tenta extrair PENSAMENTO e RESPOSTA
            match_pensamento = re.search(
                r'PENSAMENTO[:\s]*(.+?)(?=RESPOSTA[:\s]|$)', 
                full_response, 
                re.DOTALL | re.IGNORECASE
            )
            match_resposta = re.search(
                r'RESPOSTA[:\s]*(.+?)$', 
                full_response, 
                re.DOTALL | re.IGNORECASE
            )
            
            if match_pensamento:
                pensamento = match_pensamento.group(1).strip()
            
            if match_resposta:
                resposta = match_resposta.group(1).strip()
            
            # Evento 1: Pensamento (se existir)
            if pensamento:
                yield Event(
                    author=self.name,
                    invocation_id=ctx.invocation_id,
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=f"💭 **Pensamento**\n\n{pensamento}")]
                    )
                )
            
            # Evento 2: Resposta Final
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=f"🤖 {resposta}")]
                )
            )


# Exporta o agente como root_agent
root_agent = ThinkingAgent(
    name="thinking_agent",
    description="Agente que mostra o pensamento separado da resposta",
    sub_agents=[internal_llm],
)
