from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, ENUM

from .base import Base
from ..static import Regions


class TakenMatches(Base):
    __tablename__ = "taken_matches"

    region: Mapped[Regions] = mapped_column(ENUM(Regions, create_type=False), primary_key=True)
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(['region', 'id'], ['registry.matches.region', 'registry.matches.id']),
    )
