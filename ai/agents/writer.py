from ai.agents.base_agent import BBLBaseAgent

class BBLWriterAgent(BBLBaseAgent):
    def write(self, prompt: str) -> str:
        """Generates clean BBL code matching user prompts."""
        system_prompt = self.SYSTEM_INSTRUCTION + (
            "\nYour role is code generation. Output clean, syntactically-correct BBL code matching the user's requirements.\n"
            "Include comments explaining your design choices, and make sure contracts use the correct Tagalog keywords.\n"
            "Never output target languages (like JS or Python) unless explicitly asked; output BBL."
        )
        user_prompt = f"Write BBL code for: {prompt}"
        return self._call_gemini(system_prompt, user_prompt)
