from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests import Response, Session

from utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class ApiResult:
    ok: bool
    status_code: int | None
    data: Any
    error: str | None = None


class ApiClient:
    """Small requests wrapper for hybrid UI/API framework use cases."""

    def __init__(self, base_url: str, timeout: int = 10, session: Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def get(self, path: str = "", **kwargs: Any) -> ApiResult:
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        try:
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            return self._parse_response(response)
        except requests.RequestException as exc:
            logger.error("GET request failed for %s: %s", url, exc)
            return ApiResult(ok=False, status_code=None, data=None, error=str(exc))

    @staticmethod
    def _parse_response(response: Response) -> ApiResult:
        try:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            data = response.json() if "application/json" in content_type else response.text
            return ApiResult(ok=True, status_code=response.status_code, data=data)
        except ValueError as exc:
            logger.error("Response JSON parsing failed: %s", exc)
            return ApiResult(
                ok=False,
                status_code=response.status_code,
                data=response.text,
                error=str(exc),
            )
        except requests.HTTPError as exc:
            logger.error("HTTP error returned: %s", exc)
            return ApiResult(
                ok=False,
                status_code=response.status_code,
                data=response.text,
                error=str(exc),
            )
