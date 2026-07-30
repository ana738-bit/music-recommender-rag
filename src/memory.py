from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ─── Conversation Memory Class ────────────────────────────
class ConversationMemory:
    def __init__(self, k: int = 5):
        self.k = k
        self.history = []

    def save(self, user_query: str, ai_response: str):
        self.history.append({
            "user": user_query,
            "dj":   ai_response
        })
        if len(self.history) > self.k:
            self.history = self.history[-self.k:]
        print(f"Memory saved ({len(self.history)}/{self.k} exchanges)")

    def format(self) -> str:
        if not self.history:
            return "No previous conversation."
        lines = []
        for exchange in self.history:
            lines.append(f"User: {exchange['user']}")
            lines.append(f"DJ:   {exchange['dj'][:100]}...")
        return "\n".join(lines)

    def clear(self):
        self.history = []
        print("Memory cleared")

    def is_empty(self) -> bool:
        return len(self.history) == 0


# ─── Session-based Memory Store ───────────────────────────
_memory_store: dict = {}


def get_memory(session_id: str = "default") -> ConversationMemory:
    """
    Returns memory instance for the given session_id.
    Creates a new one if it doesn't exist yet.
    Called by chain.py with session_id from app.py.
    """
    global _memory_store
    if session_id not in _memory_store:
        _memory_store[session_id] = ConversationMemory(k=5)
        print(f"New memory created for session: {session_id}")
    return _memory_store[session_id]


def reset_memory(session_id: str = "default"):
    """
    Resets memory for a specific session only.
    Called by /clear-memory endpoint in backend/main.py.
    """
    global _memory_store
    if session_id in _memory_store:
        _memory_store[session_id].clear()
        print(f"Memory reset for session: {session_id}")
    else:
        print(f"⚠️ No memory found for session: {session_id}")


def get_all_sessions() -> list:
    """Returns list of all active session IDs. For debugging."""
    return list(_memory_store.keys())


# ─── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing session-based memory...\n")

    # Test separate sessions
    mem_a = get_memory("user_alice")
    mem_b = get_memory("user_bob")

    mem_a.save("sad songs", "Here are melancholic songs...")
    mem_b.save("party songs", "Here are upbeat songs...")

    print("Alice's memory:")
    print(mem_a.format())
    print("\nBob's memory:")
    print(mem_b.format())

    # Verify they are isolated
    assert "party" not in mem_a.format()
    assert "sad" not in mem_b.format()
    print("\n Sessions are isolated correctly")

    # Test reset
    reset_memory("user_alice")
    print(f"\nAlice after reset: {mem_a.format()}")
    print("\n memory.py complete!")
