from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from benchmark_config import BenchmarkSettings, WorkloadProfile


@dataclass(frozen=True)
class MediaPayload:
    profile_name: str
    payload_kind: str
    mime_type: str
    codec: str
    width: int
    height: int
    duration_ms: int
    payload_bytes: bytes

    @property
    def payload_size_bytes(self) -> int:
        return len(self.payload_bytes)

    @property
    def payload_size_mb(self) -> float:
        return len(self.payload_bytes) / (1024 * 1024)


def _build_collage(source_path: Path, width: int, height: int) -> Image.Image:
    src = Image.open(source_path).convert("RGB")
    tile_w = max(width // 2, 1)
    tile_h = max(height // 2, 1)

    variants = [
        ImageOps.fit(src, (tile_w, tile_h), method=Image.Resampling.LANCZOS),
        ImageOps.mirror(ImageOps.fit(src, (tile_w, tile_h), method=Image.Resampling.LANCZOS)),
        ImageOps.flip(ImageOps.fit(src, (tile_w, tile_h), method=Image.Resampling.LANCZOS)),
        ImageOps.mirror(
            ImageOps.flip(ImageOps.fit(src, (tile_w, tile_h), method=Image.Resampling.LANCZOS))
        ),
    ]

    canvas = Image.new("RGB", (width, height))
    positions = [(0, 0), (tile_w, 0), (0, tile_h), (tile_w, tile_h)]
    for image, position in zip(variants, positions, strict=True):
        canvas.paste(image, position)

    return canvas.crop((0, 0, width, height))


def _build_image_payload(source_path: Path, profile: WorkloadProfile) -> MediaPayload:
    image = _build_collage(source_path, profile.width, profile.height)
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=profile.image_quality or 95, optimize=True)
    return MediaPayload(
        profile_name=profile.name,
        payload_kind=profile.payload_kind,
        mime_type=profile.mime_type,
        codec=profile.codec,
        width=profile.width,
        height=profile.height,
        duration_ms=0,
        payload_bytes=buf.getvalue(),
    )


def _build_video_payload(source_path: Path, profile: WorkloadProfile) -> MediaPayload:
    collage = _build_collage(source_path, profile.width, profile.height)
    duration_sec = profile.video_duration_sec or 3.0
    fps = profile.video_fps or 24
    crf = profile.video_crf or 23

    with tempfile.TemporaryDirectory(prefix="media_payload_") as tmpdir:
        tmp_path = Path(tmpdir)
        frame_path = tmp_path / "source.jpg"
        output_path = tmp_path / "payload.mp4"
        collage.save(frame_path, format="JPEG", quality=96, optimize=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(fps),
            "-t",
            f"{duration_sec:.2f}",
            "-i",
            str(frame_path),
            "-vf",
            f"scale={profile.width}:{profile.height},noise=alls=18:allf=t+u:all_seed=23",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        payload_bytes = output_path.read_bytes()

    return MediaPayload(
        profile_name=profile.name,
        payload_kind=profile.payload_kind,
        mime_type=profile.mime_type,
        codec=profile.codec,
        width=profile.width,
        height=profile.height,
        duration_ms=int(duration_sec * 1000),
        payload_bytes=payload_bytes,
    )


def load_media_payload(settings: BenchmarkSettings) -> MediaPayload:
    if not settings.source_image_path.exists():
        raise FileNotFoundError(f"Source asset not found: {settings.source_image_path}")

    if settings.workload.payload_kind == "image":
        return _build_image_payload(settings.source_image_path, settings.workload)
    return _build_video_payload(settings.source_image_path, settings.workload)
