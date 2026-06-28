from typing import Optional
import sys
from ai.agents.base_agent import BBLBaseAgent
from ai.agents.writer import BBLWriterAgent
from ai.agents.auditor import BBLAuditorAgent
from ai.agents.explainer import BBLExplainerAgent
from ai.agents.browser_tool import BBLBrowserTool
from ai.guro.guro_agent import BBLGuroAgent

class BBLOrchestrator(BBLBaseAgent):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.writer = BBLWriterAgent(self.api_key)
        self.auditor = BBLAuditorAgent(self.api_key)
        self.explainer = BBLExplainerAgent(self.api_key)
        self.guro = BBLGuroAgent(self.api_key)
        self.browser = BBLBrowserTool()

    def explain(self, source_code: str) -> str:
        return self.explainer.explain(source_code)

    def audit(self, source_code: str) -> str:
        return self.auditor.audit(source_code)

    def write(self, prompt: str) -> str:
        # If browser tool is active, let's check if we can search
        enriched_prompt = prompt
        if self.browser.is_available():
            try:
                search_query = self._check_web_search_need(prompt)
                if search_query:
                    print(f"Web search initiated via auto-browser: '{search_query}'...", file=sys.stderr)
                    web_context = self.browser.search(search_query)
                    enriched_prompt = f"{prompt}\n\n[Real-time Web Search Results Context for reference]:\n{web_context}"
            except Exception:
                pass
        return self.writer.write(enriched_prompt)

    def _check_web_search_need(self, query: str) -> Optional[str]:
        """Helper to decide if query needs web search and extract the search query."""
        search_decision_prompt = (
            "You are a search coordinator for a programming assistant.\n"
            "Analyze the user's query and decide if answering it requires looking up real-time web documentation or search results (e.g. latest updates, library API details, third-party libraries like Hardhat, libraries syntax, etc.).\n"
            "Respond with 'YES' on the first line and the search query on the second line if it needs search.\n"
            "Respond with 'NO' if it doesn't need search.\n"
            "Output ONLY the decision."
        )
        try:
            decision_res = self._call_gemini(search_decision_prompt, f"Query: {query}")
            lines = [line.strip() for line in decision_res.strip().splitlines() if line.strip()]
            if lines and lines[0].upper() == "YES" and len(lines) > 1:
                return lines[1]
        except Exception:
            pass
        return None

    def route_and_resolve(self, query: str, context_code: Optional[str] = None) -> str:
        """Semantically routes general developer queries to the correct sub-agent."""
        return self.route_and_resolve_detailed(query, context_code)["response"]

    def route_and_resolve_detailed(self, query: str, context_code: Optional[str] = None) -> dict:
        """Semantically routes general developer queries and returns routing details."""
        # 1. Check if we need real-time information via auto-browser
        web_context = ""
        browser_used = False
        if self.browser.is_available():
            try:
                search_query = self._check_web_search_need(query)
                if search_query:
                    print(f"Web search initiated via auto-browser: '{search_query}'...", file=sys.stderr)
                    web_context = self.browser.search(search_query)
                    browser_used = True
            except Exception:
                pass

        # 2. Classify intent to route to the correct specialized sub-agent
        system_prompt = (
            "You are the Router for the BBL Multi-Agent AI system.\n"
            "Given a developer query, classify it into one of these categories:\n"
            "- 'write': Requests to generate, write, code, implement, or construct code.\n"
            "- 'audit': Requests to check, debug, audit, analyze, optimize, or find bugs.\n"
            "- 'explain': Requests to explain, describe, translate, teach, or detail how code works.\n"
            "Respond ONLY with one of the words: 'write', 'audit', or 'explain'."
        )
        user_prompt = f"User query: {query}"
        routing_decision = self._call_gemini(system_prompt, user_prompt).strip().lower()
        
        # Enrich user prompt with web context if available
        final_query = query
        if web_context:
            final_query = f"{query}\n\n[Real-time Web Search Results Context for reference]:\n{web_context}"

        if "write" in routing_decision:
            res = self.writer.write(final_query)
            route = "writer"
        elif "audit" in routing_decision:
            code = context_code or final_query
            res = self.auditor.audit(code)
            route = "auditor"
        else:
            code = context_code or final_query
            res = self.explainer.explain(code)
            route = "explainer"

        return {
            "response": res,
            "route": route,
            "browser_used": browser_used
        }
