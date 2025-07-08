
import platform
import psutil
import json
import datetime

info = {
    "timestamp": datetime.datetime.now().isoformat(),
    "system": {
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version()
    },
    "resources": {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
            "percent": psutil.disk_usage('/').percent
        }
    }
}

print("=== System Information ===")
print(json.dumps(info, indent=2))
print("
Analysis Summary:")
print(f"- CPU Usage: {'High' if info['resources']['cpu_percent'] > 80 else 'Normal'}")
print(f"- Memory Usage: {'Critical' if info['resources']['memory']['percent'] > 90 else 'OK'}")
print(f"- Disk Usage: {'Warning' if info['resources']['disk']['percent'] > 85 else 'Good'}")
