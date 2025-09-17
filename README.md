# Dashboard
<img width="872" height="415" alt="image" src="https://github.com/user-attachments/assets/5653fdff-bbc8-4b71-9798-b085760f9579" />


# Setup Instructions
## Prerequisites
 - [Docker](https://docs.docker.com/engine/install/ubuntu/) and docker-compose installed
 - Register for OpenWeathermap [API](https://openweathermap.org/api)
 
## How-to
 - Update `GF_DATABASE_USER` and `GF_DATABASE_PASSWORD` in the `docker-compose.yaml` to arbitrary values
 - Run '`docker compose up -d`' to bring up PostgreSQL and Grafana containers, make sure they are up and healthy using '`docker ps`'
 - Access Grafana instance by connecting to `http://localhost:3000` & configure same username & password above
 - Access PostgreSQL instance by running '`docker exec -it postgres psql -U grafana -d weather_db`' & create two tables mentioned in Postgres_schema
 - Set these environment variables: `OWM_API_KEY`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
 - Install Python3 venv & `pip install requirements.txt`
 - Run `python3 collectAndPush.py` to make sure weather fetching and DB pushing is working as expected

# Architecture Diagram
<img width="741" height="415" alt="image" src="https://github.com/user-attachments/assets/3925a516-379b-4338-9b9a-03fe83f6bc06" />

