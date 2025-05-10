# LoLData

This code fetches match data from the official Riot API fro League of Legends. It is designed to be used tih a personal
key with a rate limite of 100 requests per 2 minutes, for small prototypes and experiments.

Currently, the only region supported is BR1. That can easily be changed modifying the links in the code to the
desired server.

## Instructions

To use the code, you need to create a folder called "keys" with two files, "DB_URI" and "RIOT_API_KEY":

```
keys
   |-- DB_URI
   |-- RIOT_API_KEY
```

In the "DB_URI" file, write the URI to connect to your PostgreSQL database. In the "RIOT_API_KEY", write your riot API
key.

To setup the database, run the "up" SQL scripts in the folder "migrations" in order. The file "config.py" has a few
configurable parameters for the search.
