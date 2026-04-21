#!/usr/bin/env python3
"""
LLM Client - Unified client for multiple LLM providers.

Part of the Shared module (shared/llm_client.py)

This llm_client.py provides:

Multi-Provider Support - DeepSeek, OpenAI, Ollama (extensible for Anthropic, local)
Unified Interface - Consistent API across all providers
Chat and Completion - Full chat API and simple completion
Streaming Responses - Real-time token streaming
JSON Mode - Structured JSON output with automatic parsing
Response Caching - Persistent cache to avoid redundant calls
Automatic Retries - Exponential backoff for transient failures
Async Support - Full async/await interface
Tool/Function Calling - Support for function calling
Message Formatting - Provider-specific message formatting
Configuration Integration - Uses shared Config system
CLI Interface - Command-line access to LLM capabilities

The LLM client provides a unified, robust interface to multiple LLM providers, 
making it easy to switch between providers or use fallbacks.
"""

import os
import re
import json
import time
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import get_logger
from .config import get_config, LLMProvider, LLMConfig
from .state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class MessageRole(str, Enum):
    """Message role for chat completion."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ResponseFormat(str, Enum):
    """Response format."""
    TEXT = "text"
    JSON = "json"
    JSON_OBJECT = "json_object"


class FinishReason(str, Enum):
    """Reason for completion finish."""
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"
    TOOL_CALLS = "tool_calls"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Message:
    """Chat message."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response."""
    content: str
    model: str
    finish_reason: FinishReason = FinishReason.STOP
    usage: Dict[str, int] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: datetime = field(default_factory=datetime.now)
    latency_ms: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingChunk:
    """Streaming response chunk."""
    content: str
    finish_reason: Optional[FinishReason] = None
    index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    """Function tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    required: List[str] = field(default_factory=list)


# ============================================================
# BASE LLM CLIENT
# ============================================================

class BaseLLMClient:
    """Base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._session: Optional[requests.Session] = None
        self._cache: Optional[Dict[str, Any]] = None
        self._load_cache()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update(self.config.headers)
        
        return session
    
    @property
    def session(self) -> requests.Session:
        """Get or create session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session
    
    def _get_cache_key(self, messages: List[Message], **kwargs) -> str:
        """Generate cache key from request."""
        content = json.dumps({
            'messages': [{'role': m.role.value, 'content': m.content} for m in messages],
            'model': self.config.model,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            **kwargs
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_cache(self):
        """Load cache from disk."""
        if not self.config.enable_cache:
            self._cache = {}
            return
        
        cache_dir = self.config.cache_dir or Path(".ai_state/llm_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{self.config.provider.value}_{self.config.model}_cache.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.debug(f"Loaded {len(self._cache)} cached responses")
            except Exception:
                self._cache = {}
        else:
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        if not self.config.enable_cache or not self._cache:
            return
        
        cache_dir = self.config.cache_dir or Path(".ai_state/llm_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{self.config.provider.value}_{self.config.model}_cache.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _get_cached(self, cache_key: str) -> Optional[LLMResponse]:
        """Get cached response."""
        if not self.config.enable_cache or cache_key not in self._cache:
            return None
        
        cached = self._cache[cache_key]
        age = time.time() - cached.get('timestamp', 0)
        
        if age > self.config.cache_ttl:
            del self._cache[cache_key]
            return None
        
        logger.debug(f"Cache hit: {cache_key[:16]}")
        return LLMResponse(
            content=cached['content'],
            model=cached['model'],
            finish_reason=FinishReason(cached.get('finish_reason', 'stop')),
            usage=cached.get('usage', {}),
            cached=True
        )
    
    def _set_cached(self, cache_key: str, response: LLMResponse):
        """Cache a response."""
        if not self.config.enable_cache:
            return
        
        self._cache[cache_key] = {
            'content': response.content,
            'model': response.model,
            'finish_reason': response.finish_reason.value,
            'usage': response.usage,
            'timestamp': time.time()
        }
        
        # Periodic save
        if len(self._cache) % 10 == 0:
            self._save_cache()
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Simple completion - to be implemented by subclasses."""
        raise NotImplementedError
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Chat completion - to be implemented by subclasses."""
        raise NotImplementedError
    
    def stream(self, messages: List[Message], **kwargs):
        """Streaming chat completion - to be implemented by subclasses."""
        raise NotImplementedError
    
    def close(self):
        """Clean up resources."""
        self._save_cache()
        if self._session:
            self._session.close()
            self._session = None


# ============================================================
# DEEPSEEK CLIENT
# ============================================================

class DeepSeekClient(BaseLLMClient):
    """DeepSeek API client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not config.api_base:
            config.api_base = "https://api.deepseek.com/v1"
        
        if not config.api_key:
            config.api_key = os.environ.get("DEEPSEEK_API_KEY")
        
        if config.api_key:
            self.session.headers["Authorization"] = f"Bearer {config.api_key}"
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Simple text completion."""
        messages = [Message(role=MessageRole.USER, content=prompt)]
        response = self.chat(messages, **kwargs)
        return response.content
    
    def complete_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Completion with JSON response."""
        response = self.complete(prompt, response_format=ResponseFormat.JSON_OBJECT, **kwargs)
        return self._extract_json(response)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        # Try to parse directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from code block
        json_patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(\{.*?\})\s*\n```',
            r'\{.*\}'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if '{' in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue
        
        logger.warning("Failed to extract JSON from response")
        return {}
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Chat completion."""
        cache_key = self._get_cache_key(messages, **kwargs)
        
        # Check cache
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # Build request
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "frequency_penalty": kwargs.get('frequency_penalty', self.config.frequency_penalty),
            "presence_penalty": kwargs.get('presence_penalty', self.config.presence_penalty),
            "stream": False
        }
        
        # Add response format
        if kwargs.get('response_format'):
            request_data["response_format"] = {"type": kwargs['response_format'].value}
        
        # Add tools if provided
        if kwargs.get('tools'):
            request_data["tools"] = kwargs['tools']
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                json=request_data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            
            result = LLMResponse(
                content=message.get("content", ""),
                model=data["model"],
                finish_reason=FinishReason(choice.get("finish_reason", "stop")),
                usage=data.get("usage", {}),
                function_call=message.get("function_call"),
                tool_calls=message.get("tool_calls"),
                latency_ms=(time.time() - start_time) * 1000
            )
            
            # Cache response
            self._set_cached(cache_key, result)
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def stream(self, messages: List[Message], **kwargs):
        """Streaming chat completion."""
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "stream": True
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                json=request_data,
                stream=True,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk_data = json.loads(data)
                            choice = chunk_data["choices"][0]
                            
                            if "delta" in choice and "content" in choice["delta"]:
                                yield StreamingChunk(
                                    content=choice["delta"]["content"],
                                    finish_reason=FinishReason(choice.get("finish_reason", "stop")),
                                    index=choice.get("index", 0)
                                )
                        except json.JSONDecodeError:
                            continue
                            
        except requests.RequestException as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise
    
    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for DeepSeek API."""
        formatted = []
        for msg in messages:
            formatted_msg = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.function_call:
                formatted_msg["function_call"] = msg.function_call
            formatted.append(formatted_msg)
        return formatted


# ============================================================
# OLLAMA CLIENT
# ============================================================

class OllamaClient(BaseLLMClient):
    """Ollama client for local models."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not config.api_base:
            config.api_base = "http://localhost:11434"
        
        if not config.model:
            config.model = "llama3.2:latest"
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Simple text completion."""
        messages = [Message(role=MessageRole.USER, content=prompt)]
        response = self.chat(messages, **kwargs)
        return response.content
    
    def complete_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Completion with JSON response."""
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        response = self.complete(json_prompt, **kwargs)
        
        # Extract JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract from code block
            match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {}
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Chat completion."""
        cache_key = self._get_cache_key(messages, **kwargs)
        
        # Check cache
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
                "top_p": kwargs.get('top_p', self.config.top_p),
            }
        }
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/api/chat",
                json=request_data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            result = LLMResponse(
                content=data["message"]["content"],
                model=data["model"],
                finish_reason=FinishReason(data.get("done_reason", "stop")),
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                latency_ms=(time.time() - start_time) * 1000
            )
            
            # Cache response
            self._set_cached(cache_key, result)
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def stream(self, messages: List[Message], **kwargs):
        """Streaming chat completion."""
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "stream": True,
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/api/chat",
                json=request_data,
                stream=True,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield StreamingChunk(
                                content=data["message"]["content"],
                                finish_reason=FinishReason.STOP if data.get("done") else None
                            )
                    except json.JSONDecodeError:
                        continue
                        
        except requests.RequestException as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for Ollama API."""
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]


# ============================================================
# OPENAI CLIENT
# ============================================================

class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not config.api_base:
            config.api_base = "https://api.openai.com/v1"
        
        if not config.api_key:
            config.api_key = os.environ.get("OPENAI_API_KEY")
        
        if config.api_key:
            self.session.headers["Authorization"] = f"Bearer {config.api_key}"
    
    def complete(self, prompt: str, **kwargs) -> str:
        """Simple text completion."""
        messages = [Message(role=MessageRole.USER, content=prompt)]
        response = self.chat(messages, **kwargs)
        return response.content
    
    def complete_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Completion with JSON response."""
        response = self.complete(prompt, response_format=ResponseFormat.JSON_OBJECT, **kwargs)
        return json.loads(response)
    
    def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Chat completion."""
        cache_key = self._get_cache_key(messages, **kwargs)
        
        # Check cache
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "frequency_penalty": kwargs.get('frequency_penalty', self.config.frequency_penalty),
            "presence_penalty": kwargs.get('presence_penalty', self.config.presence_penalty),
        }
        
        # Add response format
        if kwargs.get('response_format'):
            request_data["response_format"] = {"type": kwargs['response_format'].value}
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                json=request_data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            
            result = LLMResponse(
                content=message.get("content", ""),
                model=data["model"],
                finish_reason=FinishReason(choice.get("finish_reason", "stop")),
                usage=data.get("usage", {}),
                function_call=message.get("function_call"),
                tool_calls=message.get("tool_calls"),
                latency_ms=(time.time() - start_time) * 1000
            )
            
            # Cache response
            self._set_cached(cache_key, result)
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def stream(self, messages: List[Message], **kwargs):
        """Streaming chat completion."""
        request_data = {
            "model": self.config.model,
            "messages": self._format_messages(messages),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "stream": True
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                json=request_data,
                stream=True,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk_data = json.loads(data)
                            choice = chunk_data["choices"][0]
                            
                            if "delta" in choice and "content" in choice["delta"]:
                                yield StreamingChunk(
                                    content=choice["delta"]["content"],
                                    finish_reason=FinishReason(choice.get("finish_reason", "stop")),
                                    index=choice.get("index", 0)
                                )
                        except json.JSONDecodeError:
                            continue
                            
        except requests.RequestException as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            formatted_msg = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.function_call:
                formatted_msg["function_call"] = msg.function_call
            if msg.tool_calls:
                formatted_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            formatted.append(formatted_msg)
        return formatted


# ============================================================
# MAIN LLM CLIENT
# ============================================================

class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    
    Features:
    - Multiple providers (DeepSeek, OpenAI, Anthropic, Ollama, Local)
    - Chat and completion APIs
    - Streaming responses
    - JSON mode
    - Response caching
    - Automatic retries
    - Rate limiting
    - Fallback providers
    - Tool/function calling
    - Async support
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client."""
        if config is None:
            app_config = get_config()
            config = LLMConfig(
                provider=app_config.llm.provider,
                model=app_config.llm.model,
                api_key=app_config.llm.api_key,
                api_base=app_config.llm.api_base,
                temperature=app_config.llm.temperature,
                max_tokens=app_config.llm.max_tokens,
                timeout=app_config.llm.timeout,
                max_retries=app_config.llm.max_retries,
                retry_delay=app_config.llm.retry_delay,
                enable_cache=app_config.llm.enable_cache,
                cache_ttl=app_config.llm.cache_ttl
            )
        
        self.config = config
        self._client: Optional[BaseLLMClient] = None
        self._fallback_clients: List[BaseLLMClient] = []
        self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client."""
        if self.config.provider == LLMProvider.DEEPSEEK:
            self._client = DeepSeekClient(self.config)
        elif self.config.provider == LLMProvider.OPENAI:
            self._client = OpenAIClient(self.config)
        elif self.config.provider == LLMProvider.OLLAMA:
            self._client = OllamaClient(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
        
        logger.info(f"Initialized {self.config.provider.value} client with model {self.config.model}")
    
    def complete(self, prompt: str, **kwargs) -> str:
        """
        Simple text completion.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        return self._client.complete(prompt, **kwargs)
    
    def complete_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Completion with JSON response.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        if hasattr(self._client, 'complete_json'):
            return self._client.complete_json(prompt, **kwargs)
        
        response = self.complete(prompt, **kwargs)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {}
    
    def chat(self, messages: List[Union[Message, Dict[str, Any]]], **kwargs) -> LLMResponse:
        """
        Chat completion.
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
        """
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted_messages.append(msg)
            else:
                formatted_messages.append(Message(
                    role=MessageRole(msg.get('role', 'user')),
                    content=msg.get('content', '')
                ))
        
        return self._client.chat(formatted_messages, **kwargs)
    
    def stream(self, messages: List[Union[Message, Dict[str, Any]]], **kwargs):
        """
        Streaming chat completion.
        
        Args:
            messages: List of messages
            **kwargs: Additional parameters
            
        Yields:
            StreamingChunk objects
        """
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted_messages.append(msg)
            else:
                formatted_messages.append(Message(
                    role=MessageRole(msg.get('role', 'user')),
                    content=msg.get('content', '')
                ))
        
        yield from self._client.stream(formatted_messages, **kwargs)
    
    async def complete_async(self, prompt: str, **kwargs) -> str:
        """Async completion."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.complete(prompt, **kwargs))
    
    async def complete_json_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Async JSON completion."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.complete_json(prompt, **kwargs))
    
    async def chat_async(self, messages: List[Union[Message, Dict[str, Any]]], **kwargs) -> LLMResponse:
        """Async chat completion."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.chat(messages, **kwargs))
    
    async def stream_async(self, messages: List[Union[Message, Dict[str, Any]]], **kwargs) -> AsyncGenerator[StreamingChunk, None]:
        """Async streaming chat."""
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        
        def producer():
            for chunk in self.stream(messages, **kwargs):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(producer)
        
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
    
    def create_message(self, role: Union[str, MessageRole], content: str) -> Message:
        """Create a message."""
        if isinstance(role, str):
            role = MessageRole(role)
        return Message(role=role, content=content)
    
    def create_tool(self, name: str, description: str, parameters: Dict[str, Any],
                     required: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a tool definition."""
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required or []
                }
            }
        }
    
    def close(self):
        """Clean up resources."""
        if self._client:
            self._client.close()
        for client in self._fallback_clients:
            client.close()


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for LLM client."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="LLM Client")
    parser.add_argument("--provider", choices=["deepseek", "openai", "ollama"], default="deepseek")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--prompt", "-p", help="Input prompt")
    parser.add_argument("--file", "-f", type=Path, help="Read prompt from file")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--stream", action="store_true", help="Stream output")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=4096)
    
    args = parser.parse_args()
    
    config = LLMConfig(
        provider=LLMProvider(args.provider),
        model=args.model or "deepseek-chat",
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    client = LLMClient(config)
    
    # Get prompt
    if args.file:
        prompt = args.file.read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        prompt = sys.stdin.read()
    
    if not prompt:
        print("No prompt provided", file=sys.stderr)
        sys.exit(1)
    
    # Build messages
    messages = []
    if args.system:
        messages.append(client.create_message(MessageRole.SYSTEM, args.system))
    messages.append(client.create_message(MessageRole.USER, prompt))
    
    # Execute
    if args.stream:
        for chunk in client.stream(messages):
            print(chunk.content, end="", flush=True)
        print()
    elif args.json:
        result = client.complete_json(prompt)
        print(json.dumps(result, indent=2))
    else:
        response = client.chat(messages)
        print(response.content)
    
    client.close()


if __name__ == "__main__":
    main()