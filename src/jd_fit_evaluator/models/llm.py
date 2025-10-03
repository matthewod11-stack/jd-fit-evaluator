from __future__ import annotations
import json, os, http.client, urllib.parse
from dataclasses import dataclass
from typing import Optional, Dict, Any
from jd_fit_evaluator.config import cfg

@dataclass
class LLMResponse:
    text: str
    parsed_json: Optional[Dict[str, Any]] = None

class LLMProvider:
    def chat_json(self, system: str, user: str, schema_hint: Optional[str]=None) -> LLMResponse:
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self, model: str, host: str="http://localhost:11434"):
        self.model, self.host = model, host
    def chat_json(self, system: str, user: str, schema_hint: Optional[str]=None) -> LLMResponse:
        conn = http.client.HTTPConnection(urllib.parse.urlparse(self.host).netloc, timeout=cfg.llm.timeout_s)
        body = {
            "model": self.model,
            "messages": [{"role":"system","content":system},{"role":"user","content":user}],
            "stream": False,
            "options": {"temperature": cfg.llm.temperature}
        }
        conn.request("POST", "/api/chat", body=json.dumps(body), headers={"Content-Type":"application/json"})
        resp = json.loads(conn.getresponse().read())
        text = resp.get("message",{}).get("content","").strip()
        parsed = None
        try: parsed = json.loads(text)
        except Exception:
            if "```json" in text:
                j = text.split("```json",1)[1].split("```",1)[0]
                try: parsed = json.loads(j)
                except Exception: pass
        return LLMResponse(text=text, parsed_json=parsed)

class OpenAIProvider(LLMProvider):
    def __init__(self, model: str):
        self.model = model
        self.key = os.environ.get("OPENAI_API_KEY","")
    def chat_json(self, system: str, user: str, schema_hint: Optional[str]=None) -> LLMResponse:
        import urllib.request
        payload = {
            "model": self.model,
            "messages":[{"role":"system","content":system},{"role":"user","content":user}],
            "temperature": cfg.llm.temperature,
            "max_tokens": cfg.llm.max_tokens
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type":"application/json","Authorization":f"Bearer {self.key}"}
        )
        with urllib.request.urlopen(req, timeout=cfg.llm.timeout_s) as r:
            data = json.loads(r.read())
        text = data["choices"][0]["message"]["content"].strip()
        parsed=None
        try: parsed=json.loads(text)
        except Exception: pass
        return LLMResponse(text=text, parsed_json=parsed)

def get_llm() -> LLMProvider:
    if cfg.llm.provider == "ollama": return OllamaProvider(cfg.llm.model)
    if cfg.llm.provider == "openai": return OpenAIProvider(cfg.llm.model)
    class Mock(LLMProvider):
        def chat_json(self, system, user, schema_hint=None):
            return LLMResponse(text='{"name":"Alex Rivera"}', parsed_json={"name":"Alex Rivera"})
    return Mock()