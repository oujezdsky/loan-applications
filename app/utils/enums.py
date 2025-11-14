import asyncio
import json
from typing import Set
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from redis import Redis
# from redis.asyncio import Redis as AsyncRedis
from app.utils.caching import get_redis_client
from app.database import get_db
from app.models import EnumType, EnumValue
from app.logging_config import logger


async def get_valid_enum_values(
    enum_name: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> dict:
    """
    Fetch valid values for an enum type.

    Returns basic info like valid values, multi-select flag, and max selections. Uses Redis cache if available.
    """
    cache_key = f"enum_info:{enum_name}"
    try:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis get failed for {cache_key}: {e}. Falling back to DB.")

    try:
        stmt = select(EnumType).where(
            EnumType.name == enum_name, EnumType.is_active == True
        )
        enum_type = await db.scalar(stmt)
        if not enum_type:
            raise ValueError(f"Enum type '{enum_name}' not found or inactive")

        stmt = select(EnumValue.value).where(
            EnumValue.enum_type_id == enum_type.id, EnumValue.is_active == True
        )
        results = await db.scalars(stmt)
        valid_values = set(results.all())

        info = {
            "valid_values": list(valid_values),
            "is_multi_select": enum_type.is_multi_select,
            "max_selections": enum_type.max_selections,
        }

        try:
            await redis.set(cache_key, json.dumps(info), ex=3600 * 24)
        except Exception as e:
            logger.warning(f"Redis set failed for {cache_key}: {e}")

        return info
    except SQLAlchemyError as e:
        logger.error(f"DB query failed for enum {enum_name}: {e}")
        raise RuntimeError("Database error during enum fetch")


async def get_enum_full_info(
    enum_name: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> dict:
    """
    Fetch full details of an enum type including all active values.

    Returns a detailed structure with metadata for each value. Uses Redis cache if available.
    """
    cache_key = f"enum_full_info:{enum_name}"
    try:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis get failed for {cache_key}: {e}. Falling back to DB.")

    try:
        stmt = select(EnumType).where(
            EnumType.name == enum_name, EnumType.is_active == True
        )
        enum_type = await db.scalar(stmt)
        if not enum_type:
            raise ValueError(f"Enum type '{enum_name}' not found or inactive")

        stmt = (
            select(EnumValue)
            .where(EnumValue.enum_type_id == enum_type.id, EnumValue.is_active == True)
            .order_by(EnumValue.display_order)
        )
        values = await db.scalars(stmt)
        values_list = values.all()

        info = {
            "enum_type": {
                "id": enum_type.id,
                "name": enum_type.name,
                "description": enum_type.description,
                "is_multi_select": enum_type.is_multi_select,
                "max_selections": enum_type.max_selections,
            },
            "values": [
                {
                    "id": val.id,
                    "value": val.value,
                    "label": val.label,
                    "display_order": val.display_order,
                    "is_active": val.is_active,
                    "meta_info": val.meta_info,
                }
                for val in values_list
            ],
        }

        try:
            await redis.set(cache_key, json.dumps(info), ex=3600 * 24)
        except Exception as e:
            logger.warning(f"Redis set failed for {cache_key}: {e}")

        return info
    except SQLAlchemyError as e:
        logger.error(f"DB query failed for enum {enum_name}: {e}")
        raise RuntimeError("Database error during enum fetch")


async def invalidate_enum_cache(
    enum_name: str,
    redis: Redis = Depends(get_redis_client),
    db: AsyncSession | None = None,
    refresh: bool = False,
):
    keys = [f"enum_info:{enum_name}", f"enum_full_info:{enum_name}"]
    for key in keys:
        await redis.delete(key)
    logger.info(f"Cache invalidated for {enum_name} (both info and full_info)")

    if refresh and db:
        try:
            # Force enums regresh
            await get_valid_enum_values(enum_name, db=db, redis=redis)
            await get_enum_full_info(enum_name, db=db, redis=redis)
            logger.info(f"Cache refreshed for {enum_name}")
        except Exception as e:
            logger.error(f"Failed to refresh cache for {enum_name}: {e}")


async def enum_changes_subscriber(redis: Redis, db: AsyncSession):
    """
    Listen to enum changes via Redis PubSub.

    Automatically invalidates (and optionally refreshes) cache when enums are added, updated, or deleted.
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(
        "enum_changes"
    )  # Channel for listening to the changes from enum admin view

    while True:
        try:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    enum_name = payload.get("enum_name")
                    action = payload.get("action")  # "insert", "update", "delete"
                    if enum_name:
                        # Invalidation + optional refresh (i.e. "update" or "insert" refresh=True)
                        refresh = action in [
                            "update",
                            "insert",
                        ]
                        await invalidate_enum_cache(
                            enum_name, redis=redis, db=db, refresh=refresh
                        )
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in enum_changes message: {e}")
        except Exception as e:
            logger.error(f"PubSub error: {e}. Reconnecting...")
            await asyncio.sleep(5)  # TODO add retry mechanism...
