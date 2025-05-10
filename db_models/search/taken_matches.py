from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import INTEGER

from .base import Base


class TakenMatches(Base):
    __tablename__ = "taken_matches"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(['id'], ['registry.matches.id']),
    )
