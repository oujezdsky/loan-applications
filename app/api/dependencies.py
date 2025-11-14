from fastapi import Header, HTTPException, status
from typing import Optional


def get_user_agent(user_agent: Optional[str] = Header(None)) -> str:
    return user_agent or "Unknown"


def get_client_ip(
    x_forwarded_for: Optional[str] = Header(None),
    x_real_ip: Optional[str] = Header(None),
) -> str:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    elif x_real_ip:
        return x_real_ip
    else:
        return "127.0.0.1"
