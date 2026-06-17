# -*- coding: utf-8 -*-
"""
app.core.llm_adapter — LLM 适配器
==================================
抽象类 LLMAdapter + 三个实现: OpenAI / Ollama / Mock
"""
import json
import re
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from ..config import settings
from ..utils.logger import get_logger
from .mock_data import get_mock_story, get_mock_refactor

log = get_logger("core.llm_adapter")


class LLMAdapter(ABC):
    """LLM 适配器抽象类"""

    @abstractmethod
    def generate_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成函数故事"""
        pass

    @abstractmethod
    def generate_refactor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成重构建议"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名"""
        pass

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从 LLM 输出中提取 JSON"""
        if not text:
            return None
        # 尝试 ```json ... ``` 包裹
        m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # 尝试 ``` ... ``` 包裹
        m = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # 尝试裸 JSON
        try:
            return json.loads(text)
        except Exception:
            pass
        return None


class MockAdapter(LLMAdapter):
    """Mock 适配器: 返回预置的演示文本"""

    @property
    def model_name(self) -> str:
        return "mock"

    def generate_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        log.info("MockAdapter.generate_story: %s", context.get("function_name"))
        fn = context.get("function_name", "")
        fp = context.get("file_path", "")
        return get_mock_story(fn, fp)

    def generate_refactor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        log.info("MockAdapter.generate_refactor: %s", context.get("function_name"))
        fn = context.get("function_name", "")
        fp = context.get("file_path", "")
        return get_mock_refactor(fn, fp)


class OpenAIAdapter(LLMAdapter):
    """OpenAI 适配器"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout
        self._client = None

    @property
    def model_name(self) -> str:
        return f"openai-{self.model}"

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY 未设置")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
            return self._client
        except ImportError:
            log.error("openai 库未安装")
            return None

    def _call(self, prompt: str) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return None
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名资深代码考古学家, 输出严格 JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1500,
            )
            text = resp.choices[0].message.content
            return self._extract_json(text)
        except Exception as e:
            log.error("OpenAI 调用失败: %s", e)
            return None

    def generate_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from .prompts import STORY_PROMPT
        prompt = STORY_PROMPT.format(
            function_name=context.get("function_name", ""),
            file_path=context.get("file_path", ""),
            start_line=context.get("start_line", 0),
            end_line=context.get("end_line", 0),
            line_count=context.get("line_count", 0),
            complexity=context.get("complexity", 1),
            class_name=context.get("class_name", ""),
            code=context.get("code", ""),
            blame=context.get("blame", ""),
            timeline=context.get("timeline", ""),
            callers=context.get("callers", ""),
            callees=context.get("callees", ""),
        )
        result = self._call(prompt)
        if not result:
            log.warning("OpenAI 调用失败, 降级到 Mock")
            return get_mock_story(context.get("function_name", ""), context.get("file_path", ""))
        result["node_id"] = context.get("node_id", "")
        result["model"] = self.model_name
        from datetime import datetime, timezone
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        return result

    def generate_refactor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from .prompts import REFACTOR_PROMPT
        prompt = REFACTOR_PROMPT.format(
            function_name=context.get("function_name", ""),
            file_path=context.get("file_path", ""),
            start_line=context.get("start_line", 0),
            end_line=context.get("end_line", 0),
            line_count=context.get("line_count", 0),
            complexity=context.get("complexity", 1),
            cc_rating=context.get("cc_rating", ""),
            code=context.get("code", ""),
            callers=context.get("callers", ""),
            callees=context.get("callees", ""),
            siblings=context.get("siblings", ""),
        )
        result = self._call(prompt)
        if not result:
            log.warning("OpenAI 调用失败, 降级到 Mock")
            return get_mock_refactor(context.get("function_name", ""), context.get("file_path", ""))
        result["node_id"] = context.get("node_id", "")
        return result


class OllamaAdapter(LLMAdapter):
    """Ollama 适配器, 用 HTTP POST"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 timeout: float = 60.0):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return f"ollama-{self.model}"

    def _call(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            import httpx
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.4},
            }
            r = httpx.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            text = data.get("response", "")
            return self._extract_json(text)
        except Exception as e:
            log.error("Ollama 调用失败: %s", e)
            return None

    def generate_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from .prompts import STORY_PROMPT
        prompt = STORY_PROMPT.format(
            function_name=context.get("function_name", ""),
            file_path=context.get("file_path", ""),
            start_line=context.get("start_line", 0),
            end_line=context.get("end_line", 0),
            line_count=context.get("line_count", 0),
            complexity=context.get("complexity", 1),
            class_name=context.get("class_name", ""),
            code=context.get("code", ""),
            blame=context.get("blame", ""),
            timeline=context.get("timeline", ""),
            callers=context.get("callers", ""),
            callees=context.get("callees", ""),
        )
        result = self._call(prompt)
        if not result:
            log.warning("Ollama 调用失败, 降级到 Mock")
            return get_mock_story(context.get("function_name", ""), context.get("file_path", ""))
        result["node_id"] = context.get("node_id", "")
        result["model"] = self.model_name
        from datetime import datetime, timezone
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        return result

    def generate_refactor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from .prompts import REFACTOR_PROMPT
        prompt = REFACTOR_PROMPT.format(
            function_name=context.get("function_name", ""),
            file_path=context.get("file_path", ""),
            start_line=context.get("start_line", 0),
            end_line=context.get("end_line", 0),
            line_count=context.get("line_count", 0),
            complexity=context.get("complexity", 1),
            cc_rating=context.get("cc_rating", ""),
            code=context.get("code", ""),
            callers=context.get("callers", ""),
            callees=context.get("callees", ""),
            siblings=context.get("siblings", ""),
        )
        result = self._call(prompt)
        if not result:
            log.warning("Ollama 调用失败, 降级到 Mock")
            return get_mock_refactor(context.get("function_name", ""), context.get("file_path", ""))
        result["node_id"] = context.get("node_id", "")
        return result


def get_adapter(mode: Optional[str] = None) -> LLMAdapter:
    """工厂方法: 根据配置返回对应 adapter"""
    mode = (mode or settings.LLM_MODE or "mock").lower()
    if mode == "openai" and settings.OPENAI_API_KEY:
        try:
            return OpenAIAdapter()
        except Exception as e:
            log.warning("OpenAI 初始化失败: %s, 降级到 Mock", e)
    elif mode == "ollama":
        try:
            return OllamaAdapter()
        except Exception as e:
            log.warning("Ollama 初始化失败: %s, 降级到 Mock", e)
    log.warning("LLM 模式: %s, 无可用后端, 使用 MockAdapter", mode)
    return MockAdapter()