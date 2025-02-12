CREATE SCHEMA "search";

CREATE TABLE "search".player_ranks (
	player_id     integer,
	"rank"        "static".ranks NOT NULL,
	lp            smallint,
	last_update   timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (player_id),
	FOREIGN KEY (player_id) REFERENCES registry.players ("id")
);