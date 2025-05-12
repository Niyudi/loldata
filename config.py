from db_models.static import Ranks


GET_PLAYERS: bool = True  # If True, the program fetches all players before fetching matches.
MINIMUM_RANK: Ranks = Ranks.MASTER  # Restricts fetching to players at this rank or above.
TARGET_PATCH: int | None = 1508  # Patch within which search matches. If None, searches current patch.
