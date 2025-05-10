CREATE SCHEMA registry;

CREATE TABLE registry.players (
	id        integer GENERATED ALWAYS AS IDENTITY,
	riot_id   char(78) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (riot_id)
);

CREATE TABLE registry.player_ranks (
	player_id   integer,
	timestamp   bigint,
	rank        static.ranks NOT NULL,
	lp          smallint,
	PRIMARY KEY (player_id, timestamp),
	FOREIGN KEY (player_id) REFERENCES registry.players (id)
);

CREATE FUNCTION registry.enforce_rank() RETURNS trigger AS $$
DECLARE
	row_count integer := 0;
    must_check boolean := false;
BEGIN
    IF TG_OP = 'INSERT' THEN
        must_check := true;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF (NEW.id != OLD.id OR NEW.riot_id != OLD.riot_id) THEN
            must_check := true;
        END IF;
    END IF;

    IF must_check THEN
        LOCK TABLE registry.players IN EXCLUSIVE MODE;
        LOCK TABLE registry.player_ranks IN EXCLUSIVE MODE;

        SELECT INTO row_count COUNT(timestamp) 
        	FROM registry.player_ranks
        	WHERE player_id = NEW.id;

        IF row_count = 0 THEN
            RAISE EXCEPTION 'Player with riot id % must have a registered rank.', NEW.riot_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER enforce_rank
    AFTER INSERT OR UPDATE ON registry.players
	DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION registry.enforce_rank();

CREATE TABLE registry.matches (
    id            integer GENERATED ALWAYS AS IDENTITY,
	region        static.regions NOT NULL,
	riot_id       bigint NOT NULL,
	patch         smallint,
	time          bigint,
	duration      smallint,
	is_blue_win   boolean,
	PRIMARY KEY (id),
    UNIQUE (region, riot_id)
);

CREATE TABLE registry.match_players (
	match_id       integer,
	player_id      integer,
	champion_id    smallint,
	role           static.roles NOT NULL,
	is_blue_team   boolean NOT NULL,
	PRIMARY KEY (match_id, player_id),
	FOREIGN KEY (match_id) REFERENCES registry.matches (id),
	FOREIGN KEY (player_id) REFERENCES registry.players (id),
	FOREIGN KEY (champion_id) REFERENCES static.champions (id),
	UNIQUE (match_id, role, is_blue_team),
	UNIQUE (match_id, champion_id)
);

CREATE FUNCTION registry.enforce_valid_matches() RETURNS trigger AS $$
DECLARE
    player_count smallint := 0;
    must_check boolean := false;
BEGIN
    IF TG_OP = 'INSERT' AND NEW.is_blue_win IS NOT NULL THEN
        must_check := true;
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.is_blue_win IS NOT NULL THEN
        IF (NEW.region != OLD.region OR NEW.id != OLD.id) THEN
            must_check := true;
        END IF;
    END IF;

    IF must_check THEN
        LOCK TABLE registry.matches IN EXCLUSIVE MODE;
        LOCK TABLE registry.match_players IN EXCLUSIVE MODE;

        SELECT INTO player_count COUNT(player_id) 
        	FROM registry.match_players
        	WHERE region = NEW.region AND match_id = NEW.id;

        IF player_count != 10 THEN
            RAISE EXCEPTION 'Match %_% must have 10 players.', NEW.region, NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER enforce_valid_matches 
    AFTER INSERT OR UPDATE ON registry.matches
	DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION registry.enforce_valid_matches();
