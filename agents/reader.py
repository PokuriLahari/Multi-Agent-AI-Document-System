from agents import BaseAgent


class ReaderAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a document reader. Your only job is to clearly extract and present the raw content of a document. Do not interpret or analyse. Return content exactly as found, organised by section."""
        super().__init__(name="Reader", system_prompt=system_prompt)

    def extract(self, chunks: list[dict]) -> str:
        extracted_text = []
        for i, chunk in enumerate(chunks):
            header = f"--- Chunk {i + 1} (Page {chunk.get('page_number', 'N/A')}) ---"
            extracted_text.append(header)
            extracted_text.append(chunk["text"])
        
        return "\n\n".join(extracted_text)
