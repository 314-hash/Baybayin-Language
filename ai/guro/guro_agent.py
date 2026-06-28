import os
import json
from typing import Optional
from ai.agents.base_agent import BBLBaseAgent

class BBLGuroAgent(BBLBaseAgent):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.glossary = {}
        try:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            glossary_path = os.path.join(curr_dir, 'glossary.json')
            if os.path.exists(glossary_path):
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    self.glossary = json.load(f)
        except Exception:
            pass

    def respond(self, query: str, context_code: Optional[str] = None) -> str:
        """Responds to queries as a supportive Tagalog programming mentor."""
        glossary_str = json.dumps(self.glossary, indent=2, ensure_ascii=False)
        
        system_instruction = (
            "You are the 'Guro' (Teacher) Agent for the Baybayin Language (BBL) project.\n"
            "Your role is to act as a friendly, engaging Filipino programming professor and pre-colonial historian.\n"
            "You must explain BBL concepts, VM logic, algorithms, and general programming terms in clean, educational Filipino/Tagalog (or Taglish where appropriate).\n"
            "Always maintain a welcoming, helpful 'guro' persona. Use Tagalog analogies and historic script contexts when relevant.\n"
            "Below is a Tagalog programming glossary you should reference when explaining technical terms:\n"
            f"{glossary_str}\n\n"
            "If code is provided, refer to it to help explain your examples."
        )

        user_content = f"User Query: {query}"
        if context_code:
            user_content += f"\n\n[Active Source Code Context]:\n{context_code}"

        return self._call_gemini(system_instruction, user_content)
