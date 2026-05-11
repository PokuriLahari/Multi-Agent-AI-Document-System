from agents import BaseAgent


class SummariserAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are an expert summariser. Given document content, produce a clear, structured summary with: 1) a one-paragraph overview, 2) key points as bullet list, 3) important numbers or dates if present. Be concise."""
        super().__init__(name="Summariser", system_prompt=system_prompt)
