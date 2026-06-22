import uuid
import httpx
from config.logger import logger


class HTTPDebugger:

    @staticmethod
    async def log_request(request: httpx.Request) -> None:
        await request.aread()
        request_id = uuid.uuid4().hex[:8]
        logger.debug("=" * 60)
        logger.debug("[%s] REQUEST %s %s", request_id, request.method, request.url)
        for k, v in request.headers.items():
            logger.debug("  %s: %s", k, v)
        body = request.content
        if body:
            try:
                decoded = body.decode("utf-8")
                logger.debug("BODY (utf-8) preview:")
                logger.debug(decoded[:1000])
            except UnicodeDecodeError:
                logger.debug("BODY (hex preview): %s", body[:200].hex())
        else:
            logger.debug("BODY: <empty>")
        logger.debug("=" * 60)

    @staticmethod
    async def log_response(response: httpx.Response) -> None:
        await response.aread()
        logger.debug("RESPONSE %s %s", response.status_code, response.url)
        logger.debug("HEADERS: %s", dict(response.headers))
        try:
            logger.debug("BODY: %s", response.text[:1000])
        except Exception:
            logger.debug("BODY: <unreadable>")