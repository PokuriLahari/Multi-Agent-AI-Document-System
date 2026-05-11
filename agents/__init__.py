from langchain_ollama import OllamaLLM


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, model: str = "llama3.2"):
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model

    def run(self, user_message: str, context: str = "") -> str:
        try:
            llm = OllamaLLM(model=self.model_name, base_url="http://localhost:11434")
            full_prompt = f"{self.system_prompt}\n\nContext:\n{context}\n\nUser: {user_message}"
            response = llm.invoke(full_prompt)
            return response
        except Exception as e:
            print(f"[DEBUG] Error in {self.name} agent: {type(e).__name__}: {str(e)}")
            return f"Error: Agent failed to process request. Please try again."
