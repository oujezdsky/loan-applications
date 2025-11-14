from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    event,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
from app.models import Base

from app.models import Base


class EnumType(Base):
    """
    Represents a type of enumerated values.

    Stores metadata about the enum and its behavior.
    """
    __tablename__ = "enum_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_multi_select = Column(Boolean, default=False)
    max_selections = Column(Integer, nullable=True)
    is_active = Column(Boolean, server_default=expression.true(), default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    values = relationship("EnumValue", back_populates="enum_type")

    def __repr__(self):
        return f"<EnumType(name='{self.name}', is_multi_select={self.is_multi_select})>"


class EnumValue(Base):
    """
    Represents a single value within an EnumType.

    Includes display label, order, and optional metadata for UI.
    """
    __tablename__ = "enum_values"

    id = Column(Integer, primary_key=True, index=True)
    enum_type_id = Column(
        Integer,
        ForeignKey("enum_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value = Column(String(200), nullable=False)
    label = Column(String(200), nullable=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, server_default=expression.true(), default=True)
    meta_info = Column(
        Text, nullable=True
    )  # JSON string, i.e. '{"icon": "wedding_ring.png", "color": "#bfff00"}'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    enum_type = relationship("EnumType", back_populates="values")

    __table_args__ = (
        UniqueConstraint('enum_type_id', 'value', name='uq_enum_type_value'),
    )

    def __repr__(self):
        return f"<EnumValue(value='{self.value}', label='{self.label}')>"


@event.listens_for(EnumType, "before_update")
@event.listens_for(EnumValue, "before_update")
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
