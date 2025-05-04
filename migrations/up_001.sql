CREATE SCHEMA static;

CREATE TYPE static.ranks AS ENUM (
	'UNRANKED',
	'IRONIV',
	'IRONIII',
	'IRONII',
	'IRONI',
	'BRONZEIV',
	'BRONZEIII',
	'BRONZEII',
	'BRONZEI',
	'SILVERIV',
	'SILVERIII',
	'SILVERII',
	'SILVERI',
	'GOLDIV',
	'GOLDIII',
	'GOLDII',
	'GOLDI',
	'PLATINUMIV',
	'PLATINUMIII',
	'PLATINUMII',
	'PLATINUMI',
	'EMERALDIV',
	'EMERALDIII',
	'EMERALDII',
	'EMERALDI',
	'DIAMONDIV',
	'DIAMONDIII',
	'DIAMONDII',
	'DIAMONDI',
	'MASTER',
	'GRANDMASTER',
	'CHALLENGER'
);

CREATE TYPE static.regions AS ENUM (
	'BR1',
	'EUN1',
	'EUW1',
	'JP1',
	'KR',
	'LA1',
	'LA2',
	'ME1',
	'NA1',
	'OC1',
	'RU',
	'SG2',
	'TR1',
	'TW2',
	'VN2'
);

CREATE TYPE static.roles AS ENUM (
	'Top',
	'Jungle',
	'Mid',
	'Bot',
	'Support'
);

CREATE TABLE "static".champions (
	id     smallserial,
	name   varchar(25) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
);
