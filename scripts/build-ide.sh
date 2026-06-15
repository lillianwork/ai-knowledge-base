#!/bin/bash
set -euo pipefail

# build-ide.sh — IDE toolchain compilation with SonarQube build-wrapper capture
# Context: Captures full compilation database for C/C++ static analysis

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
BUILD_DIR="${BUILD_DIR:-$WORKSPACE/build}"
BUILD_TYPE="${BUILD_TYPE:-Debug}"
BUILD_WRAPPER_OUTPUT="${BUILD_WRAPPER_OUTPUT:-bw-output}"
SONAR_SCANNER_HOME="${SONAR_SCANNER_HOME:-/opt/sonar-scanner}"
IDE_TOOLCHAIN="${IDE_TOOLCHAIN:-gcc}"  # gcc, iar, keil, armcc

log() { echo "[BUILD] $(date '+%H:%M:%S') $*"; }

extract_version() {
    local version_file="$WORKSPACE/version.h"
    if [[ -f "$version_file" ]]; then
        grep -oP '(?<=VERSION_STRING ")[^"]*' "$version_file" 2>/dev/null || echo "0.0.0-dev"
    else
        git describe --tags --always --dirty 2>/dev/null || echo "0.0.0-dev"
    fi
}

detect_ide_toolchain() {
    case "$IDE_TOOLCHAIN" in
        iar)
            IDE_CC="${IAR_CC:-iccarm}"
            IDE_MAKE="${IAR_BUILD:-iarbuild}"
            BUILD_CMD="$IDE_MAKE ${IAR_PROJECT:-project.ewp} -build $BUILD_TYPE -log info"
            ;;
        keil)
            IDE_CC="${KEIL_CC:-armcc}"
            IDE_MAKE="${KEIL_BUILD:-UV4}"
            BUILD_CMD="$IDE_MAKE -b ${KEIL_PROJECT:-project.uvprojx} -t ${KEIL_TARGET:-Target1} -o $BUILD_DIR/build.log"
            ;;
        armcc)
            IDE_CC="${ARM_CC:-armclang}"
            IDE_MAKE="${ARM_BUILD:-make}"
            BUILD_CMD="$IDE_MAKE -j$(nproc) -f ${MAKEFILE:-Makefile} BUILD=$BUILD_TYPE"
            ;;
        gcc|*)
            IDE_CC="${CROSS_COMPILE:-arm-none-eabi-}gcc"
            IDE_MAKE="make"
            BUILD_CMD="$IDE_MAKE -j$(nproc) -f ${MAKEFILE:-Makefile} BUILD=$BUILD_TYPE"
            ;;
    esac
}

run_build_with_wrapper() {
    mkdir -p "$BUILD_DIR" "$BUILD_DIR/output" "$BUILD_DIR/logs"

    local build_wrapper="$SONAR_SCANNER_HOME/build-wrapper-linux-x86/build-wrapper-linux-x86"

    if [[ -x "$build_wrapper" ]]; then
        log "Using SonarQube build-wrapper to capture compilation database"
        "$build_wrapper" --out-dir "$BUILD_WRAPPER_OUTPUT" \
            bash -c "cd $WORKSPACE && $BUILD_CMD" \
            2>&1 | tee "$BUILD_DIR/logs/build.log"
        log "Compilation database captured in $BUILD_WRAPPER_OUTPUT/compile_commands.json"
    else
        log "Build wrapper not found at $build_wrapper, running plain build"
        (cd "$WORKSPACE" && eval "$BUILD_CMD") 2>&1 | tee "$BUILD_DIR/logs/build.log"
    fi

    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log "ERROR: Build failed with exit code $exit_code"
        return $exit_code
    fi
}

collect_firmware_artifacts() {
    local output_dir="$BUILD_DIR/output"
    log "Collecting firmware artifacts..."

    if compgen -G "$BUILD_DIR/*.bin" > /dev/null; then cp "$BUILD_DIR"/*.bin "$output_dir/" 2>/dev/null; fi
    if compgen -G "$BUILD_DIR/*.hex" > /dev/null; then cp "$BUILD_DIR"/*.hex "$output_dir/" 2>/dev/null; fi
    if compgen -G "$BUILD_DIR/*.elf" > /dev/null; then cp "$BUILD_DIR"/*.elf "$output_dir/" 2>/dev/null; fi
    if compgen -G "$BUILD_DIR/*.map" > /dev/null; then cp "$BUILD_DIR"/*.map "$output_dir/" 2>/dev/null; fi
    if compgen -G "$BUILD_DIR/*.s19" > /dev/null; then cp "$BUILD_DIR"/*.s19 "$output_dir/" 2>/dev/null; fi

    local count
    count=$(find "$output_dir" -type f | wc -l)
    log "Collected $count firmware artifact(s)"
}

generate_build_info() {
    tee "$BUILD_DIR/output/build-info.json" <<EOF
{
  "version": "$(extract_version)",
  "build_type": "$BUILD_TYPE",
  "toolchain": "$IDE_TOOLCHAIN",
  "compiler": "$IDE_CC",
  "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "build_host": "$(hostname)",
  "jenkins_build_number": "${BUILD_NUMBER:-local}"
}
EOF
}

main() {
    log "Starting IDE build (toolchain: $IDE_TOOLCHAIN, type: $BUILD_TYPE)"
    detect_ide_toolchain
    run_build_with_wrapper
    collect_firmware_artifacts
    generate_build_info
    log "Build completed successfully"
}

main "$@"
