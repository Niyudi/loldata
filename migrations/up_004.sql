CREATE SCHEMA "sync";

CREATE TABLE "sync".taken_matches (
	region   static.regions,
	"id"     bigint,
	PRIMARY KEY (region, "id"),
	FOREIGN KEY (region, "id") REFERENCES registry.matches (region, "id")
);
