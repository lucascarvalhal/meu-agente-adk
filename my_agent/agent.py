from google.adk.agents.llm_agent import Agent
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig

# Tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

# Configura o "pensamento" do modelo
thinking_config = ThinkingConfig(
    include_thoughts=True,   # Mostrar o raciocínio
    thinking_budget=1024     # Limite de tokens para pensar
)

# Cria o planner
planner = BuiltInPlanner(
    thinking_config=thinking_config
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time],
    planner=planner,  # Adiciona o planner
)
