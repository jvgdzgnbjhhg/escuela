from starlette.datastructures import Headers
from starlette.responses import JSONResponse


class RequestBoundary:
    """Límite de cuerpo antes de parsear JSON; no confía en Content-Length."""

    def __init__(self, app, allowed_origins):
        self.app = app
        self.allowed_origins = allowed_origins

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS"}:
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        if headers.get("origin") not in self.allowed_origins:
            await JSONResponse({"detail": "Origen de solicitud no permitido"}, 403)(
                scope, receive, send
            )
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 65536:
                await JSONResponse({"detail": "Solicitud demasiado grande"}, 413)(
                    scope, receive, send
                )
                return
            if not message.get("more_body", False):
                break
        if body and headers.get("content-type", "").split(";")[0] != "application/json":
            await JSONResponse({"detail": "Utiliza JSON para enviar datos"}, 415)(
                scope, receive, send
            )
            return
        consumed = False

        async def replay():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
