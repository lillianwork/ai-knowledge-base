#!/bin/bash
set -euo pipefail

# archive-artifacts.sh — Archive all project artifacts: source, docs, firmware, test cases, defects
# Context: Final stage; runs after all gates pass; uploads to Nexus or filesystem archive

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
ARCHIVE_MAPPING="${ARCHIVE_MAPPING:-$WORKSPACE/config/archive-mapping.json}"
NEXUS_HOST_URL="${NEXUS_HOST_URL:-http://nexus:8081}"
NEXUS_USER="${NEXUS_USER:-admin}"
NEXUS_PASSWORD="${NEXUS_PASSWORD:-}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-/var/archive/firmware}"
BUILD_DIR="${BUILD_DIR:-$WORKSPACE/build}"

log() { echo "[ARCHIVE] $(date '+%H:%M:%S') $*"; }

resolve_version() {
    local version
    if [[ -n "${CI_COMMIT_TAG:-}" ]]; then
        version="${CI_COMMIT_TAG#v}"
    elif git describe --tags --exact-match 2>/dev/null; then
        version="$(git describe --tags --exact-match | sed 's/^v//')"
    else
        local branch
        branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null | sed 's/[\/]/-/g' || echo "unknown")
        local sha
        sha=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        version="${branch}-${sha}"
    fi
    echo "$version"
}

is_release() {
    [[ "${CI_COMMIT_BRANCH:-}" == "main" || "${CI_COMMIT_BRANCH:-}" == release/* ]] && echo "true" || echo "false"
}

archive_file_system() {
    local source_path="$1" archive_name="$2" required="${3:-false}"

    if [[ ! -e "$source_path" ]]; then
        if [[ "$required" == "true" ]]; then
            log "ERROR: Required artifact not found: $source_path"
            return 1
        else
            log "Skipping optional artifact: $source_path"
            return 0
        fi
    fi

    local target="$ARCHIVE_ROOT/$VERSION/$archive_name"
    mkdir -p "$(dirname "$target")"

    log "Archiving: $source_path → $target"
    tar -czf "$target" -C "$(dirname "$source_path")" "$(basename "$source_path")" 2>/dev/null || \
        (log "WARNING: Could not compress, copying directly" && cp -r "$source_path" "$target")
}

archive_to_nexus() {
    local source_path="$1" archive_name="$2" required="${3:-false}"

    if [[ ! -e "$source_path" ]]; then
        if [[ "$required" == "true" ]]; then
            log "ERROR: Required artifact not found: $source_path"
            return 1
        fi
        return 0
    fi

    local tmp_archive="/tmp/${archive_name}"
    tar -czf "$tmp_archive" -C "$(dirname "$source_path")" "$(basename "$source_path")"

    local repo="${NEXUS_REPO:-embedded-firmware-releases}"
    local nexus_path="${VERSION}/${archive_name}"

    log "Uploading to Nexus: $nexus_path"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -u "$NEXUS_USER:$NEXUS_PASSWORD" \
        --upload-file "$tmp_archive" \
        "$NEXUS_HOST_URL/repository/$repo/$nexus_path" 2>/dev/null || echo "000")

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        log "Uploaded to Nexus: $nexus_path"
    else
        log "Nexus upload failed (HTTP $http_code), falling back to filesystem"
        archive_file_system "$source_path" "$archive_name" "$required"
    fi

    rm -f "$tmp_archive"
}

archive_artifacts_from_config() {
    log "Archiving artifacts per config: $ARCHIVE_MAPPING"

    jq -c '.archive.artifacts | to_entries[]' "$ARCHIVE_MAPPING" 2>/dev/null | while read -r entry; do
        local key
        key=$(echo "$entry" | jq -r '.key')
        local path
        path=$(echo "$entry" | jq -r '.value.path' | sed "s|\${WORKSPACE}|$WORKSPACE|g;s|\${BUILD_DIR}|$BUILD_DIR|g")
        local archive_name
        archive_name=$(echo "$entry" | jq -r '.value.archive_name' | sed "s|\${VERSION}|$VERSION|g")
        local required
        required=$(echo "$entry" | jq -r '.value.required // false')

        log "Processing artifact: $key"

        local archive_type="${ARCHIVE_TYPE:-filesystem}"
        if [[ "$archive_type" == "nexus" && -n "$NEXUS_PASSWORD" ]]; then
            archive_to_nexus "$path" "$archive_name" "$required"
        else
            archive_file_system "$path" "$archive_name" "$required"
        fi
    done
}

generate_sbom() {
    log "Generating Software Bill of Materials..."
    mkdir -p "$BUILD_DIR/sbom"

    tee "$BUILD_DIR/sbom/sbom.spdx.json" <<EOF
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "${CI_PROJECT_NAME:-embedded-firmware}",
  "documentNamespace": "${CI_PROJECT_URL:-local}/${VERSION}",
  "creationInfo": {
    "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "creators": ["Tool: CICD-Pipeline", "Organization: ${CI_PROJECT_NAMESPACE:-embedded}"]
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package",
      "name": "${CI_PROJECT_NAME:-embedded-firmware}",
      "versionInfo": "$VERSION",
      "downloadLocation": "${NEXUS_HOST_URL:-local}/repository/embedded-firmware-releases/$VERSION/",
      "supplier": "Organization: ${CI_PROJECT_NAMESPACE:-embedded}",
      "filesAnalyzed": false
    }
  ]
}
EOF
    log "SBOM generated: $BUILD_DIR/sbom/sbom.spdx.json"
}

generate_archive_manifest() {
    local manifest="$ARCHIVE_ROOT/$VERSION/MANIFEST.json"
    mkdir -p "$(dirname "$manifest")"

    tee "$manifest" <<EOF
{
  "version": "$VERSION",
  "release": $(is_release),
  "project": "${CI_PROJECT_NAME:-embedded-firmware}",
  "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "branch": "${CI_COMMIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pipeline_id": "${CI_PIPELINE_ID:-local}",
  "build_number": "${BUILD_NUMBER:-local}",
  "artifacts": $(jq '.archive.artifacts | to_entries | map({key: .key, archive_name: .value.archive_name})' "$ARCHIVE_MAPPING" 2>/dev/null || echo '[]'),
  "archive_root": "$ARCHIVE_ROOT/$VERSION",
  "nexus_url": "${NEXUS_HOST_URL:-}/repository/${NEXUS_REPO:-embedded-firmware-releases}/$VERSION/"
}
EOF
}

cleanup_old_snapshots() {
    local keep_count="${ARCHIVE_RETENTION_SNAPSHOTS:-10}"

    if [[ "$(is_release)" == "false" ]]; then
        log "Cleaning up old snapshots (keeping latest $keep_count)..."
        find "$ARCHIVE_ROOT" -maxdepth 1 -type d -name '*-SNAPSHOT-*' 2>/dev/null | \
            sort -r | tail -n +$((keep_count + 1)) | while read -r old_dir; do
            log "Removing old snapshot: $old_dir"
            rm -rf "$old_dir"
        done
    fi
}

main() {
    log "Starting artifact archiving"

    VERSION=$(resolve_version)
    log "Version: $VERSION (release: $(is_release))"

    generate_sbom
    archive_artifacts_from_config
    generate_archive_manifest
    cleanup_old_snapshots

    log "All artifacts archived successfully"
    echo "ARCHIVE_VERSION=$VERSION"
    echo "ARCHIVE_PATH=$ARCHIVE_ROOT/$VERSION"

    if [[ "$(is_release)" == "true" ]]; then
        log "RELEASE ARCHIVE COMPLETED: $VERSION"
    fi
}

main "$@"
