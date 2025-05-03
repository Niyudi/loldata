CREATE SCHEMA registry;

CREATE TABLE registry.players (
	id        serial,
	riot_id   char(78) NOT NULL,
	name      varchar(16) NOT NULL,
	tag       varchar(5) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (riot_id)
);

CREATE TABLE registry.matches (
	region        static.regions,
	id            bigint,
	patch         smallint,
	time          bigint,
	duration      smallint,
	is_blue_win   boolean,
	PRIMARY KEY (region, id)
);

CREATE TABLE registry.match_players (
	region         static.regions,
	match_id       bigint,
	player_id      integer,
	champion_id    smallint NOT NULL,
	role           static.roles NOT NULL,
	is_blue_team   boolean NOT NULL,
	PRIMARY KEY (region, match_id, player_id),
	FOREIGN KEY (region, match_id) REFERENCES registry.matches (region, id),
	FOREIGN KEY (player_id) REFERENCES registry.players (id),
	FOREIGN KEY (champion_id) REFERENCES static.champions (id),
	UNIQUE (region, match_id, role, is_blue_team),
	UNIQUE (region, match_id, champion_id)
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
        	FROM registry.matches
			JOIN registry.match_players
				ON matches.region = match_players.region AND
					match_id = id
        	WHERE match_players.region = NEW.region AND match_id = NEW.id;

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
