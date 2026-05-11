from agents import BaseAgent


class AnalyserAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a critical analyst. Identify themes, patterns, contradictions, strengths, and weaknesses in the provided content. Always explain your reasoning. Structure your output with clear headings."""
        super().__init__(name="Analyser", system_prompt=system_prompt)
