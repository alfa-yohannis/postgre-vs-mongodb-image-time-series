from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


@dataclass(frozen=True)
class WorkloadProfile:
    name: str
    payload_kind: str
    width: int
    height: int
    mime_type: str
    codec: str
    image_quality: int | None
    video_duration_sec: float | None
    video_fps: int | None
    video_crf: int | None
    warmup_rows: int
    total_rows: int
    batch_size: int
    insert_runs: int
    description: str


WORKLOAD_PROFILES: dict[str, WorkloadProfile] = {
    "baseline_qvga_image": WorkloadProfile(
        name="baseline_qvga_image",
        payload_kind="image",
        width=320,
        height=240,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="Legacy low-resolution image workload retained for comparison.",
    ),
    "large_fhd_image": WorkloadProfile(
        name="large_fhd_image",
        payload_kind="image",
        width=1920,
        height=1080,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="Full-HD still-image workload intended for large media benchmarking.",
    ),
    "fhd_video_clip": WorkloadProfile(
        name="fhd_video_clip",
        payload_kind="video",
        width=1920,
        height=1080,
        mime_type="video/mp4",
        codec="h264",
        image_quality=None,
        video_duration_sec=3.0,
        video_fps=24,
        video_crf=23,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="Full-HD H.264 clip workload generated from the benchmark source image.",
    ),
    "6k_image": WorkloadProfile(
        name="6k_image",
        payload_kind="image",
        width=6144,
        height=3456,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="6K still-image workload.",
    ),
    "5k_image": WorkloadProfile(
        name="5k_image",
        payload_kind="image",
        width=5120,
        height=2880,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="5K still-image workload.",
    ),
    "4k_uhd_image": WorkloadProfile(
        name="4k_uhd_image",
        payload_kind="image",
        width=3840,
        height=2160,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="4K still-image workload intended to push database payload limits.",
    ),
    "1440p_qhd_image": WorkloadProfile(
        name="1440p_qhd_image",
        payload_kind="image",
        width=2560,
        height=1440,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="1440p QHD still-image workload.",
    ),
    "1080p_fhd_image": WorkloadProfile(
        name="1080p_fhd_image",
        payload_kind="image",
        width=1920,
        height=1080,
        mime_type="image/jpeg",
        codec="jpeg",
        image_quality=90,
        video_duration_sec=None,
        video_fps=None,
        video_crf=None,
        warmup_rows=100,
        total_rows=2000,
        batch_size=50,
        insert_runs=5,
        description="1080p Full-HD still-image workload.",
    ),
}


@dataclass(frozen=True)
class BenchmarkSettings:
    repo_root: Path
    code_dir: Path
    results_dir: Path
    paper_figures_dir: Path
    source_image_path: Path
    workload: WorkloadProfile
    device_id: int
    postgres_config: dict[str, object]
    mongo_uri: str
    mongo_db_name: str
    mongo_collection_name: str
    postgres_table_name: str
    warmup_rows: int
    total_rows: int
    batch_size: int
    insert_runs: int
    aggregation_warmup_runs: int
    aggregation_runs: int
    point_read_warmup_runs: int
    point_read_runs: int
    point_read_limit: int

    @property
    def profile_slug(self) -> str:
        return self.workload.name

    @property
    def workload_label(self) -> str:
        if self.workload.payload_kind == "image":
            return f"{self.workload.width}x{self.workload.height} JPEG"
        duration = self.workload.video_duration_sec or 0.0
        fps = self.workload.video_fps or 0
        return (
            f"{self.workload.width}x{self.workload.height} "
            f"{self.workload.codec.upper()} {duration:.1f}s/{fps}fps"
        )

    def result_csv(self, stem: str) -> Path:
        return self.results_dir / f"{stem}_{self.profile_slug}.csv"

    def figure_pdf(self, filename: str) -> Path:
        return self.results_dir / filename


def load_settings() -> BenchmarkSettings:
    code_dir = Path(__file__).resolve().parent
    repo_root = code_dir.parent
    paper_figures_dir = repo_root / "paper" / "figures"

    profile_name = os.getenv("MEDIA_PROFILE", "large_fhd_image")
    if profile_name not in WORKLOAD_PROFILES:
        available = ", ".join(sorted(WORKLOAD_PROFILES))
        raise ValueError(
            f"Unknown MEDIA_PROFILE '{profile_name}'. Available profiles: {available}"
        )
    workload = WORKLOAD_PROFILES[profile_name]

    source_image_path = Path(
        os.getenv("BENCHMARK_SOURCE_IMAGE", str(code_dir / "assets" / "Schwarzsee.jpg"))
    ).resolve()

    postgres_config = {
        "dbname": os.getenv("POSTGRES_DB", "iot_ts"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "port": _env_int("POSTGRES_PORT", 55432),
    }

    mongo_db_name = os.getenv("MONGO_DB", "iot_ts")
    mongo_uri = os.getenv(
        "MONGO_URI",
        "mongodb://mongo:mongo@127.0.0.1:57017/?authSource=admin",
    )

    results_dir = code_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    return BenchmarkSettings(
        repo_root=repo_root,
        code_dir=code_dir,
        results_dir=results_dir,
        paper_figures_dir=paper_figures_dir,
        source_image_path=source_image_path,
        workload=workload,
        device_id=_env_int("DEVICE_ID", 1),
        postgres_config=postgres_config,
        mongo_uri=mongo_uri,
        mongo_db_name=mongo_db_name,
        mongo_collection_name=os.getenv("MONGO_COLLECTION", "sensor_media"),
        postgres_table_name=os.getenv("POSTGRES_TABLE", "sensor_media"),
        warmup_rows=_env_int("BENCHMARK_WARMUP_ROWS", workload.warmup_rows),
        total_rows=_env_int("BENCHMARK_TOTAL_ROWS", workload.total_rows),
        batch_size=_env_int("BENCHMARK_BATCH_SIZE", workload.batch_size),
        insert_runs=_env_int("BENCHMARK_INSERT_RUNS", workload.insert_runs),
        aggregation_warmup_runs=_env_int("BENCHMARK_AGG_WARMUP_RUNS", 2),
        aggregation_runs=_env_int("BENCHMARK_AGG_RUNS", 5),
        point_read_warmup_runs=_env_int("BENCHMARK_POINT_READ_WARMUP_RUNS", 2),
        point_read_runs=_env_int("BENCHMARK_POINT_READ_RUNS", 5),
        point_read_limit=_env_int("BENCHMARK_POINT_READ_LIMIT", 1),
    )


def describe_settings(settings: BenchmarkSettings) -> str:
    return (
        f"profile={settings.profile_slug}, "
        f"payload={settings.workload_label}, "
        f"rows/run={settings.total_rows}, "
        f"batch={settings.batch_size}, "
        f"insert_runs={settings.insert_runs}"
    )
