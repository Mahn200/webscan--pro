"""
WAF Evasion Engine for WebScan Pro.
Provides stealth mechanisms for bypassing WAF detection during scanning.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Set
from urllib.parse import quote, urlparse

import httpx
from fake_useragent import UserAgent

logger = logging.getLogger("webscanpro.stealth")

# ─── User-Agent Rotation ────────────────────────────────────────────

_ua = UserAgent()
_used_agents: Set[str] = set()


def get_realistic_headers() -> Dict[str, str]:
    """
    Generate realistic HTTP headers with a random User-Agent.
    Rotates through different user agents to avoid fingerprinting.
    """
    user_agent = _get_fresh_user_agent()

    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,tr;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def _get_fresh_user_agent() -> str:
    """Get a fresh user agent, avoiding recently used ones."""
    for _ in range(10):
        try:
            agent = _ua.random
            if agent not in _used_agents:
                _used_agents.add(agent)
                # Keep the set from growing too large
                if len(_used_agents) > 50:
                    _used_agents.clear()
                return agent
        except Exception:
            pass
    # Fallback user agents
    fallbacks = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    return random.choice(fallbacks)


# ─── Stealth Timer ──────────────────────────────────────────────────


class StealthTimer:
    """
    Implements human-like delays between requests to avoid
    triggering rate limiting and behavioral detection.
    """

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def human_delay(self) -> None:
        """
        Wait for a human-like random duration between requests.
        Uses random gaussian-like distribution.
        """
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Stealth delay: {delay:.2f}s")
        await asyncio.sleep(delay)

    async def micro_delay(self) -> None:
        """
        Brief delay between rapid operations (50-200ms).
        Useful between steps of a single request.
        """
        delay = random.uniform(0.05, 0.2)
        await asyncio.sleep(delay)


# ─── Payload Encoder for WAF Evasion ────────────────────────────────


class PayloadEncoder:
    """
    Encodes payloads using various techniques to evade WAF detection.
    """

    @staticmethod
    def url_encode(payload: str) -> str:
        """Basic URL encoding of the payload."""
        return quote(payload)

    @staticmethod
    def double_url_encode(payload: str) -> str:
        """Double URL encoding - bypasses WAFs that decode only once."""
        first_pass = quote(payload)
        return quote(first_pass)

    @staticmethod
    def mixed_case(payload: str) -> str:
        """Random mixed casing for SQL keywords to evade simple pattern matches."""
        result = []
        for char in payload:
            if char.isalpha() and random.choice([True, False]):
                result.append(
                    char.upper() if random.choice([True, False]) else char.lower()
                )
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def comment_injection(payload: str) -> str:
        """Inject inline comments into SQL keywords."""
        # Insert /**/ between characters of SQL keywords
        keywords = [
            "SELECT",
            "UNION",
            "FROM",
            "WHERE",
            "OR",
            "AND",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "SLEEP",
            "BENCHMARK",
        ]
        result = payload
        for keyword in keywords:
            obfuscated = "/**/".join(list(keyword))
            result = result.replace(keyword, obfuscated)
            result = result.replace(keyword.lower(), obfuscated.lower())
        return result

    @staticmethod
    def unicode_escape(payload: str) -> str:
        """Use Unicode escapes for certain characters."""
        # Encode common SQL characters as Unicode escapes
        replacements = {
            "'": "\\u0027",
            '"': "\\u0022",
            "=": "\\u003d",
            " ": "\\u0020",
            ">": "\\u003e",
            "<": "\\u003c",
        }
        result = payload
        for char, escape in replacements.items():
            result = result.replace(char, escape)
        return result

    @staticmethod
    def hex_encode_sql(payload: str) -> str:
        """Hex encode portions of SQL payloads."""
        # Convert parts of the payload to hex
        import re

        def hex_replace(match):
            word = match.group(0)
            return "0x" + word.encode("utf-8").hex()

        # Replace string literals with hex equivalents
        result = re.sub(
            r"'([^']+)'", lambda m: f"0x{m.group(1).encode('utf-8').hex()}", payload
        )
        return result

    @staticmethod
    def html_encode(payload: str) -> str:
        """HTML-encode the payload to evade WAF detection."""
        html_map = {
            "'": "&#39;",
            '"': "&#34;",
            "<": "&#60;",
            ">": "&#62;",
            "&": "&#38;",
        }
        result = ""
        for char in payload:
            result += html_map.get(char, char)
        return result

    @staticmethod
    def tab_substitution(payload: str) -> str:
        """Replace spaces with tab characters."""
        return payload.replace(" ", "\t")

    @classmethod
    def apply_evasion(cls, payload: str, technique: Optional[str] = None) -> str:
        """
        Apply a selected evasion technique.
        If none specified, choose randomly.
        """
        techniques = [
            cls.double_url_encode,
            cls.comment_injection,
            cls.mixed_case,
            cls.hex_encode_sql,
            cls.tab_substitution,
        ]

        if technique == "random":
            encoder = random.choice(techniques)
        elif technique == "all":
            # Apply multiple techniques
            result = payload
            for encoder in techniques:
                result = encoder(result)
            return result
        else:
            encoder = random.choice(techniques)

        return encoder(payload)

    @classmethod
    def generate_variants(cls, payload: str, count: int = 5) -> List[str]:
        """Generate multiple evasive variants of a payload."""
        variants = [payload]
        for _ in range(count - 1):
            variants.append(cls.apply_evasion(payload, "random"))
        return variants


# ─── Stealth Session ────────────────────────────────────────────────


class StealthSession:
    """
    Async context manager for stealth HTTP sessions.
    Features:
    - Cookie persistence across requests
    - Warm-up requests to appear legitimate
    - Configurable delays
    - Automatic header rotation
    - Payload evasion integration
    """

    def __init__(
        self,
        target_url: str = "",
        min_delay: float = 0.5,
        max_delay: float = 2.0,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.target_url = target_url
        self.timer = StealthTimer(min_delay=min_delay, max_delay=max_delay)
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None
        self.base_domain = ""
        self._warmed_up = False

        # Parse base domain
        if target_url:
            try:
                parsed = urlparse(target_url)
                self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                pass

    async def __aenter__(self) -> "StealthSession":
        """Create and warm up the async HTTP client."""
        self.client = httpx.AsyncClient(
            verify=True,
            timeout=httpx.Timeout(20.0),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Close the async HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def warm_up(self) -> bool:
        """
        Send a legitimate-looking request to warm up the session.
        This helps avoid WAF detection by establishing normal traffic patterns.
        """
        if self._warmed_up or not self.base_domain:
            return True

        try:
            if not self.client:
                logger.warning(
                    f"Cannot warm up {self.base_domain}: client not initialized"
                )
                self._warmed_up = True
                return True

            headers = get_realistic_headers()
            logger.debug(f"Warming up session for {self.base_domain}")

            response = await self.client.get(self.base_domain, headers=headers)
            self._warmed_up = response.status_code < 500
            await self.timer.human_delay()

            return self._warmed_up

        except Exception as e:
            logger.warning(
                f"Warm-up failed for {self.base_domain}: {type(e).__name__}: {e}"
            )
            self._warmed_up = True  # Continue anyway
            return True

    async def request(
        self,
        method: str = "GET",
        url: str = "",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        evade: bool = False,
        **kwargs,
    ) -> httpx.Response:
        """
        Make a stealth HTTP request with evasion capabilities.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL or path (relative to base domain)
            params: Query parameters
            data: POST data
            headers: Custom headers (merged with realistic headers)
            evade: Whether to apply payload evasion
            **kwargs: Additional httpx request arguments

        Returns:
            httpx.Response object
        """
        if not self.client:
            raise RuntimeError("StealthSession not initialized. Use 'async with'.")

        # Construct full URL if needed
        if url and not url.startswith("http"):
            full_url = self.base_domain.rstrip("/") + "/" + url.lstrip("/")
        else:
            full_url = url or self.base_domain

        # Merge headers with realistic defaults
        request_headers = get_realistic_headers()
        if headers:
            request_headers.update(headers)

        # Apply evasion if requested
        if evade and params:
            evaded_params = {}
            for key, value in params.items():
                evaded_params[key] = PayloadEncoder.apply_evasion(str(value))
            params = evaded_params

        # Warm up if not done yet
        if not self._warmed_up:
            await self.warm_up()

        # Attempt request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=full_url,
                    params=params,
                    data=data,
                    headers=request_headers,
                    **kwargs,
                )
                return response

            except httpx.TimeoutException as e:
                last_error = e
                logger.debug(
                    f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {full_url}"
                )
                await asyncio.sleep(1 * (attempt + 1))

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                await asyncio.sleep(1)

        raise last_error  # type: ignore

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for GET requests."""
        return await self.request(method="GET", url=url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Convenience method for POST requests."""
        return await self.request(method="POST", url=url, **kwargs)
