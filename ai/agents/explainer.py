from ai.agents.base_agent import BBLBaseAgent

class BBLExplainerAgent(BBLBaseAgent):
    def explain(self, source_code: str) -> str:
        """Explains BBL source code line-by-line using natural language."""
        system_prompt = self.SYSTEM_INSTRUCTION + (
            "\nYour role is education and instruction. Break down the user's BBL code line-by-line.\n"
            "Explain Tagalog keyword translations, what structures (like contracts or loops) are doing,\n"
            "and trace the flow of execution. Answer in clear English or Tagalog as appropriate."
        )
        user_prompt = f"Please explain this BBL code:\n\n```bbl\n{source_code}\n```"
        return self._call_gemini(system_prompt, user_prompt)
