# Preparing GitHub Codespaces for OpenBSW S32K344 Development

The default Codespace (Ubuntu 24.04) is missing several tools required to build,
test, and simulate the S32K344 port. Install them as described below.

## Required Installs

### 1. Ninja Build System

```bash
sudo apt-get update && sudo apt-get install -y ninja-build
```

*CMake presets use `Ninja Multi-Config` generator — not available without this.*

### 2. ARM GCC Cross-Compiler (for S32K344 firmware builds)

```bash
wget -qO- https://developer.arm.com/-/media/Files/downloads/gnu/14.3.rel1/binrel/arm-gnu-toolchain-14.3.rel1-x86_64-arm-none-eabi.tar.xz \
  | sudo tar -xJ -C /opt --transform='s/^[^/]*/arm-gnu-toolchain/'
export PATH="/opt/arm-gnu-toolchain/bin:$PATH"
```

### 3. Host GCC 11 (for POSIX unit tests)

```bash
sudo apt-get install -y g++-11 gcc-11
```

*The project's test presets expect `g++-11`/`gcc-11`. Codespace ships with GCC 13.*

### 4. lcov (for code coverage reports)

```bash
sudo apt-get install -y lcov
```

### 5. Renode (for virtual MCU simulation)

```bash
bash test/renode/install_renode.sh
# or manually:
#   sudo apt-get install -y mono-complete
#   wget https://github.com/renode/renode/releases/download/v1.15.3/renode_1.15.3_amd64.deb
#   sudo dpkg -i renode_1.15.3_amd64.deb
```

### 6. Python Test Dependencies

```bash
pip3 install robotframework pytest python-can can-isotp doipclient udsoncan pyserial tomli
```

## Quick Verification

```bash
ninja --version          # 1.11+
cmake --version          # 3.28+
arm-none-eabi-gcc -v     # 14.3
g++-11 --version         # 11.x
lcov --version           # 2.0+
renode --version         # 1.15+
python3 -c "import robot; print(robot.version.VERSION)"
```

## One-Liner (everything except Renode)

```bash
sudo apt-get update && sudo apt-get install -y ninja-build g++-11 gcc-11 lcov tmux \
  && pip3 install robotframework pytest python-can can-isotp doipclient udsoncan pyserial tomli
```

> **tmux** is used by `./demo.sh --live` for the split-screen status + log view.
