from agents.crew_builder import build_agent, build_task, run_crew

def main():
    agent = build_agent("Tester", "Test the system", "You are a test agent", "llama3.2")
    task = build_task("Say hello world", "A greeting", agent)
    results = run_crew([(agent, task)])
    print(results)

if __name__ == "__main__":
    main()
