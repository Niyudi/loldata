CREATE SCHEMA match_data;

CREATE TABLE match_data.timelines (
    id             integer GENERATED ALWAYS AS IDENTITY,
	match_id       integer,
	role           static.roles,
	is_blue_team   boolean NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (match_id) REFERENCES registry.matches (id),
    UNIQUE (match_id, role, is_blue_team)
);

CREATE TABLE match_data.timeline_snapshots(
    id                          integer GENERATED ALWAYS AS IDENTITY,
    timeline_id                 integer,
    timestamp                   integer NOT NULL,
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
    experience                  integer NOT NULL,
    minions_killed              smallint NOT NULL,
    minions_killed_jungle       smallint NOT NULL,
    position_x                  smallint NOT NULL,
    position_y                  smallint NOT NULL,
    total_gold                  integer NOT NULL,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id),
    UNIQUE (timeline_id, timestamp)
);

CREATE TABLE match_data.timeline_items (
    id            integer GENERATED ALWAYS AS IDENTITY,
    timeline_id   integer,
    timestamp     integer NOT NULL,
    item_id       smallint NOT NULL,
    is_purchase   boolean NOT NULL,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);

CREATE TABLE match_data.timeline_kills (
    id            integer GENERATED ALWAYS AS IDENTITY,
    timeline_id   integer,
    timestamp     integer NOT NULL,
    target_role   static.roles NOT NULL,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id),
    UNIQUE (timeline_id, timestamp, target_role)
);

CREATE TABLE match_data.timeline_kills_assists (
    id            integer GENERATED ALWAYS AS IDENTITY,
    timeline_id   integer,
    kill_id       integer,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id),
	FOREIGN KEY (kill_id) REFERENCES match_data.timeline_kills (id),
    UNIQUE (timeline_id, kill_id)
);

CREATE TYPE static.objective_types AS ENUM (
    'ATAKHAN',
    'BARON',
    'DRAKE_CHEMTECH',
    'DRAKE_CLOUD',
    'DRAKE_HEXTECH',
    'DRAKE_INFERNAL',
    'DRAKE_MOUNTAIN',
    'DRAKE_OCEAN',
    'ELDER_DRAKE',
    'GRUBS',
    'HERALD'
);

CREATE TABLE match_data.timeline_objectives (
    id                   integer GENERATED ALWAYS AS IDENTITY,
    timeline_id          integer,
    timestamp            integer NOT NULL,
    type                 static.objective_types NOT NULL,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);

CREATE TABLE match_data.timeline_objectives_assists (
    id             integer   GENERATED ALWAYS AS IDENTITY,
    timeline_id    integer,
    objective_id   integer,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id),
	FOREIGN KEY (objective_id) REFERENCES match_data.timeline_objectives (id),
    UNIQUE (timeline_id, objective_id)
);

CREATE TYPE static.structure_types AS ENUM (
    'TURRET_NEXUS',
    'TURRET_T1_TOP',
    'TURRET_T1_MID',
    'TURRET_T1_BOT',
    'TURRET_T2_TOP',
    'TURRET_T2_MID',
    'TURRET_T2_BOT',
    'TURRET_T3_TOP',
    'TURRET_T3_MID',
    'TURRET_T3_BOT',
    'INHIBITOR_TOP',
    'INHIBITOR_MID',
    'INHIBITOR_BOT'
);

CREATE TABLE match_data.timeline_structures (
    id             integer GENERATED ALWAYS AS IDENTITY,
    timeline_id    integer,
    timestamp      integer,
    type           static.structure_types NOT NULL,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);

CREATE TABLE match_data.timeline_structures_assists (
    id             integer GENERATED ALWAYS AS IDENTITY,
    timeline_id    integer,
    structure_id   integer,
    PRIMARY KEY (id),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id),
	FOREIGN KEY (structure_id) REFERENCES match_data.timeline_structures (id),
    UNIQUE (timeline_id, structure_id)
);
