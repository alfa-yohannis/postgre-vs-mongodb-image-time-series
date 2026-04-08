# PostgreSQL vs PostgreSQL + MinIO Carbon Footprint

This experiment benchmarks PostgreSQL/TimescaleDB with inline `BYTEA` against PostgreSQL/TimescaleDB plus MinIO, and tracks phase-level energy and emissions with CodeCarbon.

## Directory Layout

- `code/`: benchmark runners, CodeCarbon tracking wrapper, summaries, and plotting utilities
- `code/assets/`: source image used to generate synthetic payloads
- `code/results/`: raw benchmark outputs and carbon reports
- `paper/figures/`: generated paper figures

## Requirements

- Linux, macOS, or WSL with Docker Engine and Docker Compose v2 available as `docker compose`
- Python 3.10 or newer
- A virtual environment at `~/venv`
- Enough free disk space for repeated high-resolution runs
- `ffmpeg` only if you plan to use the optional video profile

## Python Packages

The shared helper modules import `pymongo`, so keep it installed even though the main comparison is PostgreSQL vs MinIO.

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pillow psycopg2-binary pymongo minio matplotlib codecarbon
```

## Environment Setup

1. Enter the benchmark directory:

```bash
cd /home/alfa/projects/image-based-time-series-data/postgre-vs-postgre-minio-carbon-footprint/code
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

The tracked phase scripts use:

- `360p_sd_image`
- `480p_sd_image`
- `720p_hd_image`
- `1080p_fhd_image`
- `1440p_qhd_image`
- `4k_uhd_image`
- `5k_uhd_image`

## How To Run

### Full Carbon-Tracked Experiment

```bash
bash ./run_all.sh
```

This performs:

1. A CodeCarbon-tracked PostgreSQL phase via `run_postgres_phase.sh`
2. A CodeCarbon-tracked PostgreSQL + MinIO phase via `run_postgres_minio_phase.sh`
3. Plot generation, carbon summarization, aggregation, and final stats export

### PostgreSQL Phase Only

```bash
bash ./run_postgres_phase.sh
```

### PostgreSQL + MinIO Phase Only

```bash
bash ./run_postgres_minio_phase.sh
```

### Engine-Only Runners

Inline PostgreSQL:

```bash
bash ./run_postgre_only.sh
```

PostgreSQL + MinIO:

```bash
bash ./run_postgre_minio_only.sh
```

Run selected profiles only:

```bash
bash ./run_postgre_only.sh 360_sd_image 5k_uhd_image
bash ./run_postgre_minio_only.sh 360_sd_image 5k_uhd_image
```

### Fast Smoke Test

```bash
bash ./run_retrieve_fast.sh
```

## Manual Step-By-Step Run

For the PostgreSQL phase:

```bash
docker compose down -v
docker compose up -d timescaledb
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_postgre.py
python insert_postgre.py
python retrieve_postgre.py
python point_read_postgre.py
```

For the PostgreSQL + MinIO phase:

```bash
docker compose down -v
docker compose up -d timescaledb minio
sleep 10

export MEDIA_PROFILE=4k_uhd_image
python driver_overhead_minio.py
python insert_postgre_minio.py
python retrieve_postgre_minio.py
```

Note: as currently scripted, the PM carbon runner does not execute `point_read_postgre_minio.py`. If you want that metric as a separate manual step, run it explicitly after `retrieve_postgre_minio.py`.

## Useful Overrides

- `MEDIA_PROFILE`
- `BENCHMARK_INSERT_RUNS`
- `BENCHMARK_POINT_READ_RUNS`
- `BENCHMARK_AGG_RUNS`
- `BENCHMARK_DRIVER_WARMUP_RUNS`
- `BENCHMARK_DRIVER_RUNS`
- `BENCHMARK_SOURCE_IMAGE`

Example:

```bash
export MEDIA_PROFILE=5k_uhd_image
export BENCHMARK_INSERT_RUNS=3
python insert_postgre_minio.py
```

## Outputs

After a tracked run, check:

- `code/results/emissions.csv`
- `code/results/carbon_results.md`
- `code/results/carbon_profile_breakdown.csv`
- `code/all_summaries.txt`
- `code/final_stats_summary.csv`
- `paper/figures/*.pdf`

