from __future__ import annotations

from benchmark_config import WORKLOAD_PROFILES, load_settings
from media_payloads import _build_image_payload
from reporting_utils import PROFILE_ORDER, profile_label


def main() -> None:
    settings = load_settings()
    print(f"Source asset: {settings.source_image_path}")
    for profile_name in PROFILE_ORDER:
        profile = WORKLOAD_PROFILES[profile_name]
        payload = _build_image_payload(settings.source_image_path, profile)
        print(
            f"{profile_label(profile_name):>5} | "
            f"{profile.width}x{profile.height} | "
            f"{payload.payload_size_mb:.3f} MB"
        )


if __name__ == "__main__":
    main()
