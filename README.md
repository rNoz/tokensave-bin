# tokensave (AUR package)

<div align="center">

> Automated packaging for tokensave (Semantic Code Intelligence for AI Coding Agents) as tokensave-bin AUR package (x86_64, aarch64)

[![Package CI](https://github.com/rNoz/tokensave-bin/actions/workflows/aur-package.yml/badge.svg)](https://github.com/rNoz/tokensave-bin/actions/workflows/aur-package.yml)
[![AUR version](https://img.shields.io/aur/version/tokensave-bin.svg?logo=archlinux)](https://aur.archlinux.org/packages/tokensave-bin)
[![Security audit: aurscan](https://img.shields.io/badge/security%20audit-aurscan-informational?logo=shield&logoColor=white)](https://github.com/rNoz/tokensave-bin/actions/workflows/aur-package.yml)
[![Upstream release](https://img.shields.io/github/v/release/aovestdipaperino/tokensave?label=upstream%20release)](https://github.com/aovestdipaperino/tokensave/releases/latest)
[![License](https://img.shields.io/badge/license-Apache--2.0%20%2B%20MIT-blue.svg)](LICENSE)
[![Arch](https://img.shields.io/badge/arch-x86__64%20%7C%20aarch64-informational)](#installation)

</div>

Reproducible Arch Linux package metadata for the prebuilt **TokenSave** command-line tool. The package reuses the upstream x86_64 and aarch64 Linux releases rather than compiling Rust source code.

## Package

<!-- release-metadata:start -->
- Packaged release: `v7.14.0`
- Release archives: `tokensave-v7.14.0-x86_64-linux.tar.gz`, `tokensave-v7.14.0-aarch64-linux.tar.gz`
- Upstream release: <https://github.com/aovestdipaperino/tokensave/releases/tag/v7.14.0>
<!-- release-metadata:end -->
- Installed command: `/usr/bin/tokensave`

The release archives and matching upstream MIT license are pinned by SHA-256 in `PKGBUILD`; the updater additionally cross-checks the GitHub-reported asset digests against the upstream `SHA256SUMS`. Every change is validated in CI with `namcap`, dual-architecture builds, `shellcheck`, `flake8`, and a pinned [aurscan](https://github.com/manticore-projects/aurscan) security audit. Runtime dependencies are `glibc` and `libgcc`.

## Upstream

TokenSave is maintained at <https://github.com/aovestdipaperino/tokensave>. This repository packages
its prebuilt x86_64 and aarch64 Linux releases without compiling or modifying the upstream executable.

## Installation

Install from the AUR with an AUR helper:

```bash
yay -S tokensave-bin
```

Build manually from the package repository:

```bash
git clone https://aur.archlinux.org/tokensave-bin.git
cd tokensave-bin
makepkg -si
```

Install an already-built package directly:

<!-- package-file:start -->
```bash
# x86_64
sudo pacman -U tokensave-bin-7.14.0-1-x86_64.pkg.tar.zst

# aarch64
sudo pacman -U tokensave-bin-7.14.0-1-aarch64.pkg.tar.zst
```
<!-- package-file:end -->

## Local verification

The package can be built without installing it:

```bash
# Verify PKGBUILD syntax and .SRCINFO
bash -n PKGBUILD
makepkg --printsrcinfo | diff -u .SRCINFO -

# Verify and build x86_64
makepkg --verifysource --force
makepkg --cleanbuild --clean --force

# Verify and build aarch64
sed 's/CARCH=.*/CARCH="aarch64"/; s/CHOST=.*/CHOST="aarch64-unknown-linux-gnu"/' /etc/makepkg.conf > /tmp/makepkg-aarch64.conf
grep -q '^CARCH="aarch64"' /tmp/makepkg-aarch64.conf
makepkg --config /tmp/makepkg-aarch64.conf --verifysource --force
makepkg --config /tmp/makepkg-aarch64.conf --cleanbuild --clean --force

# Inspect packages
namcap PKGBUILD tokensave-bin-*-x86_64.pkg.tar.zst tokensave-bin-*-aarch64.pkg.tar.zst
```

The package contents are intentionally small:

```text
/usr/bin/tokensave
/usr/share/licenses/tokensave-bin/LICENSE
```

For the complete maintenance procedure, see [`docs/maintenance.md`](docs/maintenance.md).

## License

Repository metadata, documentation, and automation are Apache-2.0. The packaged TokenSave executable and its included license are upstream works distributed under the MIT license. This repository is not affiliated with or endorsed by the upstream project.
