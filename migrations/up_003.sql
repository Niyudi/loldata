CREATE SCHEMA search;

CREATE TABLE search.patch_players (
	patch       smallint,
	player_id   integer,
	PRIMARY KEY (patch, player_id),
	FOREIGN KEY (player_id) REFERENCES registry.players (id)
);

CREATE TABLE search.taken_matches (
	id   integer,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES registry.matches (id)
);
