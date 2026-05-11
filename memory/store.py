class SessionMemory:
    def __init__(self):
        self.history = []

    def add_turn(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        return self.history

    def get_context_string(self) -> str:
        last_turns = self.history[-5:] if len(self.history) > 5 else self.history
        formatted = "\n".join([f"{turn['role']}: {turn['content']}" for turn in last_turns])
        return formatted

    def clear(self) -> None:
        self.history = []
