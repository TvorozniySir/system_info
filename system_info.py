import json, os, sys

OUTPUT_FILE = "system_info.json"
ARCH_NAMES = {"AMD64": "x86_64", "x86": "x86 (32-bit)", "ARM64": "arm64"}

def read_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""

def parse(text, sep):
    result = {}
    for line in text.splitlines():
        if sep in line:
            key, value = line.split(sep, 1)
            result[key.strip()] = value.strip().strip('"')
    return result

def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024

def human_duration(seconds):
    minutes = int(seconds // 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    parts = [f"{days} д" if days else "", f"{hours} ч" if hours else "", f"{minutes} мин"]
    return " ".join(p for p in parts if p)

def percent(part, whole):
    return round(part / whole * 100, 1) if whole else None

def collect_linux():
    release = parse(read_file("/etc/os-release"), "=")
    uname = os.uname()
    mem = parse(read_file("/proc/meminfo"), ":")

    def kb(key):  
        return int(mem.get(key, "0 kB").split()[0]) * 1024

    mem_total, mem_free = kb("MemTotal"), kb("MemAvailable")
    swap_total, swap_free = kb("SwapTotal"), kb("SwapFree")

    st = os.statvfs("/")
    disk_total = st.f_blocks * st.f_frsize
    disk_free = st.f_bavail * st.f_frsize

    uptime = read_file("/proc/uptime").split()
    load = os.getloadavg()

    return {
        "os": {
            "family": "Linux",
            "name": release.get("PRETTY_NAME", "unknown"),
            "kernel": uname.release,
            "architecture": uname.machine,
        },
        "memory": {
            "total": human_size(mem_total),
            "available": human_size(mem_free),
            "used_percent": percent(mem_total - mem_free, mem_total),
            "swap_total": human_size(swap_total),
            "swap_free": human_size(swap_free),
        },
        "disk_root": {
            "total": human_size(disk_total),
            "free": human_size(disk_free),
            "used_percent": percent(disk_total - disk_free, disk_total),
        },
        "uptime": human_duration(float(uptime[0])) if uptime else None,
        "load_average": {"1min": load[0], "5min": load[1], "15min": load[2]},
    }


def collect_windows():
    v = sys.getwindowsversion()
    if v.major == 10:
        name = "Windows 11" if v.build >= 22000 else "Windows 10"
    else:
        name = f"Windows NT {v.major}.{v.minor}"
    arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE", "unknown")

    return {
        "os": {
            "family": "Windows",
            "name": name,
            "version": f"{v.major}.{v.minor}.{v.build}",
            "service_pack": v.service_pack or "нет",
            "architecture": ARCH_NAMES.get(arch, arch),
            "system_root": os.environ.get("SystemRoot"),
        },
    }


def collect_common():
    return {
        "system": {
            "byte_order": f"{sys.byteorder}-endian",
            "path_separator": os.sep,
            "line_ending": "CRLF" if os.linesep == "\r\n" else "LF",
            "filesystem_encoding": sys.getfilesystemencoding(),
        },
        "python": {
            "version": sys.version.split()[0],
            "implementation": sys.implementation.name,
            "bits": 64 if sys.maxsize > 2**32 else 32,
        },
    }


def main():
    if sys.platform.startswith("linux"):
        data = collect_linux()
    elif sys.platform.startswith("win"):
        data = collect_windows()
    else:
        sys.exit("Поддерживаются только Linux и Windows")

    data.update(collect_common())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"ОС: {data['os']['name']}. Результат записан в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
