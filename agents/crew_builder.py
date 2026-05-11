from crewai import Agent, Task, Crew, LLM, Process


def build_crew_agent(
    role: str,
    goal: str,
    backstory: str,
    task_description: str,
    expected_output: str,
    model_name: str = "llama3.2"
) -> tuple[Agent, Task]:
    llm = LLM(model=f"ollama/{model_name}", base_url="http://localhost:11434")
    
    agent = Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=llm,
        allow_delegation=False,
        verbose=True
    )
    
    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent
    )
    
    return (agent, task)


def run_crew(agents_and_tasks: list[tuple]) -> str:
    try:
        crew_agents = [item[0] for item in agents_and_tasks]
        crew_tasks = [item[1] for item in agents_and_tasks]
        
        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error: Crew execution failed. {str(e)}"


def get_predefined_configs() -> dict:
    return {
        "reader": {
            "role": "Document Reader",
            "goal": "Extract and present raw document content",
            "backstory": "Expert at parsing documents faithfully without interpretation"
        },
        "summariser": {
            "role": "Document Summariser",
            "goal": "Produce concise structured summaries",
            "backstory": "Specialist in condensing complex documents into clear summaries"
        },
        "analyser": {
            "role": "Critical Analyst",
            "goal": "Identify themes, patterns and insights",
            "backstory": "Expert analyst finding patterns, contradictions, and key insights"
        },
        "qa": {
            "role": "QA Specialist",
            "goal": "Answer questions precisely from context only",
            "backstory": "Only answers from provided document context, cites sources"
        },
        "writer": {
            "role": "Professional Writer",
            "goal": "Generate well-structured documents",
            "backstory": "Skilled writer producing professional output matching tone and format"
        }
    }
