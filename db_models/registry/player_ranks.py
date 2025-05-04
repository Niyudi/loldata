from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BIGINT, ENUM, INTEGER, SMALLINT

from .base import Base
from ..static import Ranks


class PlayerRanks(Base):
    __tablename__ = "player_ranks"

    player_id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    timestamp: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    rank: Mapped[Ranks] = mapped_column(ENUM(Ranks, create_type=False), nullable=False)
    lp: Mapped[int] = mapped_column(SMALLINT)

    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['registry.players.id']),
    )
