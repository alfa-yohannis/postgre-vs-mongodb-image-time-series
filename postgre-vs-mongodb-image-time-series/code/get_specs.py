import os
import platform
import subprocess

def get_sys_info():
    print("--- SYSTEM INFO ---")
    print(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Machine: {platform.machine()}")
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    print(line.strip())
                    break
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if "MemTotal" in line:
                    mem_kb = int(line.split()[1])
                    print(f"RAM: {mem_kb / (1024**2):.2f} GB")
                    break
    except:
        pass
    print("-------------------")

get_sys_info()
