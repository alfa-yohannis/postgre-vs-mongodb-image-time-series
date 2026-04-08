# PostgreSQL vs PostgreSQL + MinIO Image Time-Series

This experiment compares two storage layouts for image-based time-series data:

- PostgreSQL/TimescaleDB with inline `BYTEA`
- PostgreSQL/TimescaleDB with binary payloads externalized to MinIO

The benchmark code lives in `code/`, and paper assets live in `paper/`.

## Directory Layout

- `code/`: benchmark scripts, Docker Compose file, summaries, and plotting utilities
- `code/assets/`: source image used to synthesize payloads
- `code/results/`: raw CSV outputs
- `paper/figures/`: generated PDF figures

## Requirements

- Linux, macOS, or WSL with Docker Engine and Docker Compose v2 available as `docker compose`
- Python 3.10 or newer
- A virtual environment at `~/venv`
- Enough free disk space for repeated high-resolution runs
- `ffmpeg` only if you plan to run the optional video profile

## Python Packages

Some shared helper modules import MongoDB classes even though the main benchmark is PostgreSQL vs MinIO, so keep `pymongo` installed as well.

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pillow psycopg2-binary pymongo minio matplotlib
```

## Environment Setup

1. Move into the benchmark code directory:

```bash
cd /home/alfa/projects/image-based-time-series-data/postgre-vs-postgre-minio-image-time-series/code
```

2. Activate the environment:

```bash
source ~/venv/bin/activate
```

3. Optional checks:

```bash
python get_specs.py
python estimate_sizes.py
docker --version
docker compose version
```

## Default Profiles

- `run_all.sh` uses `360p_sd_image` through `5k_uhd_image`
- `run_postgre_only.sh` defaults to `1080p_fhd_image`, `1440p_qhd_image`, `4k_uhd_image`, and `5k_uhd_image`
- `run_postgre_minio_only.sh` defaults to the same high-resolution subset

Both single-engine runners also accept aliases such as `360_sd_image`.

## How To Run

### Full Experiment

```bash
bash ./run_all.sh
```

This runs:

1. PostgreSQL driver overhead, insert, and point-read benchmarks
2. PostgreSQL + MinIO driver overhead, insert, and point-read benchmarks
3. Plot generation and summary aggregation

### PostgreSQL Only

```bash
bash ./run_postgre_only.sh
```

Run selected profiles only:

```bash
bash ./run_postgre_only.sh 360_sd_image 5k_uhd_image
```

### PostgreSQL + MinIO Only

```bash
bash ./run_postgre_minio_only.sh
```

Run selected profiles only:

```bash
bash ./run_postgre_minio_only.sh 360_sd_image 5k_uhd_image
```

### Fast Smoke Test

```bash
bash ./run_retrieve_fast.sh
```

This performs a short insert + point-read pass on the high-resolution profiles.

## Manual Step-By-Step Run

For inline PostgreSQL:

```bash
docker compose down -v
docker compose up -d timescaledb
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_postgre.py
python insert_postgre.py
python point_read_postgre.py
```

For PostgreSQL + MinIO:

```bash
docker compose down -v
docker compose up -d timescaledb minio
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_minio.py
python insert_postgre_minio.py
python point_read_postgre_minio.py
```

## Useful Overrides

- `MEDIA_PROFILE`
- `BENCHMARK_INSERT_RUNS`
- `BENCHMARK_POINT_READ_RUNS`
- `BENCHMARK_DRIVER_WARMUP_RUNS`
- `BENCHMARK_DRIVER_RUNS`
- `BENCHMARK_SOURCE_IMAGE`

Example:

```bash
export MEDIA_PROFILE=360p_sd_image
export BENCHMARK_INSERT_RUNS=3
python insert_postgre.py
```

## Outputs

Check these after a run:

- `code/results/*.csv`
- `code/all_summaries.txt`
- `code/final_stats_summary.csv`
- `paper/figures/*.pdf`

