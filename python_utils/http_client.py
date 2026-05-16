"""General purpose async HTTP client with retry, connection pooling, concurrency and rate limit via TokenBucket"""

from __future__ import annotations
import asyncio, logging, random, time, httpx
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional
from .restapi_auth import TokenProvider

__all__ = ["HttpClientSettings", "TokenBucket", "AsyncApiClient"]

logger = logging.getLogger(__name__)


@dataclass
class HttpClientSettings:
    base_url: str
    bearer_token: Optional[str] = None
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    max_keepalive: int = 20
    max_connections: int = 40
    keepalive_expiry: float = 10.0
    concurrency: int = 12
    rps: Optional[float] = None
    burst: Optional[int] = None
    enable_http2: bool = True
    default_headers: Optional[Mapping[str, str]] = None


class TokenBucket:
    """Simple async token bucket used to enforce global RPS limits."""

    def __init__(self, rate_per_sec: float, capacity: int) -> None:
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = float(capacity)
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def take(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self.tokens = min(
                self.capacity, self.tokens + (now - self.updated) * self.rate
            )
            self.updated = now
            if self.tokens < 1.0:
                wait_for = (1.0 - self.tokens) / self.rate
                logger.debug("Token bucket depleted; sleeping %.2fs", wait_for)
                await asyncio.sleep(wait_for)
                self.tokens = 0.0
                self.updated = time.monotonic()
            self.tokens -= 1.0


class AsyncApiClient:
    """Wrapper around httpx.AsyncClient with retries and auth hooks."""

    def __init__(
        self,
        settings: HttpClientSettings,
        *,
        token_provider: Optional[TokenProvider] = None,
    ) -> None:
        self.settings = settings
        self._token_provider = token_provider
        self._sem = asyncio.Semaphore(settings.concurrency)
        self._bucket = (
            TokenBucket(settings.rps, settings.burst or int(max(1, settings.rps)))
            if settings.rps
            else None
        )

        limits = httpx.Limits(
            max_keepalive_connections=settings.max_keepalive,
            max_connections=settings.max_connections,
            keepalive_expiry=settings.keepalive_expiry,
        )

        timeout = httpx.Timeout(
            timeout=None, connect=settings.connect_timeout, read=settings.read_timeout
        )

        self._base_headers: Dict[str, str] = {"Accept": "application/json"}
        if settings.default_headers:
            self._base_headers.update(dict(settings.default_headers))

        self._client = httpx.AsyncClient(
            base_url=settings.base_url.rstrip("/"),
            timeout=timeout,
            limits=limits,
            http2=settings.enable_http2,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
        if self._token_provider:
            await self._token_provider.aclose()

    async def _build_headers(
        self, extra: Optional[Mapping[str, str]]
    ) -> Dict[str, str]:
        headers = dict(self._base_headers)
        if extra:
            headers.update(dict(extra))

        if self._token_provider:
            token = await self._token_provider.get_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.settings.bearer_token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.settings.bearer_token}"
        return headers

    @staticmethod
    def _retry_delay(attempt: int, base: float = 0.5, cap: float = 20.0) -> float:
        exp = min(cap, base * (2**attempt))
        return random.uniform(0, exp)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
        max_retries: int = 6,
        retry_on: Iterable[int] = (429, 502, 503, 504),
    ) -> httpx.Response:
        if self._bucket:
            await self._bucket.take()

        async with self._sem:
            for attempt in range(max_retries + 1):
                try:
                    request_headers = await self._build_headers(headers)
                    response = await self._client.request(
                        method,
                        url,
                        params=params,
                        headers=request_headers,
                        json=json,
                    )

                    if response.status_code < 400:
                        return response

                    if response.status_code in retry_on and attempt < max_retries:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            delay = float(retry_after)
                        else:
                            delay = self._retry_delay(attempt)
                        logger.warning(
                            "Retryable status %s for %s %s; sleeping %.2fs",
                            response.status_code,
                            method,
                            url,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    return response

                except (
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.RemoteProtocolError,
                ) as exc:
                    if attempt < max_retries:
                        delay = self._retry_delay(attempt)
                        logger.warning(
                            "Transient error %s; retrying in %.2fs",
                            exc.__class__.__name__,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise

    async def get_json(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        **kw: Any,
    ) -> Any:
        response = await self._request("GET", url, params=params, headers=headers, **kw)
        return response.json()

    async def http_version_probe(self, path: str = "/") -> str:
        try:
            response = await self._request("GET", path)
            return response.http_version
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP version probe for %s returned status %s",
                path,
                exc.response.status_code,
            )
            return exc.response.http_version
