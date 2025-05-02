from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import INTEGER, SMALLINT

from .base import Base
from ..static import Ranks


class PatchPlayers(Base):
    __tablename__ = "patch_players"

    patch: Mapped[int] = mapped_column(SMALLINT, primary_key=True)
    player_id: Mapped[int] = mapped_column(INTEGER, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['registry.players.id']),
    )