#!/usr/bin/env python3
"""Update package metadata from an upstream TokenSave release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


UPSTREAM_REPOSITORY = "aovestdipaperino/tokensave"
UPSTREAM_API = f"https://api.github.com/repos/{UPSTREAM_REPOSITORY}"
VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+)$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def fetch_bytes(url: str) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tokensave-bin-release-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token and urlsplit(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"could not download {url}: {error}") from error


def fetch_json(url: str) -> dict[str, Any]:
    try:
        value = json.loads(fetch_bytes(url))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON from {url}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"expected an object from {url}")
    return value


def normalize_version(tag: str) -> str:
    match = VERSION_PATTERN.fullmatch(tag)
    if not match:
        raise ValueError(f"unsupported release tag: {tag!r}")
    return match.group(1)


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = tuple(int(part) for part in normalize_version(candidate).split("."))
    current_parts = tuple(int(part) for part in normalize_version(current).split("."))
    return candidate_parts > current_parts


def parse_sha256sums(contents: str, filename: str) -> str:
    for line in contents.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[-1].lstrip("*") == filename:
            checksum = fields[0].lower()
            if not SHA256_PATTERN.fullmatch(checksum):
                raise ValueError(f"invalid SHA-256 checksum for {filename}")
            return checksum
    raise ValueError(f"no SHA-256 checksum found for {filename}")


def validate_mit_license(contents: bytes) -> None:
    required_text = (
        b"MIT License",
        b"Permission is hereby granted, free of charge",
    )
    if not all(marker in contents for marker in required_text):
        raise ValueError("upstream LICENSE does not contain the expected MIT license text")


def validate_release_archive(
    release: dict[str, str],
    *,
    downloader: Callable[[str], bytes] = fetch_bytes,
) -> None:
    actual_checksum = hashlib.sha256(downloader(release["archive_url"])).hexdigest()
    if actual_checksum != release["archive_sha256"]:
        raise ValueError(
            f"archive checksum mismatch: expected {release['archive_sha256']}, got {actual_checksum}"
        )


def release_from_github(tag: str | None = None) -> dict[str, str]:
    endpoint = f"{UPSTREAM_API}/releases/latest"
    if tag:
        endpoint = f"{UPSTREAM_API}/releases/tags/v{normalize_version(tag)}"
    release = fetch_json(endpoint)
    if release.get("draft") or release.get("prerelease"):
        raise RuntimeError("the selected upstream release is not a stable published release")

    tag_name = release.get("tag_name")
    if not isinstance(tag_name, str):
        raise RuntimeError("upstream release has no tag_name")
    version = normalize_version(tag_name)
    expected_archive = f"tokensave-v{version}-x86_64-linux.tar.gz"
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("upstream release has no assets")

    asset_urls: dict[str, str] = {}
    for asset in assets:
        if isinstance(asset, dict):
            name = asset.get("name")
            download_url = asset.get("browser_download_url")
            if isinstance(name, str) and isinstance(download_url, str):
                asset_urls[name] = download_url
    archive_url = asset_urls.get(expected_archive)
    sums_url = asset_urls.get("SHA256SUMS")
    if not archive_url or not sums_url:
        raise RuntimeError(f"release v{version} is missing {expected_archive} or SHA256SUMS")

    archive_sha256 = parse_sha256sums(fetch_bytes(sums_url).decode("utf-8"), expected_archive)
    license_url = f"https://raw.githubusercontent.com/{UPSTREAM_REPOSITORY}/{tag_name}/LICENSE"
    license_contents = fetch_bytes(license_url)
    validate_mit_license(license_contents)
    license_sha256 = hashlib.sha256(license_contents).hexdigest()
    release_url = release.get("html_url")
    if not isinstance(release_url, str):
        release_url = f"https://github.com/{UPSTREAM_REPOSITORY}/releases/tag/{tag_name}"
    body = release.get("body")
    if not isinstance(body, str):
        body = ""

    return {
        "version": version,
        "tag": tag_name,
        "archive_name": expected_archive,
        "archive_url": archive_url,
        "archive_sha256": archive_sha256,
        "license_sha256": license_sha256,
        "release_url": release_url,
        "body": body,
    }


def update_pkgbuild_text(
    contents: str,
    *,
    version: str,
    archive_sha256: str,
    license_sha256: str,
) -> str:
    if not SHA256_PATTERN.fullmatch(archive_sha256) or not SHA256_PATTERN.fullmatch(license_sha256):
        raise ValueError("PKGBUILD checksums must be SHA-256 values")
    updated, version_count = re.subn(
        r"^pkgver=\S+$",
        f"pkgver={version}",
        contents,
        count=1,
        flags=re.MULTILINE,
    )
    if version_count != 1:
        raise ValueError("PKGBUILD must contain exactly one pkgver assignment")
    updated, release_count = re.subn(
        r"^pkgrel=\S+$",
        "pkgrel=1",
        updated,
        count=1,
        flags=re.MULTILINE,
    )
    if release_count != 1:
        raise ValueError("PKGBUILD must contain exactly one pkgrel assignment")
    updated, checksums_count = re.subn(
        r"(?ms)^sha256sums=\(\n.*?^\)",
        f"sha256sums=(\n  '{archive_sha256}'\n  '{license_sha256}'\n)",
        updated,
        count=1,
    )
    if checksums_count != 1:
        raise ValueError("PKGBUILD must contain one sha256sums array")
    return updated


def render_readme_metadata(*, version: str, archive_name: str, release_url: str) -> str:
    return "\n".join(
        [
            "<!-- release-metadata:start -->",
            f"- Packaged release: `v{version}`",
            f"- Release archive: `{archive_name}`",
            f"- Upstream release: <{release_url}>",
            "<!-- release-metadata:end -->",
        ]
    )


def render_package_command(*, version: str) -> str:
    return "\n".join(
        [
            "<!-- package-file:start -->",
            "```bash",
            f"sudo pacman -U tokensave-bin-{version}-1-x86_64.pkg.tar.zst",
            "```",
            "<!-- package-file:end -->",
        ]
    )


def render_release_notes(*, version: str, release_url: str, body: str) -> str:
    notes = body.strip() or "No upstream release notes were provided."
    return "\n".join(
        [
            f"# TokenSave v{version}",
            "",
            f"Source release: <{release_url}>",
            "",
            notes,
            "",
        ]
    )


def replace_marked_block(contents: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(
        rf"(?ms)^{re.escape(start)}\n.*?^{re.escape(end)}$"
    )
    updated, count = pattern.subn(replacement, contents, count=1)
    if count != 1:
        raise ValueError(f"README is missing the marked block {start!r}")
    return updated


def package_version(contents: str) -> str:
    matches = re.findall(r"^pkgver=(\S+)$", contents, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("PKGBUILD must contain exactly one pkgver assignment")
    return normalize_version(matches[0])


def update_repository(root: Path, release: dict[str, str]) -> bool:
    pkgbuild_path = root / "PKGBUILD"
    pkgbuild = pkgbuild_path.read_text(encoding="utf-8")
    if not is_newer_version(release["version"], package_version(pkgbuild)):
        return False
    validate_release_archive(release)
    pkgbuild_path.write_text(
        update_pkgbuild_text(
            pkgbuild,
            version=release["version"],
            archive_sha256=release["archive_sha256"],
            license_sha256=release["license_sha256"],
        ),
        encoding="utf-8",
    )

    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = replace_marked_block(
        readme,
        "<!-- release-metadata:start -->",
        "<!-- release-metadata:end -->",
        render_readme_metadata(
            version=release["version"],
            archive_name=release["archive_name"],
            release_url=release["release_url"],
        ),
    )
    readme = replace_marked_block(
        readme,
        "<!-- package-file:start -->",
        "<!-- package-file:end -->",
        render_package_command(version=release["version"]),
    )
    readme_path.write_text(readme, encoding="utf-8")

    release_notes_path = root / "docs" / "releases" / f"v{release['version']}.md"
    release_notes_path.parent.mkdir(parents=True, exist_ok=True)
    release_notes_path.write_text(
        render_release_notes(
            version=release["version"],
            release_url=release["release_url"],
            body=release["body"],
        ),
        encoding="utf-8",
    )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        help="specific stable upstream tag to process; defaults to the latest release",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="package repository root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        release = release_from_github(args.tag)
        changed = update_repository(args.root, release)
    except (RuntimeError, ValueError, OSError) as error:
        print(f"update-release: {error}", file=sys.stderr)
        return 1
    if changed:
        print(f"Prepared TokenSave v{release['version']}")
    else:
        print(f"TokenSave v{release['version']} is already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
