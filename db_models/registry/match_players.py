from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import BOOLEAN, CHAR, ENUM, INTEGER, SMALLINT

from .base import Base
from ..static import Regions, Roles


class MatchPlayers(Base):
    __tablename__ = "match_players"

    match_id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    player_id: Mapped[str] = mapped_column(CHAR(78), primary_key=True)
    champion_id: Mapped[int] = mapped_column(SMALLINT)
    role: Mapped[Roles] = mapped_column(ENUM(Roles, create_type=False), nullable=False)
    is_blue_team: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(['match_id'], ['registry.matches.id']),
        ForeignKeyConstraint(['player_id'], ['registry.players.id']),
        ForeignKeyConstraint(['champion_id'], ['static.champions.id']),
        UniqueConstraint('match_id', 'role', 'is_blue_team'),
        UniqueConstraint('match_id', 'champion_id')
    )
