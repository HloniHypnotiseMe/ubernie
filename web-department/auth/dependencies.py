#!/usr/bin/env python3
"""FastAPI dependencies for JWT auth."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Header
from typing import Optional

from auth.security import decode_token


async def current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract + verify the bearer token. Returns {'user_id', 'role', 'email'}."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {
        "user_id": payload["sub"],
        "role": payload["role"],
        "email": payload["email"],
    }


def require_role(*allowed_roles: str):
    """Factory: returns a dependency that asserts the current user has one of these roles."""
    async def _checker(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {'|'.join(allowed_roles)}")
        return user
    return _checker
