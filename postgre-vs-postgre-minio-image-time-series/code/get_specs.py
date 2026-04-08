from __future__ import annotations

import platform


def get_sys_info() -> None:
    print("--- SYSTEM INFO ---")
    print(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Machine: {platform.machine()}")
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as handle:
            for line in handle:
                if "model name" in line:
                    print(line.strip())
                    break
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                if "MemTotal" in line:
                    mem_kb = int(line.split()[1])
                    print(f"RAM: {mem_kb / (1024 ** 2):.2f} GB")
                    break
    except OSError:
        pass
    print("-------------------")


if __name__ == "__main__":
    get_sys_info()
