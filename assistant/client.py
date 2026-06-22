import json
import urllib.parse
from typing import Any
import httpx
from assistant.headers import random_headers
from assistant.utils import get_message, extract_csrf_from_html
from config.settings import BASE_URL


class AssistantClient:

    url = "/jood/chat"

    def __init__(
            self,
            base_url: str,
            verify_ssl: bool = False,
            timeout: float = 30.0,
            debug: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.debug = debug
        self._client: httpx.AsyncClient | None = None
        self._csrf_token: str | None = None

    async def __aenter__(self) -> "AssistantClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_base_headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
            follow_redirects=True,
            event_hooks={"request": [self._log_request]} if self.debug else {},
        )
        await self._init_session()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @staticmethod
    async def _log_request(request: httpx.Request) -> None:
        await request.aread()
        print("\n" + "=" * 60)
        print(f"[REQUEST] {request.method} {request.url}")
        print("[HEADERS]")
        for k, v in request.headers.items():
            print(f"  {k}: {v}")
        body = request.content
        if body:
            try:
                print("[BODY (utf-8)]")
                print(body.decode("utf-8")[:1000])
            except UnicodeDecodeError:
                print("[BODY (hex preview)]", body[:200].hex())
        else:
            print("[BODY] <empty>")
        print("=" * 60 + "\n")

    async def _init_session(self) -> None:
        client = self._get_client()

        response = await client.get("/")
        response.raise_for_status()

        if self.debug:
            print("\n[SESSION INIT]")
            print("  Status         :", response.status_code)
            print("  Cookies in jar :", dict(client.cookies))

        # Extract CSRF from <meta name="csrf-token" content="...">
        self._csrf_token = extract_csrf_from_html(response.text)

        # Fallback: decode the XSRF-TOKEN cookie (Laravel accepts this as X-XSRF-TOKEN)
        if not self._csrf_token:
            raw = client.cookies.get("XSRF-TOKEN", "")
            self._csrf_token = urllib.parse.unquote(raw) if raw else None

        if not self._csrf_token:
            raise RuntimeError("Could not obtain a CSRF token from the home page.")

        if self.debug:
            print("  CSRF token     :", (self._csrf_token or "")[:50], "…")

        client.headers.update({
            "X-CSRF-TOKEN": self._csrf_token,
            "X-XSRF-TOKEN": urllib.parse.unquote(client.cookies.get("XSRF-TOKEN", "") or ''),
        })

    async def send_message(
            self,
            message: str,
            route_name: str,
            history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        history = history or []
        strategies = [
            ("multipart", self._post_multipart),
            ("urlencoded", self._post_urlencoded),
            ("json", self._post_json),
        ]
        last_exc: Exception | None = None
        for name, fn in strategies:
            try:
                if self.debug:
                    print(f"\n>>> Trying strategy: {name}")
                result = await fn(message, route_name, history)
                if self.debug:
                    print(f">>> Strategy '{name}' succeeded.")
                return result
            except httpx.HTTPStatusError as exc:
                if self.debug:
                    print(
                        f">>> Strategy '{name}' failed "
                        f"[{exc.response.status_code}]: {exc.response.text[:300]}"
                    )
                last_exc = exc
                if exc.response.status_code not in (415, 422):
                    raise  # only retry on content/validation errors
        raise last_exc  # type: ignore[misc]

    async def _post_multipart(
            self,
            message: str,
            route_name: str,
            history: list[dict[str, str]],
    ) -> dict[str, Any]:
        client = self._get_client()
        fields = self._build_flat_fields(message, route_name, history)

        # httpx multipart text field: (field_name, (None, value))
        files: list[tuple[str, tuple[None, str]]] = [
            (name, (None, value)) for name, value in fields
        ]
        response = await client.post(
           self.url,
            files=files,
            headers={"Accept": "application/json"},
        )
        self._raise_with_body(response)
        return response.json()  # type: ignore[no-any-return]

    async def _post_urlencoded(
            self,
            message: str,
            route_name: str,
            history: list[dict[str, str]],
    ) -> dict[str, Any]:
        client = self._get_client()
        fields = self._build_flat_fields(message, route_name, history)

        response = await client.post(
            AssistantClient.url,
            data=fields,  # list of tuples keeps duplicate bracket keys
            headers={"Accept": "application/json"},
        )
        self._raise_with_body(response)
        return response.json()  # type: ignore[no-any-return]

    async def _post_json(
            self,
            message: str,
            route_name: str,
            history: list[dict[str, str]],
    ) -> dict[str, Any]:
        client = self._get_client()
        payload = {
            "message": message,
            "route_name": route_name,
            "history": history,
            "_token": self._csrf_token,  # some Laravel setups need this in body too
        }
        response = await client.post(
            AssistantClient.url,
            content=json.dumps(payload).encode(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        self._raise_with_body(response)
        return response.json()  # type: ignore[no-any-return]

    def _build_base_headers(self, rand=False) -> dict[str, str]:
        if rand:
            return random_headers(
                base_url=self.base_url,
                accept="application/json",
                accept_encoding="gzip, deflate",
                accept_language="en-US,en;q=0.9"
            )
        else:
            return {
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
                ),
            }

    @staticmethod
    def _build_flat_fields(
            message: str,
            route_name: str,
            history: list[dict[str, str]],
    ) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = [
            ("message", message),
            ("route_name", route_name),
        ]
        for idx, entry in enumerate(history):
            for key, value in entry.items():
                fields.append((f"history[{idx}][{key}]", value))
        return fields

    @staticmethod
    def _raise_with_body(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise httpx.HTTPStatusError(
                f"HTTP {exc.response.status_code} — {exc.response.text[:500]}",
                request=exc.request,
                response=exc.response,
            ) from exc

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Use `async with AssistantClient(...) as client:`")
        return self._client


async def main() -> None:
    async with AssistantClient(
            base_url=BASE_URL,
            verify_ssl=False,
            debug=False,
    ) as client:
        result = await client.send_message(
            message="عامل اية النهرضا",
            route_name="website.home",
            history=[{"role": "user", "content": "عامل اية النهرضا"}],
        )
        print(
            get_message(result)
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

