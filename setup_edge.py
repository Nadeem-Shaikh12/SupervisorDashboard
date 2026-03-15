#!/usr/bin/env python3
"""
setup_edge.py
=============
One-shot edge-device setup script for Raspberry Pi.

Enables the I²C and SPI interfaces, installs system-level dependencies
(i2c-tools, libatlas-base-dev, etc.), and installs the correct Python
package set for the configured camera backend.

Usage
-----
    sudo python3 setup_edge.py              # auto-detect from config
    sudo python3 setup_edge.py mlx90640     # force MLX90640
    sudo python3 setup_edge.py lepton       # force FLIR Lepton
    sudo python3 setup_edge.py esp32        # ESP32 TCP stream only
    sudo python3 setup_edge.py simulator    # simulator only
"""

import subprocess
import sys
import os


# ---------------------------------------------------------------------------
# System-level packages
# ---------------------------------------------------------------------------

BASE_APT = [
    "python3-pip", "python3-dev",
    "i2c-tools", "libatlas-base-dev",
    "libopenjp2-7", "libtiff5",
    "python3-opencv",
]

SPI_APT   = ["raspi-config"]   # raspi-config does the actual enablement
I2C_APT   = ["i2c-tools"]

# ---------------------------------------------------------------------------
# Python packages per backend
# ---------------------------------------------------------------------------

BACKEND_PACKAGES = {
    "mlx90640":  ["adafruit-circuitpython-mlx90640"],
    "lepton":    ["pylepton"],
    "esp32":     [],
    "simulator": [],
}

BASE_PYTHON = [
    "fastapi", "uvicorn[standard]", "opencv-python-headless",
    "numpy", "requests",
]


def run(cmd: list, check=True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode == 0


def apt_install(pkgs: list):
    if pkgs:
        run(["apt-get", "install", "-y"] + pkgs)


def pip_install(pkgs: list):
    if pkgs:
        run([sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs)


def enable_i2c():
    """Enable I²C via raspi-config non-interactive mode."""
    print("\n[*] Enabling I²C …")
    run(["raspi-config", "nonint", "do_i2c", "0"], check=False)


def enable_spi():
    """Enable SPI via raspi-config non-interactive mode."""
    print("\n[*] Enabling SPI …")
    run(["raspi-config", "nonint", "do_spi", "0"], check=False)


def main():
    if os.geteuid() != 0:
        print("ERROR: Please run with sudo.")
        sys.exit(1)

    backend = (sys.argv[1] if len(sys.argv) > 1 else "simulator").lower()
    if backend not in BACKEND_PACKAGES:
        print(f"Unknown backend '{backend}'. Choose from: {list(BACKEND_PACKAGES)}")
        sys.exit(1)

    print("=" * 60)
    print(f"  DreamVision Edge Setup — backend: {backend.upper()}")
    print("=" * 60)

    # System packages
    print("\n[1] Updating apt packages …")
    run(["apt-get", "update", "-y"])
    apt_install(BASE_APT)

    # Hardware interface enablement
    if backend == "mlx90640":
        enable_i2c()
    elif backend == "lepton":
        enable_spi()
        enable_i2c()

    # Python packages
    print(f"\n[2] Installing Python packages for {backend} …")
    pip_install(BASE_PYTHON + BACKEND_PACKAGES[backend])

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print(f"  Set DREAMVISION_CAMERA_BACKEND={backend.upper()} before running.")
    print("=" * 60)


if __name__ == "__main__":
    main()
