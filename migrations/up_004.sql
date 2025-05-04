CREATE SCHEMA timeline;

CREATE TABLE timeline.timeline_fields(
    region                      static.regions,
	match_id                    bigint,
	player_id                   integer,
    minute                      smallint,
    crowd_control_time          integer NOT NULL,
    damage_magic                integer NOT NULL,
    damage_magic_champions      integer NOT NULL,
    damage_magic_taken          integer NOT NULL,
    damage_physical             integer NOT NULL,
    damage_physical_champions   integer NOT NULL,
    damage_physical_taken       integer NOT NULL,
    damage_true                 integer NOT NULL,
    damage_true_champions       integer NOT NULL,
    damage_true_taken           integer NOT NULL,
    experience                  smallint NOT NULL,
    minions_killed              smallint NOT NULL,
    minions_killed_jungle       smallint NOT NULL,
    position_x                  smallint NOT NULL,
    position_y                  smallint NOT NULL,
    total_gold                  integer NOT NULL,
    PRIMARY KEY (region, match_id, player_id, minute),
	FOREIGN KEY (region, match_id, player_id) REFERENCES registry.match_players (region, match_id, player_id)
);
