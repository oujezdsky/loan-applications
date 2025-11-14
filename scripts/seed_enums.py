#!/usr/bin/env python3
"""
Enum Data Seeder for Loan Approval System.
This script seeds initial enum data.
"""

import asyncio
import sys
import os
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.database import SessionLocal
from app.models.enums import EnumType, EnumValue
from app.logging_config import setup_logging, logger


# Enum data definition
ENUM_SEED_DATA: List[Dict[str, Any]] = [
    {
        "name": "MaritalStatusEnum",
        "description": "Jste vdaná?",
        "is_multi_select": False,
        "values": [
            {"value": "married", "label": "Ano", "display_order": 1},
            {"value": "single", "label": "Ne", "display_order": 2},
            {"value": "divorced", "label": "Rozvedený/Rozvedená", "display_order": 3},
            {"value": "widowed", "label": "Vdovec/Vdova", "display_order": 4},
        ],
    },
    {
        "name": "HousingTypeEnum",
        "description": "Kde v tuto chvíli bydlíte?",
        "is_multi_select": False,
        "values": [
            {"value": "own", "label": "Ve vlastním", "display_order": 1},
            {"value": "rent", "label": "V nájmu", "display_order": 2},
            {"value": "with_parents", "label": "U rodičů", "display_order": 3},
            {
                "value": "with_partner",
                "label": "U partnera/partnerky",
                "display_order": 4,
            },
            {"value": "cooperative", "label": "V družstevním", "display_order": 5},
        ],
    },
    {
        "name": "EducationLevelEnum",
        "description": "Jaké máte nejvyšší dosažené vzdělání?",
        "is_multi_select": False,
        "values": [
            {"value": "elementary", "label": "Základní škola", "display_order": 1},
            {"value": "apprenticeship", "label": "Vyučen", "display_order": 2},
            {"value": "high_school", "label": "Maturitni zkouška", "display_order": 3},
            {"value": "bachelor", "label": "Bakalář", "display_order": 4},
            {"value": "master", "label": "Vysokoškolský titul", "display_order": 5},
            {"value": "doctorate", "label": "Doktorát", "display_order": 6},
        ],
    },
    {
        "name": "IncomeSourceEnum",
        "description": "Jaký je váš hlavní příjem?",
        "is_multi_select": True,
        "max_selections": 6,  # Limit multi-select to 3 choices
        "values": [
            {"value": "employment", "label": "Zaměstnání", "display_order": 1},
            {"value": "business", "label": "Podnikání", "display_order": 2},
            {
                "value": "parental_leave",
                "label": "Rodičovská dovolená",
                "display_order": 3,
            },
            {
                "value": "maternity_leave",
                "label": "Mateřská dovolená",
                "display_order": 4,
            },
            {"value": "pension", "label": "Starobní důchod", "display_order": 5},
            {
                "value": "disability_pension",
                "label": "Invalidní důchod",
                "display_order": 6,
            },
            {"value": "part_time_job", "label": "Brigáda", "display_order": 7},
            {
                "value": "rental_income",
                "label": "Příjem z pronájmu/kapitálového majetku",
                "display_order": 8,
            },
            {"value": "foster_care", "label": "Pěstounská péče", "display_order": 9},
            {"value": "alimony", "label": "Výživné", "display_order": 10},
            {"value": "military_service", "label": "Výsluha", "display_order": 11},
            {
                "value": "care_for_relative",
                "label": "Péče o osobu blízkou",
                "display_order": 12,
            },
            {"value": "unemployed", "label": "Bez zaměstnání", "display_order": 13},
        ],
    },
]


class EnumSeeder:
    """Enum data seeder with idempotent operations."""

    def __init__(self, db_session):
        self.db = db_session

    async def seed(self) -> None:
        """Main seeding method - idempotent and safe for multiple runs."""
        logger.info("Starting enum data seeding process...")

        for enum_data in ENUM_SEED_DATA:
            await self._seed_enum_type(enum_data)

        self.db.commit()
        logger.info(f"Enum seeding completed")

    async def _seed_enum_type(self, enum_data: Dict[str, Any]):
        """Seed or update a single enum type with its values."""
        # Check if enum type exists
        stmt = select(EnumType).where(EnumType.name == enum_data["name"])
        existing_enum = self.db.scalar(stmt)

        if existing_enum:
            # Update existing enum type
            existing_enum.description = enum_data["description"]
            existing_enum.is_multi_select = enum_data["is_multi_select"]
            existing_enum.max_selections = enum_data.get("max_selections")
            logger.debug(f"Updated enum type: {enum_data['name']}")
        else:
            # Create new enum type
            existing_enum = EnumType(
                name=enum_data["name"],
                description=enum_data["description"],
                is_multi_select=enum_data["is_multi_select"],
                max_selections=enum_data.get("max_selections"),
            )
            self.db.add(existing_enum)
            self.db.flush()  # Get the ID
            logger.debug(f"Created enum type: {enum_data['name']}")

        # Seed enum values
        await self._seed_enum_values(existing_enum, enum_data["values"])

    async def _seed_enum_values(
        self, enum_type: EnumType, values_data: List[Dict[str, Any]]
    ):
        """Seed or update enum values for a specific enum type."""
        existing_values = {value.value: value for value in enum_type.values}

        for value_data in values_data:
            if value_data["value"] in existing_values:
                # Update existing value
                existing_value = existing_values[value_data["value"]]
                existing_value.label = value_data["label"]
                existing_value.display_order = value_data["display_order"]
                existing_value.is_active = True
            else:
                # Create new value
                new_value = EnumValue(
                    enum_type_id=enum_type.id,
                    value=value_data["value"],
                    label=value_data["label"],
                    display_order=value_data["display_order"],
                    is_active=True,
                )
                self.db.add(new_value)

        # Deactivate any values not in the seed data
        for value in enum_type.values:
            if value.value not in [v["value"] for v in values_data]:
                value.is_active = False


async def main():
    """Main entry point for enum seeding."""
    setup_logging()
    logger.info("Enum Seeder starting...")

    db = SessionLocal()
    try:
        seeder = EnumSeeder(db)
        stats = await seeder.seed()

        logger.info("Enum seeding completed successfully!")

        # Verify the seeding
        enum_count = db.scalar(select(EnumType))
        logger.info(f"Verified: {enum_count} enum types in database")

    except Exception as e:
        logger.error(f"Enum seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
