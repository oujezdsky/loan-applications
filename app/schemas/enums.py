from pydantic import BaseModel, Field, List
from typing import Optional


class EnumTypeSchema(BaseModel):
    id: Optional[int] = Field(
        ..., description="ID of the enum type (for internal reference)"
    )
    name: str = Field(
        ..., description="Unique name of the enum (e.g., 'HousingTypeEnum')"
    )
    description: Optional[str] = Field(
        None, description="Description of the enum for documentation purposes"
    )
    is_multi_select: bool = Field(
        ..., description="Indicates whether multiple selections are allowed"
    )
    max_selections: Optional[int] = Field(
        None,
        description="Maximum number of selections allowed if multi-select is enabled",
    )

    class Config:
        from_attributes = True


class EnumValueSchema(BaseModel):
    id: int = Field(..., description="ID of the enum value")
    value: str = Field(..., description="Internal value (e.g., 'own_house')")
    label: str = Field(
        ..., description="Display label shown to users (e.g., 'Own House')"
    )
    display_order: int = Field(..., description="Ordering index for display purposes")
    is_active: bool = Field(..., description="Indicates whether the value is active")
    metadata: Optional[str] = Field(
        None,
        description="Optional additional metadata as a JSON string (e.g., {'icon': 'house.png'})",
    )

    class Config:
        from_attributes = True


class EnumResponseSchema(BaseModel):
    enum_type: EnumTypeSchema
    values: List[EnumValueSchema] = Field(
        ..., description="List of active values for the enum"
    )

    class Config:
        from_attributes = True
