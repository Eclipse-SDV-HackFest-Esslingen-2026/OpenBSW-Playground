"""Shared fixtures for SOVD demo integration tests."""

import os
import signal
import socket
import subprocess
import time

import pytest

# --- Configuration -----------------------------------------------------------

ECU_IP = "192.168.0.201"
ECU_DOIP_PORT = 13400
ECU_LOGICAL_ADDR = 0x002A
TESTER_LOGICAL_ADDR = 0x0EF1

CDA_HOST = "127.0.0.1"
CDA_PORT = 8080

# Locate ECU binary relative to repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECU_ELF_CANDIDATES = [
    os.path.join(
        REPO_ROOT,
        "OpenBSW-SOVD-Demo/build/posix-freertos-sovd/Debug/app.sovdDemo.elf",
    ),
    os.path.join(
        REPO_ROOT,
        "OpenBSW-SOVD-Demo/build/posix-freertos-sovd/Release/app.sovdDemo.elf",
    ),
]

CDA_DIR = os.path.join(REPO_ROOT, "OpenBSW-SOVD-Demo/sovd-cda")


# --- Helpers -----------------------------------------------------------------


def _wait_for_port(host, port, timeout=15):
    """Block until a TCP port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"{host}:{port} not reachable after {timeout}s")


def _wait_for_url(url, timeout=15):
    """Block until an HTTP endpoint returns 200."""
    import requests as _requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = _requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except _requests.ConnectionError:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"{url} not reachable after {timeout}s")


def _find_ecu_binary():
    for path in ECU_ELF_CANDIDATES:
        if os.path.isfile(path):
            return path
    pytest.skip(
        "ECU binary not found. Build with: "
        "cmake --preset posix-freertos-sovd && cmake --build build/posix-freertos-sovd"
    )


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture(scope="session")
def tap_interface():
    """Create tap0 with host IP 192.168.0.10, ECU will bind 192.168.0.201."""
    # Check if tap0 already exists (e.g. set up by CI workflow)
    result = subprocess.run(
        ["ip", "link", "show", "tap0"],
        capture_output=True,
    )
    if result.returncode == 0:
        yield  # TAP already exists
        return

    uid = os.getuid()
    subprocess.run(
        ["sudo", "ip", "tuntap", "add", "dev", "tap0", "mode", "tap", "user", str(uid)],
        check=True,
    )
    subprocess.run(["sudo", "ip", "link", "set", "tap0", "up"], check=True)
    subprocess.run(
        ["sudo", "ip", "address", "add", "192.168.0.10/24", "dev", "tap0"],
        check=True,
    )
    yield
    subprocess.run(["sudo", "ip", "link", "delete", "tap0"], check=False)


@pytest.fixture(scope="session")
def ecu_process(tap_interface):
    """Start app.sovdDemo.elf, wait for DoIP port 13400."""
    elf_path = _find_ecu_binary()

    proc = subprocess.Popen(
        [elf_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_port(ECU_IP, ECU_DOIP_PORT, timeout=15)
    except TimeoutError:
        proc.terminate()
        stdout = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
        pytest.fail(f"ECU did not start within 15s. Output:\n{stdout[:2000]}")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def cda_process(ecu_process):
    """Start stub CDA (uvicorn) on port 8080."""
    main_py = os.path.join(CDA_DIR, "main.py")
    if not os.path.isfile(main_py):
        pytest.skip("Stub CDA main.py not found")

    proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(CDA_PORT)],
        cwd=CDA_DIR,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_url(f"http://{CDA_HOST}:{CDA_PORT}/health", timeout=15)
    except TimeoutError:
        proc.terminate()
        stdout = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
        pytest.fail(f"Stub CDA did not start within 15s. Output:\n{stdout[:2000]}")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def doip_client(ecu_process):
    """Fresh DoIP connection per test."""
    from doipclient import DoIPClient

    client = DoIPClient(
        ECU_IP,
        ECU_LOGICAL_ADDR,
        protocol_version=2,
        client_logical_address=TESTER_LOGICAL_ADDR,
    )
    yield client
    client.close()
