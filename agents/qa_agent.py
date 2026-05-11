from agents import BaseAgent


class QAAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a precise question-answering assistant. Answer only based on the provided context. If the answer is not in the context, say "I could not find this in the document." Never make up information. Cite which part of the document your answer comes from."""
        super().__init__(name="QA", system_prompt=system_prompt)
