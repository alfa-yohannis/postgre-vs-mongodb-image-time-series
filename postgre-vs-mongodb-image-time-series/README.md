# PostgreSQL vs MongoDB Image Time-Series

This experiment compares PostgreSQL/TimescaleDB and MongoDB for image-based time-series workloads. The runnable benchmark code is in `code/`, and the paper assets are in `paper/`.

## Directory Layout

- `code/`: benchmark scripts, Docker Compose file, generated CSV results, and plotting utilities
- `code/assets/`: source image used to generate synthetic payloads
- `code/results/`: per-run and per-profile CSV outputs
- `paper/figures/`: generated PDF figures used by the paper

## Requirements

- Linux, macOS, or WSL with Docker Engine and Docker Compose v2 available as `docker compose`
- Python 3.10 or newer
- A virtual environment at `~/venv` because the shell runners activate that exact path
- Enough free disk space for high-resolution payloads
- Enough RAM for MongoDB; `code/docker-compose.yml` currently starts MongoDB with `--wiredTigerCacheSizeGB 30`, so reduce that value if your host has less memory
- `ffmpeg` only if you plan to run the optional video profile `fhd_video_clip`

## Python Packages

Create and populate the expected virtual environment:

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pillow psycopg2-binary pymongo matplotlib pandas seaborn
```

## Environment Setup

1. Move into the benchmark directory:

```bash
cd /home/alfa/projects/image-based-time-series-data/postgre-vs-mongodb-image-time-series/code
```

2. Activate the shared virtual environment:

```bash
source ~/venv/bin/activate
```

3. Optional sanity checks:

```bash
python get_specs.py
python estimate_sizes.py
docker --version
docker compose version
```

## Default Profiles

The main image benchmark scripts default to these profiles:

- `1080p_fhd_image`
- `1440p_qhd_image`
- `4k_uhd_image`
- `5k_image`
- `6k_image`

## How To Run

### Full Experiment

Run both engines end to end:

```bash
bash ./run_all.sh
```

This runs:

1. MongoDB driver overhead, insert, and retrieval for the default profiles
2. PostgreSQL driver overhead, insert, and retrieval for the same profiles
3. Figure generation with `boxplot.py`

### MongoDB Only

```bash
bash ./run_mongo_only.sh
```

To run selected profiles only:

```bash
bash ./run_mongo_only.sh 1080p_fhd_image 4k_uhd_image
```

### PostgreSQL Only

```bash
bash ./run_postgre_only.sh
```

To run selected profiles only:

```bash
bash ./run_postgre_only.sh 1080p_fhd_image 5k_image
```

### Fast Smoke Test

This is a shorter pass that uses one insert run per profile:

```bash
bash ./run_retrieve_fast.sh
```

## Manual Step-By-Step Run

If you want to drive one profile manually:

1. Start the target container:

```bash
docker compose down -v
docker compose up -d mongodb
sleep 10
```

2. Choose a profile:

```bash
export MEDIA_PROFILE=4k_uhd_image
```

3. Run the benchmark steps:

```bash
python driver_overhead_mongodb.py
python insert_mongodb.py
python retrieve_mongodb.py
```

For PostgreSQL, replace the container and scripts:

```bash
docker compose down -v
docker compose up -d timescaledb
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_postgre.py
python insert_postgre.py
python retrieve_postgre.py
```

## Useful Overrides

- `MEDIA_PROFILE`: choose a workload profile
- `BENCHMARK_SOURCE_IMAGE`: replace the default source image
- `BENCHMARK_INSERT_RUNS`: override the number of measured insert runs
- `BENCHMARK_DRIVER_RUNS`: override the number of measured driver roundtrips

Example:

```bash
export MEDIA_PROFILE=6k_image
export BENCHMARK_INSERT_RUNS=3
python insert_postgre.py
```

## Outputs

After a run, check:

- `code/results/` for raw CSV outputs
- `code/summary.txt` and `code/all_summaries.txt` if present
- `paper/figures/` for generated PDFs

