from agents import BaseAgent


class WriterAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a professional writer. Given content and instructions, produce well-structured new documents: emails, reports, summaries, or responses. Match the requested tone and format precisely."""
        super().__init__(name="Writer", system_prompt=system_prompt)
