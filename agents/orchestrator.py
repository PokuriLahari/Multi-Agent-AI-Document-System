from agents import BaseAgent
from agents.reader import ReaderAgent
from agents.summariser import SummariserAgent
from agents.analyser import AnalyserAgent
from agents.qa_agent import QAAgent
from agents.writer import WriterAgent
from agents.crew_builder import build_crew_agent, run_crew, get_predefined_configs
from pipeline.embedder import VectorStore


class OrchestratorAgent(BaseAgent):
    VALID_INTENTS = {"SUMMARISE", "ANALYSE", "QA", "WRITE", "READ", "MULTI"}

    def __init__(self):
        system_prompt = "You are an orchestrator that routes user requests to appropriate agents."
        super().__init__(name="Orchestrator", system_prompt=system_prompt)

    def detect_intent(self, user_message: str) -> str:
        intent_system_prompt = "Classify the user's request into exactly one of these intents: SUMMARISE, ANALYSE, QA, WRITE, READ, MULTI. Return only the intent word, nothing else."
        
        temp_orchestrator = BaseAgent(
            name="IntentDetector",
            system_prompt=intent_system_prompt,
            model=self.model
        )
        response = temp_orchestrator.run(user_message)
        intent = response.strip().upper()
        
        if intent not in self.VALID_INTENTS:
            return "QA"
        return intent

    def route(self, intent: str, user_message: str, context: str) -> str:
        if intent == "SUMMARISE":
            agent = SummariserAgent()
            return agent.run(user_message, context)
        elif intent == "ANALYSE":
            agent = AnalyserAgent()
            return agent.run(user_message, context)
        elif intent == "QA":
            agent = QAAgent()
            return agent.run(user_message, context)
        elif intent == "WRITE":
            agent = WriterAgent()
            return agent.run(user_message, context)
        elif intent == "READ":
            agent = ReaderAgent()
            chunks = self._parse_chunks_from_context(context)
            return agent.extract(chunks)
        elif intent == "MULTI":
            summariser = SummariserAgent()
            summary = summariser.run(user_message, context)
            
            analyser = AnalyserAgent()
            analysis = analyser.run(user_message, context)
            
            return f"=== SUMMARY ===\n{summary}\n\n=== ANALYSIS ===\n{analysis}"
        else:
            return "Unknown intent"

    def _parse_chunks_from_context(self, context: str) -> list[dict]:
        chunks = []
        parts = context.split("\n---\n")
        
        for i, part in enumerate(parts):
            if part.strip():
                chunks.append({
                    "text": part.strip(),
                    "page_number": i + 1,
                    "source_file": "unknown"
                })
        
        return chunks

    def process(self, user_message: str, collection_name: str, vector_store: VectorStore) -> dict:
        search_results = vector_store.search(user_message, collection_name, n_results=5)

        context_parts = [result["text"] for result in search_results]
        context = "\n---\n".join(context_parts)

        if len(context) > 3000:
            context = context[:2997] + "..."

        intent = self.detect_intent(user_message)

        response = self.route(intent, user_message, context)

        return {
            "intent": intent,
            "response": response,
            "chunks_used": len(search_results)
        }

    def process_with_crew(self, user_message: str, collection_name: str, vector_store: VectorStore, selected_agents=None) -> dict:
        search_results = vector_store.search(user_message, collection_name, n_results=5)

        context_parts = [result["text"] for result in search_results]
        context = "\n---\n".join(context_parts)

        if len(context) > 3000:
            context = context[:2997] + "..."

        detected_intent = self.detect_intent(user_message)

        if selected_agents is None:
            intent_to_agents = {
                "SUMMARISE": ["summariser"],
                "ANALYSE": ["analyser"],
                "QA": ["qa"],
                "WRITE": ["writer"],
                "READ": ["reader"],
                "MULTI": ["summariser", "analyser"]
            }
            selected_agents = intent_to_agents.get(detected_intent, ["qa"])

        predefined_configs = get_predefined_configs()
        agents_and_tasks = []

        for agent_key in selected_agents:
            if agent_key in predefined_configs:
                config = predefined_configs[agent_key]
                task_desc = f"Document context:\n{context}\n\nTask: {user_message}"
                expected = "A thorough, well-structured response based only on the document context"

                agent, task = build_crew_agent(
                    role=config["role"],
                    goal=config["goal"],
                    backstory=config["backstory"],
                    task_description=task_desc,
                    expected_output=expected
                )
                agents_and_tasks.append((agent, task))

        result = run_crew(agents_and_tasks)

        return {
            "intent": detected_intent,
            "response": result,
            "agents_used": selected_agents,
            "chunks_used": len(search_results)
        }

