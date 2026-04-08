# PostgreSQL vs MongoDB Carbon Footprint

This experiment measures both performance and phase-level carbon footprint for PostgreSQL/TimescaleDB versus MongoDB on image-based time-series workloads. The benchmark code is in `code/`, and the paper files are in `paper/`.

## Directory Layout

- `code/`: benchmark runners, CodeCarbon tracking wrapper, Docker Compose file, and generated outputs
- `code/assets/`: source image used to synthesize payloads
- `code/results/`: emissions data and benchmark CSVs
- `paper/figures/`: generated figures for the paper

## Requirements

- Linux, macOS, or WSL with Docker Engine and Docker Compose v2 available as `docker compose`
- Python 3.10 or newer
- A virtual environment at `~/venv`
- Enough free disk space for repeated high-resolution runs
- Enough RAM for MongoDB; `code/docker-compose.yml` sets `--wiredTigerCacheSizeGB 30`
- `ffmpeg` only if you want to use the optional video workload

## Python Packages

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pillow psycopg2-binary pymongo matplotlib codecarbon
```

## Environment Setup

1. Enter the benchmark directory:

```bash
cd /home/alfa/projects/image-based-time-series-data/postgre-vs-mongodb-carbon-footprint/code
```

2. Activate the environment:

```bash
source ~/venv/bin/activate
```

3. Optional checks:

```bash
docker --version
docker compose version
```

## Default Profiles

The tracked phase scripts currently use:

- `1080p_fhd_image`
- `1440p_qhd_image`
- `4k_uhd_image`
- `5k_image`

If you want a different set, edit the `PROFILES=(...)` arrays in:

- `code/run_mongo_phase.sh`
- `code/run_postgres_phase.sh`

## How To Run

### Full Carbon-Tracked Experiment

```bash
bash ./run_all.sh
```

This does the following:

1. Clears the previous `results/` directory
2. Tracks the MongoDB phase with CodeCarbon via `tracker.py`
3. Tracks the PostgreSQL phase with CodeCarbon via `tracker.py`
4. Regenerates plots and writes the carbon summary

### MongoDB Phase Only

```bash
bash ./run_mongo_phase.sh
```

### PostgreSQL Phase Only

```bash
bash ./run_postgres_phase.sh
```

### Fast Smoke Test

```bash
bash ./run_retrieve_fast.sh
```

This uses fewer runs and is useful to confirm the environment before a full tracked pass.

## Manual Step-By-Step Run

For a single MongoDB profile:

```bash
docker compose down -v
docker compose up -d mongodb
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_mongodb.py
python insert_mongodb.py
python retrieve_mongodb.py
```

For a single PostgreSQL profile:

```bash
docker compose down -v
docker compose up -d timescaledb
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_postgre.py
python insert_postgre.py
python retrieve_postgre.py
```

To wrap a custom shell command with CodeCarbon manually:

```bash
python tracker.py custom_phase bash -lc 'python insert_postgre.py'
```

## Useful Overrides

- `MEDIA_PROFILE`
- `BENCHMARK_INSERT_RUNS`
- `BENCHMARK_DRIVER_RUNS`
- `BENCHMARK_SOURCE_IMAGE`

Example:

```bash
export MEDIA_PROFILE=5k_image
export BENCHMARK_INSERT_RUNS=3
python insert_postgre.py
```

## Outputs

Important outputs after a tracked run:

- `code/results/emissions.csv`
- `code/results/carbon_results.md`
- `paper/figures/`
- `code/results/*.csv` for raw benchmark summaries

