# tokensave-bin

[![Package CI](https://github.com/rNoz/tokensave-bin/actions/workflows/aur-package.yml/badge.svg)](https://github.com/rNoz/tokensave-bin/actions/workflows/aur-package.yml)
[![Release automation](https://github.com/rNoz/tokensave-bin/actions/workflows/publish-release.yml/badge.svg)](https://github.com/rNoz/tokensave-bin/actions/workflows/publish-release.yml)
[![AUR package](https://img.shields.io/aur/version/tokensave-bin.svg?logo=archlinux)](https://aur.archlinux.org/packages/tokensave-bin)

Reproducible Arch Linux package metadata for the prebuilt **TokenSave** command-line tool. The package reuses the upstream x86_64 Linux release rather than compiling Rust source code.

## Upstream

- Repository: <https://github.com/aovestdipaperino/tokensave>
<!-- release-metadata:start -->
- Packaged release: `v7.12.1`
- Release archive: `tokensave-v7.12.1-x86_64-linux.tar.gz`
- Upstream release: <https://github.com/aovestdipaperino/tokensave/releases/tag/v7.12.1>
<!-- release-metadata:end -->
- Installed command: `/usr/bin/tokensave`
- Maintainer: `rNoz <maintainers@users.noreply.github.com>`

The release archive and matching upstream MIT license are pinned by SHA-256 in `PKGBUILD`. Runtime dependencies are `glibc` and `libgcc`.

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
sudo pacman -U tokensave-bin-7.12.1-1-x86_64.pkg.tar.zst
```
<!-- package-file:end -->

## Local verification

The package can be built without installing it:

```bash
makepkg --verifysource --force
makepkg --cleanbuild --clean --force
pkgfile=$(find . -maxdepth 1 -type f -name 'tokensave-bin-*.pkg.tar.*' -print -quit)
namcap PKGBUILD "$pkgfile"
```

The package contents are intentionally small:

```text
/usr/bin/tokensave
/usr/share/licenses/tokensave-bin/LICENSE
```

For the complete maintenance procedure, see [`docs/maintenance.md`](docs/maintenance.md).

## License

Repository metadata, documentation, and automation are Apache-2.0. The packaged TokenSave executable and its included license are upstream works distributed under the MIT license. This repository is not affiliated with or endorsed by the upstream project.
