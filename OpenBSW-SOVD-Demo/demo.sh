#!/bin/bash
# ==========================================================================
# OpenBSW + SOVD Hackathon Demo  –  Bring-up script
#
# This script:
#   1. Creates a TAP network interface (for DoIP communication)
#   2. Builds the OpenBSW POSIX reference app (if needed)
#   3. Starts the OpenBSW ECU application in the background
#   4. Installs Python deps and starts the SOVD CDA server
#   5. Runs a quick smoke test against both the ECU and the SOVD API
#   6. Displays a live ASCII status dashboard with connection health
#
# Prerequisites:
#   - Linux with TAP support (works in the dev-container / Codespace)
#   - sudo access (for network setup)
#   - CMake, GCC/G++ (already in the dev-container)
#   - Python 3.10+ with pip
#
# Usage:
#   ./demo.sh                  # auto-detect environment, full bring-up
#   ./demo.sh --local          # force local Ubuntu mode
#   ./demo.sh --real-cda       # use real Eclipse OpenSOVD CDA (Rust) instead of Python stub
#   ./demo.sh --codespaces     # force GitHub Codespaces mode
#   ./demo.sh --build-only     # just build, don't start
#   ./demo.sh --stop           # tear down
#   ./demo.sh --status         # show live status dashboard only
#   ./demo.sh --live           # tmux split: status top + logs bottom
# ==========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
OPENBSW_DIR="$REPO_ROOT/../openbsw"
CDA_DIR="$REPO_ROOT/sovd-cda"
REAL_CDA_DIR="$REPO_ROOT/real-sovd-cda"
BUILD_DIR="$REPO_ROOT/build/posix-freertos-sovd"
ECU_ELF="$BUILD_DIR/Release/app.sovdDemo.elf"

# CDA mode: "stub" (Python) or "real" (Rust/OpenSOVD)
CDA_MODE="stub"

# ECU mode: "" (default OpenBSW demo) or "flxc1000" (FLXC1000 ECU)
ECU_MODE=""

# Network config (must match OpenBSW ethConfig.h)
TAP_IF="tap0"
HOST_IP="192.168.0.10"
ECU_IP="192.168.0.201"
SOVD_PORT="8080"
GRAFANA_PORT="3000"

# PID tracking
PID_FILE="/tmp/openbsw-demo.pid"
CDA_PID_FILE="/tmp/sovd-cda-demo.pid"
GRAFANA_PID_FILE="/tmp/grafana-demo.pid"

# Log file (shared between ECU + CDA, tailed in tmux bottom pane)
LOG_FILE="/tmp/openbsw-demo.log"

# ------------------------------------------------------------------
# Environment detection / mode
# ------------------------------------------------------------------
DEPLOY_MODE="${DEPLOY_MODE:-auto}"

detect_environment() {
    if [[ "$DEPLOY_MODE" == "auto" ]]; then
        if [[ "${CODESPACES:-}" == "true" ]]; then
            DEPLOY_MODE="codespaces"
        else
            DEPLOY_MODE="local"
        fi
    fi

    if [[ "$DEPLOY_MODE" == "codespaces" ]]; then
        CS_NAME="${CODESPACE_NAME:?CODESPACE_NAME not set — use --local}"
        CS_DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
        SOVD_URL="https://${CS_NAME}-${SOVD_PORT}.${CS_DOMAIN}"
        SWAGGER_URL="${SOVD_URL}/docs"
        GRAFANA_URL="https://${CS_NAME}-${GRAFANA_PORT}.${CS_DOMAIN}"
    else
        SOVD_URL="http://localhost:${SOVD_PORT}"
        SWAGGER_URL="${SOVD_URL}/docs"
        GRAFANA_URL="http://localhost:${GRAFANA_PORT}"
    fi
}

# ------------------------------------------------------------------
# Colors and drawing primitives
# ------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'
BOLD='\033[1m'

log()   { echo -e "${BLUE}[DEMO]${NC} $*"; }
ok()    { echo -e "${GREEN}[  OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ ERR]${NC} $*"; }

# Status symbols
SYM_OK="●"
SYM_FAIL="○"
SYM_WAIT="◌"
SYM_ARROW_R="──▶"
SYM_ARROW_L="◀──"

status_color() {
    # $1 = "ok" | "fail" | "wait"
    case "$1" in
        ok)   echo -en "${GREEN}" ;;
        fail) echo -en "${RED}" ;;
        wait) echo -en "${YELLOW}" ;;
    esac
}

status_sym() {
    case "$1" in
        ok)   echo -n "$SYM_OK" ;;
        fail) echo -n "$SYM_FAIL" ;;
        wait) echo -n "$SYM_WAIT" ;;
    esac
}

# ------------------------------------------------------------------
# Health probes
# ------------------------------------------------------------------
check_ecu() {
    # ECU: check process alive
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
        echo "ok"
    else
        echo "fail"
    fi
}

check_cda() {
    # CDA: HTTP health endpoint (both real and stub use /health)
    if curl -sf --max-time 2 http://localhost:${SOVD_PORT}/health >/dev/null 2>&1; then
        echo "ok"
    else
        echo "fail"
    fi
}

check_doip_link() {
    # DoIP link: check if CDA has a live DoIP connection to ECU
    local resp
    if [[ "$CDA_MODE" == "real" ]]; then
        # Real CDA: check the health endpoint's doip component status
        resp=$(curl -sf --max-time 2 "http://localhost:${SOVD_PORT}/health" 2>/dev/null || true)
        if echo "$resp" | grep -q '"doip"' && echo "$resp" | grep -q '"Up"'; then
            echo "ok"
        else
            echo "fail"
        fi
    else
        local url="http://localhost:${SOVD_PORT}/sovd/v1/components/openbsw-ecu/faults"
        resp=$(curl -sf --max-time 3 "$url" 2>/dev/null || true)
        if [[ -n "$resp" ]]; then
            echo "ok"
        else
            echo "fail"
        fi
    fi
}

check_grafana() {
    if curl -sf --max-time 2 http://localhost:${GRAFANA_PORT}/api/health >/dev/null 2>&1; then
        echo "ok"
    else
        echo "fail"
    fi
}

check_grafana_data() {
    # Grafana → CDA data link: check if Grafana can reach CDA's health
    if [[ "$CDA_MODE" == "real" ]]; then
        if curl -sf --max-time 2 "http://localhost:${SOVD_PORT}/health" >/dev/null 2>&1; then
            echo "ok"
        else
            echo "fail"
        fi
    else
        if curl -sf --max-time 2 "http://localhost:${SOVD_PORT}/api/faults/current" >/dev/null 2>&1; then
            echo "ok"
        else
            echo "fail"
        fi
    fi
}

get_dtc_count() {
    local resp
    if [[ "$CDA_MODE" == "real" ]]; then
        # Real CDA: get a token, then query faults
        local token
        token=$(curl -sf --max-time 2 -H 'Content-Type: application/json' \
            -d '{"client_id":"status","client_secret":"status"}' \
            "http://localhost:${SOVD_PORT}/vehicle/v15/authorize" 2>/dev/null \
            | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true)
        if [[ -n "$token" ]]; then
            resp=$(curl -sf --max-time 5 \
                -H "Authorization: Bearer $token" \
                "http://localhost:${SOVD_PORT}/vehicle/v15/components/openbsw/faults" 2>/dev/null || true)
            if [[ -n "$resp" ]]; then
                echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('items',[])))" 2>/dev/null || echo "?"
            else
                echo "?"
            fi
        else
            echo "?"
        fi
    else
        resp=$(curl -sf --max-time 2 "http://localhost:${SOVD_PORT}/sovd/v1/components/openbsw-ecu/faults" 2>/dev/null || true)
        if [[ -n "$resp" ]]; then
            echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count','?'))" 2>/dev/null || echo "?"
        else
            echo "?"
        fi
    fi
}

# ------------------------------------------------------------------
# ASCII Status Dashboard
# ------------------------------------------------------------------
print_dashboard() {
    local ecu_st="$1" cda_st="$2" doip_st="$3" grafana_st="$4" gdata_st="$5"
    local dtc_count="${6:-?}"
    local ts
    ts=$(date '+%H:%M:%S')

    # Connection line fills (all exactly 28 visible chars to match box spacing)
    local doip_fill gdata_fill doip_color gdata_color
    case "$doip_st" in
        ok)   doip_fill="════════════════════════════"; doip_color="${GREEN}" ;;
        wait) doip_fill="────────────────────────────"; doip_color="${YELLOW}" ;;
        *)    doip_fill="╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"; doip_color="${RED}" ;;
    esac
    case "$gdata_st" in
        ok)   gdata_fill="════════════════════════════"; gdata_color="${GREEN}" ;;
        wait) gdata_fill="────────────────────────────"; gdata_color="${YELLOW}" ;;
        *)    gdata_fill="╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"; gdata_color="${RED}" ;;
    esac

    echo -e ""
    echo -e "  ${DIM}${ts}${NC}  ${BOLD}SOVD Demo — Live Status${NC}   ${DIM}(Ctrl-C to stop monitoring)${NC}"
    echo -e ""
    echo -e "  ┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐"
    echo -e "  │$(status_color "$ecu_st") $(status_sym "$ecu_st") ${BOLD}OpenBSW ECU${NC}        │         │$(status_color "$cda_st") $(status_sym "$cda_st") ${BOLD}SOVD CDA${NC}           │         │$(status_color "$grafana_st") $(status_sym "$grafana_st") ${BOLD}Grafana${NC}            │"
    echo -e "  │                      │         │                      │         │                      │"
    echo -e "  │  ${CYAN}app.sovdDemo.elf${NC}    │         │  ${CYAN}$(if [[ "$CDA_MODE" == "real" ]]; then echo "OpenSOVD / Rust   "; else echo "FastAPI / Python   "; fi)${NC} │         │  ${CYAN}Dashboard${NC}           │"
    echo -e "  │  ${DIM}192.168.0.201${NC}       │         │  ${DIM}192.168.0.10${NC}        │         │  ${DIM}192.168.0.100${NC}       │"
    echo -e "  │  ${DIM}UDS addr: 0x002A${NC}    │         │  ${DIM}$(if [[ "$CDA_MODE" == "real" ]]; then echo "SOVD → DoIP (MDD) "; else echo "REST → DoIP bridge "; fi)${NC} │         │  ${DIM}Infinity datasource${NC} │"
    echo -e "  └──────────┬───────────┘         └──────┬───────┬───────┘         └──────────┬───────────┘"
    echo -e "             │    ${CYAN}DoIP :13400${NC}             │       │    ${CYAN}HTTP :8080${NC}              │"
    echo -e "             ${doip_color}└${doip_fill}┘${NC}       ${gdata_color}└${gdata_fill}┘${NC}"
    echo -e "                 ${DIM}192.168.0.201 ←→ .10${NC}                    ${DIM}.10 ←→ .100${NC}"
    echo -e ""

    # Status summary line
    local summary=""
    summary+="  ECU: $(status_color "$ecu_st")$(status_sym "$ecu_st")${NC}"
    if [[ "$ecu_st" == "ok" ]]; then summary+=" ${GREEN}running${NC}"; else summary+=" ${RED}down${NC}"; fi
    summary+="    CDA: $(status_color "$cda_st")$(status_sym "$cda_st")${NC}"
    if [[ "$cda_st" == "ok" ]]; then summary+=" ${GREEN}healthy${NC}"; else summary+=" ${RED}down${NC}"; fi
    summary+="    DoIP: $(status_color "$doip_st")$(status_sym "$doip_st")${NC}"
    if [[ "$doip_st" == "ok" ]]; then summary+=" ${GREEN}connected${NC} (${dtc_count} DTCs)"; else summary+=" ${RED}no link${NC}"; fi
    summary+="    Grafana: $(status_color "$grafana_st")$(status_sym "$grafana_st")${NC}"
    if [[ "$grafana_st" == "ok" ]]; then summary+=" ${GREEN}up${NC}"; else summary+=" ${DIM}not started${NC}"; fi
    echo -e "$summary"
    echo -e ""

    # URLs
    echo -e "  ${BOLD}URLs${NC}${DIM} (${DEPLOY_MODE} mode)${NC}"
    if [[ "$DEPLOY_MODE" == "codespaces" ]]; then
        echo -e "  ${DIM}Note: GitHub Codespaces forwards ports automatically.${NC}"
        echo -e "  ${DIM}If a port is private, right-click → Make Public in the Ports tab.${NC}"
    fi
    echo -e "    Swagger UI:   ${CYAN}${SWAGGER_URL}${NC}"
    echo -e "    SOVD API:     ${CYAN}${SOVD_URL}${NC}"
    if [[ "$grafana_st" == "ok" ]]; then
        echo -e "    Grafana:      ${CYAN}${GRAFANA_URL}${NC}"
    else
        echo -e "    Grafana:      ${DIM}${GRAFANA_URL}  (start with: docker compose up grafana)${NC}"
    fi
    echo -e ""
    echo -e "  ${BOLD}Quick commands${NC}"
    if [[ "$CDA_MODE" == "real" ]]; then
        echo -e "    curl ${SOVD_URL}/vehicle/v15/components"
        echo -e "    curl ${SOVD_URL}/vehicle/v15/components/{id}/faults"
        echo -e "    curl ${SOVD_URL}/vehicle/v15/components/{id}/data/{name}"
        echo -e "    curl ${SOVD_URL}/health/live"
    else
        echo -e "    curl ${SOVD_URL}/sovd/v1/components"
        echo -e "    curl ${SOVD_URL}/sovd/v1/components/openbsw-ecu/faults"
        echo -e "    curl ${SOVD_URL}/sovd/v1/components/openbsw-ecu/data/CF10"
        echo -e "    curl -X DELETE ${SOVD_URL}/sovd/v1/components/openbsw-ecu/faults"
    fi
    echo -e ""
    echo -e "  ${DIM}Stop demo: $0 --stop${NC}"
}

# Live status loop — refreshes every 3 seconds
live_status() {
    trap 'tput cnorm 2>/dev/null; echo ""; exit 0' INT TERM
    tput civis 2>/dev/null || true  # hide cursor

    while true; do
        local ecu_st cda_st doip_st grafana_st gdata_st dtc_count

        ecu_st=$(check_ecu)
        cda_st=$(check_cda)
        if [[ "$ecu_st" == "ok" && "$cda_st" == "ok" ]]; then
            doip_st=$(check_doip_link)
        elif [[ "$cda_st" != "ok" ]]; then
            doip_st="wait"
        else
            doip_st="fail"
        fi
        grafana_st=$(check_grafana)
        if [[ "$grafana_st" == "ok" && "$cda_st" == "ok" ]]; then
            gdata_st=$(check_grafana_data)
        else
            gdata_st="wait"
        fi

        if [[ "$doip_st" == "ok" ]]; then
            dtc_count=$(get_dtc_count)
        else
            dtc_count="?"
        fi

        # Clear screen and redraw
        clear
        echo -e ""
        echo -e "  ${BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "  ${BOLD}║${NC}          ${BOLD}OpenBSW + SOVD Hackathon Demo${NC}                                            ${BOLD}║${NC}"
        echo -e "  ${BOLD}╚══════════════════════════════════════════════════════════════════════════════════════╝${NC}"
        print_dashboard "$ecu_st" "$cda_st" "$doip_st" "$grafana_st" "$gdata_st" "$dtc_count"

        sleep 3
    done
}

# ------------------------------------------------------------------
# tmux split-screen: status dashboard (top) + live logs (bottom)
# ------------------------------------------------------------------
TMUX_SESSION="sovd-demo"

live_tmux() {
    if ! command -v tmux &>/dev/null; then
        err "tmux is not installed. Install with:  sudo apt-get install -y tmux"
        err "Falling back to status-only mode."
        live_status
        return
    fi

    # Kill stale session if any
    tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true

    # Ensure log file exists
    : > "$LOG_FILE"

    # Create tmux session with the status dashboard in the top pane
    tmux new-session -d -s "$TMUX_SESSION" -x 120 -y 40 \
        "$0 --status"

    # Split horizontally — bottom 33% for log tail
    tmux split-window -t "$TMUX_SESSION" -v -l 33% \
        "tail -f $LOG_FILE"

    # Select the top pane
    tmux select-pane -t "$TMUX_SESSION":0.0

    # Attach (blocks until user detaches with Ctrl-B d or closes)
    tmux attach-session -t "$TMUX_SESSION"
}

# Single-shot status (non-looping, for after startup)
show_status_once() {
    local ecu_st cda_st doip_st grafana_st gdata_st dtc_count

    ecu_st=$(check_ecu)
    cda_st=$(check_cda)
    if [[ "$ecu_st" == "ok" && "$cda_st" == "ok" ]]; then
        doip_st=$(check_doip_link)
    elif [[ "$cda_st" != "ok" ]]; then
        doip_st="wait"
    else
        doip_st="fail"
    fi
    grafana_st=$(check_grafana)
    if [[ "$grafana_st" == "ok" && "$cda_st" == "ok" ]]; then
        gdata_st=$(check_grafana_data)
    else
        gdata_st="wait"
    fi

    if [[ "$doip_st" == "ok" ]]; then
        dtc_count=$(get_dtc_count)
    else
        dtc_count="?"
    fi

    echo -e ""
    echo -e "  ${BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "  ${BOLD}║${NC}          ${BOLD}OpenBSW + SOVD Hackathon Demo${NC}                                            ${BOLD}║${NC}"
    echo -e "  ${BOLD}╚══════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    print_dashboard "$ecu_st" "$cda_st" "$doip_st" "$grafana_st" "$gdata_st" "$dtc_count"
}

# ------------------------------------------------------------------
# stop – tear everything down
# ------------------------------------------------------------------
stop_demo() {
    log "Stopping demo..."
    if [[ -f "$PID_FILE" ]]; then
        kill "$(cat "$PID_FILE")" 2>/dev/null && ok "OpenBSW stopped" || warn "OpenBSW was not running"
        rm -f "$PID_FILE"
    fi
    if [[ -f "$CDA_PID_FILE" ]]; then
        kill "$(cat "$CDA_PID_FILE")" 2>/dev/null && ok "SOVD CDA stopped" || warn "CDA was not running"
        rm -f "$CDA_PID_FILE"
    fi
    # Clean up TAP interface
    # Stop Real CDA container
    stop_real_cda 2>/dev/null || true
    # Stop Grafana container
    stop_grafana 2>/dev/null || true
    # Clean up TAP interface
    if ip link show "$TAP_IF" &>/dev/null; then
        sudo ip link delete "$TAP_IF" 2>/dev/null && ok "TAP interface removed" || true
    fi
    ok "Demo stopped"
    exit 0
}

# ------------------------------------------------------------------
# Mode selection menu (interactive)
# ------------------------------------------------------------------
select_mode() {
    if [[ "$DEPLOY_MODE" != "auto" ]]; then
        return  # already set via CLI flag
    fi

    # Auto-detect first
    if [[ "${CODESPACES:-}" == "true" ]]; then
        local detected="codespaces"
    else
        local detected="local"
    fi

    echo -e ""
    echo -e "  ${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "  ${BOLD}║${NC}         ${BOLD}OpenBSW + SOVD Hackathon Demo${NC}                           ${BOLD}║${NC}"
    echo -e "  ${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo -e ""
    echo -e "  ${BOLD}Select deployment environment:${NC}"
    echo -e ""
    if [[ "$detected" == "codespaces" ]]; then
        echo -e "    ${GREEN}▶ 1)${NC} GitHub Codespaces  ${DIM}(auto-detected — CODESPACES=true)${NC}"
        echo -e "      2) Local Ubuntu"
    else
        echo -e "      1) GitHub Codespaces"
        echo -e "    ${GREEN}▶ 2)${NC} Local Ubuntu  ${DIM}(auto-detected)${NC}"
    fi
    echo -e ""
    echo -e "  ${DIM}Differences:${NC}"
    echo -e "  ${DIM}  Codespaces: URLs use port-forwarded domains (*.app.github.dev)${NC}"
    echo -e "  ${DIM}              Ports must be set to Public in the Ports tab.${NC}"
    echo -e "  ${DIM}  Local:      URLs use localhost. Ports are directly accessible.${NC}"
    echo -e ""

    local choice
    read -t 10 -p "  Choose [1/2] (ENTER = auto-detected): " choice 2>/dev/null || choice=""

    case "$choice" in
        1) DEPLOY_MODE="codespaces" ;;
        2) DEPLOY_MODE="local" ;;
        *) DEPLOY_MODE="$detected" ;;
    esac

    echo -e ""
    ok "Using ${BOLD}${DEPLOY_MODE}${NC} mode"
    echo -e ""
}

# ------------------------------------------------------------------
# 1. Network setup
# ------------------------------------------------------------------
setup_network() {
    log "Setting up TAP network interface..."
    if ip link show "$TAP_IF" &>/dev/null; then
        warn "TAP interface $TAP_IF already exists, reusing"
    else
        sudo ip tuntap add dev "$TAP_IF" mode tap user "$(id -u)"
        sudo ip link set "$TAP_IF" up
        sudo ip address add "$HOST_IP/24" dev "$TAP_IF"
        ok "TAP interface $TAP_IF created with IP $HOST_IP"
    fi
}

ensure_ninja() {
    if command -v ninja >/dev/null 2>&1; then
        return
    fi

    warn "Ninja not found, installing ninja-build..."
    sudo apt-get update -qq
    sudo apt-get install -y ninja-build >/dev/null

    if command -v ninja >/dev/null 2>&1; then
        ok "Ninja installed: $(command -v ninja)"
    else
        err "Failed to install ninja-build"
        exit 1
    fi
}

needs_reconfigure() {
    local cache_file="$BUILD_DIR/CMakeCache.txt"

    if [[ ! -d "$BUILD_DIR" ]]; then
        return 0
    fi

    if [[ ! -f "$cache_file" ]]; then
        return 0
    fi

    if grep -q 'CMAKE_MAKE_PROGRAM:FILEPATH=CMAKE_MAKE_PROGRAM-NOTFOUND' "$cache_file"; then
        return 0
    fi

    if [[ ! -f "$BUILD_DIR/build.ninja" ]] && [[ ! -f "$BUILD_DIR/build-Release.ninja" ]]; then
        return 0
    fi

    return 1
}

# ------------------------------------------------------------------
# 2. Build OpenBSW
# ------------------------------------------------------------------
build_openbsw() {
    log "Building SOVD Demo overlay..."
    cd "$REPO_ROOT"

    ensure_ninja

    if needs_reconfigure; then
        warn "Refreshing CMake build directory..."
        rm -rf "$BUILD_DIR"
        if [[ "$ECU_MODE" == "flxc1000" ]]; then
            log "Building with FLXC1000 ECU simulation..."
            cmake --preset posix-freertos-sovd -DUSE_FLXC1000_ECU=ON 2>&1 | tail -5
        else
            cmake --preset posix-freertos-sovd 2>&1 | tail -5
        fi
    fi

    cmake --build "$BUILD_DIR" 2>&1 | tail -5

    if [[ -f "$ECU_ELF" ]]; then
        ok "Build succeeded: $ECU_ELF"
    else
        err "Build product not found!"
        exit 1
    fi
}

# ------------------------------------------------------------------
# 3. Start OpenBSW ECU
# ------------------------------------------------------------------
start_ecu() {
    log "Starting OpenBSW ECU application..."
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        warn "ECU already running (PID $(cat "$PID_FILE"))"
        return
    fi

    # SIGTTOU workaround: The POSIX FreeRTOS app calls tcsetattr() on stdout
    # in Uart::init(), which sends SIGTTOU when running as a background process.
    # Redirect stdin from /dev/null and trap SIGTTOU to prevent the process from
    # being stopped.
    (trap '' SIGTTOU; "$ECU_ELF" < /dev/null >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE")
    ok "OpenBSW ECU started (PID $(cat "$PID_FILE"))"  

    # Wait for the ECU to initialize
    sleep 2
}

# ------------------------------------------------------------------
# 4. Start SOVD CDA
# ------------------------------------------------------------------
start_cda() {
    log "Setting up SOVD CDA..."
    cd "$CDA_DIR"

    # Install dependencies
    if [[ ! -d "$CDA_DIR/.venv" ]]; then
        python3 -m venv "$CDA_DIR/.venv"
    fi
    source "$CDA_DIR/.venv/bin/activate"
    pip install -q -r requirements.txt 2>&1 | tail -2

    log "Starting SOVD CDA on port $SOVD_PORT..."
    if [[ -f "$CDA_PID_FILE" ]] && kill -0 "$(cat "$CDA_PID_FILE")" 2>/dev/null; then
        warn "CDA already running (PID $(cat "$CDA_PID_FILE"))"
        return
    fi

    uvicorn main:app --host 0.0.0.0 --port "$SOVD_PORT" --log-level warning >> "$LOG_FILE" 2>&1 &
    echo $! > "$CDA_PID_FILE"
    ok "SOVD CDA started (PID $(cat "$CDA_PID_FILE"))"  
    sleep 1
}

# ------------------------------------------------------------------
# 4b. Start Real SOVD CDA (Eclipse OpenSOVD, Rust-based, via Docker)
# ------------------------------------------------------------------
start_real_cda() {
    if ! command -v docker &>/dev/null; then
        err "Docker is required for the real SOVD CDA. Install Docker first."
        exit 1
    fi

    log "Starting Real SOVD CDA (Eclipse OpenSOVD)..."

    # Stop any existing stub CDA
    if [[ -f "$CDA_PID_FILE" ]] && kill -0 "$(cat "$CDA_PID_FILE")" 2>/dev/null; then
        warn "Stopping stub CDA first..."
        kill "$(cat "$CDA_PID_FILE")" 2>/dev/null || true
        rm -f "$CDA_PID_FILE"
    fi

    # Stop any existing real CDA container
    docker rm -f real-sovd-cda 2>/dev/null || true

    log "Building real SOVD CDA Docker image..."
    cd "$REPO_ROOT"
    if [[ -f real-sovd-cda/bin/opensovd-cda ]]; then
        log "  Using pre-built binary (real-sovd-cda/bin/opensovd-cda)"
        docker build --build-arg USE_PREBUILT=1 \
            -f real-sovd-cda/Dockerfile \
            -t opensovd-cda . 2>&1 | tail -5
    else
        log "  Building from source (first build may take several minutes)..."
        docker build -f real-sovd-cda/Dockerfile \
            --build-context cda-src=real-sovd-cda/classic-diagnostic-adapter \
            -t opensovd-cda . 2>&1 | tail -10
    fi

    log "Starting real SOVD CDA container..."
    docker run -d --rm \
        --name real-sovd-cda \
        --network host \
        -e CDA_CONFIG_FILE=/app/opensovd-cda.toml \
        -e DOIP_TESTER_IP="$HOST_IP" \
        opensovd-cda >> "$LOG_FILE" 2>&1

    # Wait for the CDA to become healthy
    local retries=0
    while ! curl -sf --max-time 2 http://localhost:${SOVD_PORT}/health >/dev/null 2>&1; do
        retries=$((retries + 1))
        if [[ $retries -ge 60 ]]; then
            warn "Real SOVD CDA did not become healthy within 60s"
            warn "Check logs: docker logs real-sovd-cda"
            return
        fi
        sleep 1
    done
    ok "Real SOVD CDA running on port $SOVD_PORT"
}

stop_real_cda() {
    if docker ps -q --filter name=real-sovd-cda 2>/dev/null | grep -q .; then
        docker stop real-sovd-cda >/dev/null 2>&1 && ok "Real SOVD CDA stopped" || true
    fi
}

# ------------------------------------------------------------------
# 5. Start Grafana (via docker)
# ------------------------------------------------------------------
start_grafana() {
    if ! command -v docker &>/dev/null; then
        warn "Docker not found — skipping Grafana. Install Docker to enable the dashboard."
        return
    fi

    log "Starting Grafana dashboard..."
    if curl -sf --max-time 2 http://localhost:${GRAFANA_PORT}/api/health >/dev/null 2>&1; then
        warn "Grafana already running on port $GRAFANA_PORT"
        return
    fi

    # Remove stale containers that might block the port or name
    docker rm -f grafana-demo 2>/dev/null || true
    docker rm -f grafana 2>/dev/null || true

    cd "$REPO_ROOT"
    # Start only the grafana service from docker-compose
    # Override the network so Grafana talks to the host CDA (not the doip-net bridge)
    docker run -d --rm \
        --name grafana-demo \
        -p "${GRAFANA_PORT}:3000" \
        -e GF_SECURITY_ADMIN_PASSWORD=admin \
        -e GF_AUTH_ANONYMOUS_ENABLED=true \
        -e GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer \
        -e GF_INSTALL_PLUGINS=yesoreyeram-infinity-datasource \
        -v "$REPO_ROOT/grafana/provisioning:/etc/grafana/provisioning:ro" \
        -v "$REPO_ROOT/grafana/dashboards:/var/lib/grafana/dashboards:ro" \
        --add-host=host.docker.internal:host-gateway \
        grafana/grafana-oss:latest >> "$LOG_FILE" 2>&1

    # Wait for Grafana to become healthy (plugin install can take ~45s on first run)
    local retries=0
    while ! curl -sf --max-time 2 http://localhost:${GRAFANA_PORT}/api/health >/dev/null 2>&1; do
        retries=$((retries + 1))
        if [[ $retries -ge 60 ]]; then
            warn "Grafana did not become healthy within 60s"
            return
        fi
        sleep 1
    done
    ok "Grafana running at ${GRAFANA_URL:-http://localhost:$GRAFANA_PORT}"
}

stop_grafana() {
    if docker ps -q --filter name=grafana-demo >/dev/null 2>&1; then
        docker stop grafana-demo >/dev/null 2>&1 && ok "Grafana stopped" || true
    fi
}

# ------------------------------------------------------------------
# 6. Smoke test
# ------------------------------------------------------------------
smoke_test() {
    log "Running smoke test..."

    # Test SOVD health
    local health_url
    if [[ "$CDA_MODE" == "real" ]]; then
        health_url="http://localhost:$SOVD_PORT/health"
    else
        health_url="http://localhost:$SOVD_PORT/health"
    fi
    if curl -sf --max-time 3 "$health_url" > /dev/null; then
        ok "SOVD CDA health check passed"
    else
        err "SOVD CDA not responding"
        return 1
    fi

    # Test component listing
    local comps comp_url
    if [[ "$CDA_MODE" == "real" ]]; then
        comp_url="http://localhost:$SOVD_PORT/vehicle/v15/components"
    else
        comp_url="http://localhost:$SOVD_PORT/sovd/v1/components"
    fi
    comps=$(curl -sf --max-time 3 "$comp_url" || true)
    if [[ -n "$comps" ]]; then
        ok "Component listing works"
    else
        warn "Component listing returned unexpected result"
    fi

    # Test fault reading (will fail gracefully if ECU not yet reachable)
    if [[ "$CDA_MODE" != "real" ]]; then
        local faults
        faults=$(curl -sf --max-time 5 "http://localhost:$SOVD_PORT/sovd/v1/components/openbsw-ecu/faults" 2>/dev/null || true)
        if [[ -n "$faults" ]]; then
            local count
            count=$(echo "$faults" | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])" 2>/dev/null || echo "?")
            ok "Fault reading works – $count DTCs reported"
        else
            warn "Could not read faults (ECU may not be reachable yet)"
        fi
    fi
}

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
case "${1:-}" in
    --stop)
        stop_demo
        ;;
    --build-only)
        build_openbsw
        ok "Build complete. Run without --build-only to start the demo."
        ;;
    --status)
        detect_environment
        # Auto-detect CDA mode based on what's actually running
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'real-sovd-cda'; then
            CDA_MODE="real"
        elif [[ -f "$CDA_PID_FILE" ]] && kill -0 "$(cat "$CDA_PID_FILE")" 2>/dev/null; then
            CDA_MODE="stub"
        fi
        live_status
        ;;
    --live)
        detect_environment
        live_tmux
        ;;
    --local)
        DEPLOY_MODE="local"
        detect_environment
        setup_network
        build_openbsw
        start_ecu
        start_cda
        start_grafana
        smoke_test
        show_status_once
        log "For live monitoring: $0 --live  (tmux split) or  $0 --status"
        ;;
    --real-cda)
        CDA_MODE="real"
        DEPLOY_MODE="local"
        detect_environment
        setup_network
        build_openbsw
        start_ecu
        start_real_cda
        start_grafana
        smoke_test
        show_status_once
        log "Real SOVD CDA (Eclipse OpenSOVD) is running."
        log "API base URL: http://localhost:$SOVD_PORT/vehicle/v15/"
        log "For live monitoring: $0 --live  (tmux split) or  $0 --status"
        ;;
    --flxc1000)
        ECU_MODE="flxc1000"
        CDA_MODE="real"
        DEPLOY_MODE="local"
        detect_environment
        setup_network
        build_openbsw
        start_ecu
        start_real_cda
        start_grafana
        show_status_once
        log "FLXC1000 ECU simulation with real SOVD CDA is running."
        log "API: http://localhost:$SOVD_PORT/vehicle/v15/"
        ;;
    --codespaces)
        DEPLOY_MODE="codespaces"
        detect_environment
        setup_network
        build_openbsw
        start_ecu
        start_cda
        start_grafana
        smoke_test
        show_status_once
        log "For live monitoring: $0 --live  (tmux split) or  $0 --status"
        ;;
    *)
        select_mode
        detect_environment
        setup_network
        build_openbsw
        start_ecu
        start_cda
        start_grafana
        smoke_test
        show_status_once
        log "For live monitoring: $0 --live  (tmux split) or  $0 --status"
        ;;
esac
