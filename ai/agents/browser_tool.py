import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Dict, Any

class BBLBrowserTool:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')

    def is_available(self) -> bool:
        """Checks if the auto-browser local controller is running and accessible."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/sessions",
                method="GET"
            )
            # Short timeout to avoid hanging if the service is down
            with urllib.request.urlopen(req, timeout=2.0) as response:
                return response.status == 200
        except Exception:
            return False

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Utility method to perform POST requests to auto-browser."""
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)

    def _get(self, path: str) -> Dict[str, Any]:
        """Utility method to perform GET requests to auto-browser."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15.0) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)

    def fetch_url(self, target_url: str) -> str:
        """Launches a session in auto-browser, navigates to target_url, and retrieves the text content."""
        if not self.is_available():
            return "Error: auto-browser service is not running locally."

        try:
            # 1. Create session
            create_payload = {
                "name": "bbl-fetch",
                "start_url": target_url
            }
            session_data = self._post("/sessions", create_payload)
            session_id = session_data.get("session", {}).get("id") or session_data.get("id")
            
            if not session_id:
                return "Error: Failed to obtain session ID from auto-browser."

            # 2. Observe session to get text excerpt
            # auto-browser observation endpoint returns Dom outline and text excerpts
            observe_data = self._get(f"/sessions/{session_id}/observe?preset=rich")
            
            # Clean up the session so we don't leave zombie containers/tabs
            try:
                cleanup_req = urllib.request.Request(
                    f"{self.base_url}/sessions/{session_id}",
                    method="DELETE"
                )
                with urllib.request.urlopen(cleanup_req, timeout=5.0):
                    pass
            except Exception:
                pass # Silent ignore cleanup failures

            text_excerpt = observe_data.get("text_excerpt", "")
            title = observe_data.get("title", "Untitled")
            
            return f"=== Webpage: {title} ({target_url}) ===\n{text_excerpt}"

        except Exception as e:
            return f"Error connecting to auto-browser: {e}"

    def search(self, query: str) -> str:
        """Performs a Google search using auto-browser and returns the search result page text summary."""
        escaped_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={escaped_query}"
        return self.fetch_url(search_url)
