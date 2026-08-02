"""Route-scoped Bearer JWT authentication for the MCP HTTP transport."""

from jwt.exceptions import InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from knowledge_ai.core.config import get_settings
from knowledge_ai.core.database import get_session_factory
from knowledge_ai.core.mcp_context import reset_current_mcp_user, set_current_mcp_user
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.user import UserService


class MCPAuthMiddleware(BaseHTTPMiddleware):
    """Require a valid Bearer access JWT on ``/mcp`` routes only."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith("/mcp"):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if authorization is None or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": "Bearer token required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.removeprefix("Bearer ").strip()
        jwt_service = JWTService(get_settings())
        try:
            claims = jwt_service.verify_access_token(token)
        except InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if await jwt_service.is_access_token_revoked(claims.jti):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "detail": "Token has been revoked"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        session_factory = get_session_factory()
        async with session_factory() as session:
            user = await UserService(session).get_by_id(claims.user_id)
            if user is None or not user.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "detail": "User not found or inactive"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            context_token = set_current_mcp_user(user)
            try:
                return await call_next(request)
            finally:
                reset_current_mcp_user(context_token)
