CREATE TABLE search.patch_players (
    patch         smallint,
    player_id     integer,
    curr_pages    smallint NOT NULL,
    total_pages   smallint NOT NULL,
    is_done       boolean NOT NULL,
    PRIMARY KEY (patch, player_id),
    CHECK (curr_pages >= 0),
    CHECK (total_pages > 0),
    CHECK (curr_pages <= total_pages)
);
