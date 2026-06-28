from ai.agents.base_agent import BBLBaseAgent

class BBLAuditorAgent(BBLBaseAgent):
    def audit(self, source_code: str) -> str:
        """Audits BBL source code for compile safety, types, logic, and Solidity optimization."""
        system_prompt = self.SYSTEM_INSTRUCTION + (
            "\nYour role is code analysis and optimization. Inspect the BBL code for bugs, missing type definitions,\n"
            "Solidity memory decorations, or string comparison flaws (BBL doesn't support == on strings directly, we compile to keccak256).\n"
            "Emit a structured report with recommendations and concrete BBL code replacements."
        )
        user_prompt = f"Please audit this BBL code:\n\n```bbl\n{source_code}\n```"
        return self._call_gemini(system_prompt, user_prompt)
