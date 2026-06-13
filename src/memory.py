from pathlib import Path
from dotenv import load_dotenv

# ─── Load .env ────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ─── Simple Memory Class ──────────────────────────────────
class ConversationMemory:
    """
    Simple conversation memory that stores
    last k exchanges between user and DJ.
    Does not depend on any LangChain memory class
    to avoid deprecation issues.
    """

    def __init__(self, k: int = 5):
        self.k        = k
        self.history  = []   # list of {"user": ..., "dj": ...}

    def save(self, user_query: str, ai_response: str):
        """Save one exchange to memory."""
        self.history.append({
            "user": user_query,
            "dj":   ai_response
        })
        # Keep only last k exchanges
        if len(self.history) > self.k:
            self.history = self.history[-self.k:]
        print(f" Memory saved ({len(self.history)}/{self.k} exchanges)")

    def format(self) -> str:
        """
        Format history as clean string for prompt injection.
        Called by chain.py before building the prompt.
        """
        if not self.history:
            return "No previous conversation."

        lines = []
        for exchange in self.history:
            lines.append(f"User: {exchange['user']}")
            lines.append(f"DJ:   {exchange['dj'][:100]}...")
        return "\n".join(lines)

    def clear(self):
        """Clear all conversation history."""
        self.history = []
        print(" Memory cleared")

    def is_empty(self) -> bool:
        return len(self.history) == 0


# ─── Global Memory Instance ───────────────────────────────
# Single instance used across the whole app session
_memory_instance = None


def get_memory() -> ConversationMemory:
    """
    Returns the global memory instance.
    Creates it if it doesn't exist yet.
    Called by chain.py and app.py.
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory(k=5)
        print(" Memory initialized")
    return _memory_instance


def reset_memory():
    """Resets the global memory instance."""
    global _memory_instance
    _memory_instance = ConversationMemory(k=5)
    print(" Memory reset")


# ─── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print(" Testing memory.py...\n")

    mem = get_memory()

    # Test save
    print(" Testing save()...")
    mem.save(
        "sad songs for rainy night",
        "Here are some melancholic songs: Cigarette Daydreams, Rainy Day Loop..."
    )
    mem.save(
        "more upbeat please",
        "Switching the vibe! Here are energetic songs: Dance The Night, Boom Boom Pow..."
    )
    print(" save() works\n")

    # Test format
    print(" Testing format()...")
    history = mem.format()
    print(history)
    print("\n format() works\n")

    # Test is_empty
    print(" Testing is_empty()...")
    print(f"Is empty: {mem.is_empty()}")
    print(" is_empty() works\n")

    # Test clear
    print(" Testing clear()...")
    mem.clear()
    print(f"After clear: {mem.format()}")
    print(" clear() works\n")

    # Test k limit
    print(" Testing k=5 limit...")
    for i in range(7):
        mem.save(f"query {i}", f"response {i}")
    print(f"History length after 7 saves: {len(mem.history)} (should be 5)")
    print(" k limit works\n")

    print(" memory.py complete!")