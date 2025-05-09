CREATE SCHEMA match_data;

CREATE TABLE match_data.timelines (
    id             bigserial,
    region         static.regions,
	match_id       bigint,
	role           static.roles,
	is_blue_team   boolean NOT NULL,
    PRIMARY KEY ("id"),
    FOREIGN KEY (region, match_id) REFERENCES registry.matches (region, id),
    UNIQUE (region, match_id, role, is_blue_team)
);

CREATE TABLE match_data.timeline_snapshots(
    timeline_id                 bigint,
    timestamp                   integer,
    crowd_control_time          integer NOT NULL,
    damage_physical             integer NOT NULL,
    damage_physical_champions   integer NOT NULL,
    damage_physical_taken       integer NOT NULL,
    damage_magic                integer NOT NULL,
    damage_magic_champions      integer NOT NULL,
    damage_magic_taken          integer NOT NULL,
    damage_true                 integer NOT NULL,
    damage_true_champions       integer NOT NULL,
    damage_true_taken           integer NOT NULL,
    experience                  smallint NOT NULL,
    minions_killed              smallint NOT NULL,
    minions_killed_jungle       smallint NOT NULL,
    position_x                  smallint NOT NULL,
    position_y                  smallint NOT NULL,
    total_gold                  integer NOT NULL,
    PRIMARY KEY (timeline_id, timestamp),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);

CREATE TABLE match_data.timeline_items (
    timeline_id   bigint,
    timestamp     integer,
    item_id       smallint NOT NULL,
    is_purchase   boolean NOT NULL,
    PRIMARY KEY (timeline_id, timestamp),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);


CREATE TABLE match_data.timeline_kills (
    timeline_id    bigint,
    timestamp      integer,
    target_role    static.roles NOT NULL,
    assist_roles   static.roles[] NOT NULL,
    PRIMARY KEY (timeline_id, timestamp),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
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
    timeline_id    bigint,
    timestamp      integer,
    type           static.objective_types NOT NULL,
    assist_roles   static.roles[] NOT NULL,
    PRIMARY KEY (timeline_id, timestamp),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);

CREATE TYPE static.structure_types AS ENUM (
    'TURRET_NEXUS'
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
    timeline_id    bigint,
    timestamp      integer,
    type           static.structure_types NOT NULL,
    assist_roles   static.roles[] NOT NULL,
    PRIMARY KEY (timeline_id, timestamp),
	FOREIGN KEY (timeline_id) REFERENCES match_data.timelines (id)
);
