import os
import json
import urllib.request
import urllib.error
from typing import Optional

class BBLBaseAgent:
    SYSTEM_INSTRUCTION = """
You are a specialized agent in the Baybayin Language (BBL) Multi-Agent development ecosystem.
BBL is a Tagalog-inspired programming language featuring:
1. Keywords:
   - `kontrata` (class / contract declaration)
   - `tungkulin` (function declaration)
   - `itakda` (variable declaration)
   - `ibahagi` (public visibility modifier)
   - `ibalik` (return statement)
   - `kung` (if conditional branch)
   - `kundi` (else conditional branch)
   - `habang` (while loop)
   - `tama` (true literal)
   - `mali` (false literal)
   - `wala` (null literal)
   
2. Types:
   - `buo` (integer, uint256 in Solidity, int in Python)
   - `teksto` (string)
   - `kondisyon` (boolean)
   - `alamat` (address)

3. Functions:
   - `ipakita(x)` (logs output)

When generating code, output ONLY valid BBL code blocks.
"""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Nawawala ang GEMINI_API_KEY! Mangyaring itakda ito sa iyong environment variables.\n"
                "Halimbawa sa Windows (PowerShell):\n"
                "  $env:GEMINI_API_KEY=\"iyong_api_key_dito\"\n"
                "Halimbawa sa Command Prompt:\n"
                "  set GEMINI_API_KEY=iyong_api_key_dito"
            )

        # Google API keys start with 'AIzaSy'. OAuth tokens (like 'ya29.' or 'AQ.') should use Bearer header.
        is_oauth = not self.api_key.startswith("AIzaSy")
        
        headers = {"Content-Type": "application/json"}
        if is_oauth:
            headers["Authorization"] = f"Bearer {self.api_key}"
            url = self.api_url
        else:
            url = f"{self.api_url}?key={self.api_key}"
        
        request_body = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        data = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                return text
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_msg)
                message = err_json.get("error", {}).get("message", err_msg)
            except Exception:
                message = err_msg
            raise RuntimeError(f"Gemini API Error (HTTP {e.code}): {message}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Gemini API: {e}")
