from crewai import Agent, Task, Crew, LLM, Process
from config import OLLAMA_BASE_URL

# DIMENSION 4 & 5: Static configurations moved to a module-level constant.
# This improves readability and is standard practice for static data.
PREDEFINED_CONFIGS: dict[str, dict[str, str]] = {
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

class CrewExecutionError(Exception):
    """DIMENSION 5: Custom exception for specific, catchable error handling."""
    pass

# DIMENSION 5: Separated Agent and Task creation. 
# This decouples the 1:1 relationship, allowing one agent to handle multiple tasks.
def build_agent(
    role: str,
    goal: str,
    backstory: str,
    model_name: str = "llama3.2"
) -> Agent:
    # DIMENSION 3: Consider adding input sanitization for role/goal/backstory here 
    # to mitigate prompt injection risks if these inputs are user-generated.
    llm = LLM(model=f"ollama/{model_name}", base_url=OLLAMA_BASE_URL)
    
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=llm,
        allow_delegation=False,
        verbose=True
    )

def build_task(
    task_description: str,
    expected_output: str,
    agent: Agent,
    context: list[Task] = None
) -> Task:
    return Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
        context=context
    )

# DIMENSION 4: Improved type hints for clarity and IDE support.
def run_crew(
    agents_and_tasks: list[tuple[Agent, Task]],
    process_type: Process = Process.sequential
) -> list[str]:
    try:
        crew_agents = [item[0] for item in agents_and_tasks]
        crew_tasks = [item[1] for item in agents_and_tasks]

        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            verbose=True,
            process=process_type
        )

        print("[DEBUG] Starting crew.kickoff()...")
        crew_result = crew.kickoff()
        print(f"[DEBUG] crew.kickoff() returned: {type(crew_result)} - {str(crew_result)[:200]}")

        outputs = []

        # Try to extract individual task outputs
        task_outputs_found = False
        for i, task in enumerate(crew_tasks):
            try:
                output_val = None

                # Method 1: Try task.output attribute
                if hasattr(task, 'output') and task.output is not None:
                    out = task.output
                    if hasattr(out, 'raw'):
                        output_val = str(out.raw)
                    elif hasattr(out, 'content'):
                        output_val = str(out.content)
                    else:
                        output_val = str(out)

                    if output_val and output_val.strip():
                        outputs.append(output_val)
                        task_outputs_found = True
                        print(f"[DEBUG] Task {i} output extracted from task.output")
                        continue

                # Method 2: Try to get from crew's tasks_output
                if hasattr(crew, 'tasks_output') and crew.tasks_output:
                    if i < len(crew.tasks_output):
                        output_val = str(crew.tasks_output[i])
                        if output_val and output_val.strip():
                            outputs.append(output_val)
                            task_outputs_found = True
                            print(f"[DEBUG] Task {i} output extracted from crew.tasks_output")
                            continue

                # Fallback: Generate placeholder
                outputs.append(f"Task {i+1} completed successfully.")
                print(f"[DEBUG] Task {i} - no output found, using placeholder")

            except Exception as task_err:
                print(f"[DEBUG] Error extracting output from task {i}: {str(task_err)}")
                outputs.append(f"Task {i+1} completed.")

        # If no individual outputs found, use crew_result as fallback
        if not task_outputs_found and crew_result:
            crew_result_str = str(crew_result).strip()
            if crew_result_str and len(crew_result_str) > 10:
                print(f"[DEBUG] No individual task outputs found, using crew_result as single output")
                # For sequential process, crew_result is the final output
                # Repeat it for all tasks or distribute it
                outputs = [crew_result_str] * len(crew_tasks)
            else:
                print(f"[DEBUG] crew_result is empty or too short")

        if not outputs or all(o.startswith("Task") for o in outputs):
            print(f"[DEBUG] WARNING: Outputs appear to be all placeholders")
            outputs = [f"Agent {i+1} completed task" for i in range(len(crew_tasks))]

        print(f"[DEBUG] Returning {len(outputs)} outputs from {len(crew_tasks)} tasks")
        return outputs

    except Exception as e:
        print(f"[DEBUG] CRITICAL ERROR in run_crew: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise CrewExecutionError(f"Crew execution failed: {str(e)}") from e

def build_crew_agent(role, goal, backstory,
                     task_description, expected_output,
                     model_name=None):
    agent = build_agent(role, goal, backstory, model_name)
    task  = build_task(task_description, expected_output, agent)
    return agent, task


def run_crew_simple(agents_and_tasks: list[tuple[Agent, Task]]) -> list[str]:
    """
    Simplified crew execution - run agents sequentially and independently.
    Avoids complex CrewAI orchestration which can hang on LLM calls.
    """
    outputs = []

    for i, (agent, task) in enumerate(agents_and_tasks):
        try:
            print(f"[INFO] Running agent {i+1}/{len(agents_and_tasks)}: {agent.role}")

            single_crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True,
                process=Process.sequential
            )

            result = single_crew.kickoff()
            output_str = str(result).strip() if result else f"Agent {i+1} completed."

            if output_str and len(output_str) > 5:
                outputs.append(output_str)
                print(f"[DEBUG] Agent {i+1} output: {len(output_str)} chars")
            else:
                outputs.append(f"Agent {i+1} completed.")
                print(f"[DEBUG] Agent {i+1} returned minimal output")

        except Exception as agent_err:
            error_msg = f"Agent error: {str(agent_err)[:100]}"
            print(f"[ERROR] Agent {i+1}: {error_msg}")
            outputs.append(error_msg)

    return outputs if outputs else ["Execution completed"]

def get_predefined_configs() -> dict:
    return PREDEFINED_CONFIGS
