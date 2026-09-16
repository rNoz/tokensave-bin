# Maintenance

## Updating the packaged release manually

1. Check the upstream TokenSave releases at <https://github.com/aovestdipaperino/tokensave/releases>.
2. Set `pkgver` in `PKGBUILD` to the release number without the leading `v`.
3. Update the release archive URLs if the upstream filenames change.
4. Obtain the matching archive and `LICENSE` SHA-256 values from the upstream release/tag (`SHA256SUMS`).
5. Update `sha256sums_x86_64`, `sha256sums_aarch64`, and license `sha256sums`.
6. Regenerate `.SRCINFO`:

   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

Do not replace fixed release URLs with a moving `latest` URL, and do not add source compilation unless the upstream binary is unavailable or unusable.

## Automated release updates

The `update-release.yml` workflow checks the latest stable upstream release three times a day
(08:17, 14:17, and 20:17 UTC, covering the observed upstream release windows) and also accepts a
`repository_dispatch` event of type `tokensave-release-published`. Scheduled runs exit early when the
packaged version already matches upstream, so no runner time is spent on no-op checks; manual and
dispatch triggers always run the full update. It validates the release archive bytes, the upstream
`SHA256SUMS` asset, the GitHub-reported SHA-256 digest of each release asset (an independent
integrity source that must agree with `SHA256SUMS`), and the tagged MIT license before updating:

- `PKGBUILD` version and checksums;
- generated `.SRCINFO`;
- the marked current-release and package-file sections in `README.md`.

The workflow opens a pull request instead of committing directly to the default branch. Package validation
runs on that pull request, so a maintainer reviews the complete package metadata change before merging it.
The publish workflow fetches the matching upstream release notes at publication time and stores them in
the GitHub release; release-note copies are intentionally not committed to this package repository.

When `RELEASE_TOKEN` is configured, the workflow uses it for the release branch and pull request so ordinary
push and pull-request checks run normally. Without that secret, it falls back to the repository token and
explicitly dispatches package validation for the generated branch.

GitHub cannot deliver a release event from the unrelated upstream repository directly to this repository.
The scheduled check is therefore the self-contained fallback. An upstream workflow or GitHub App can
remove the polling delay by calling this repository's `repository_dispatch` endpoint with a
`tokensave-release-published` event and a `tag` payload such as `v7.13.0`.

To prepare a newer specific upstream release manually:

```bash
python3 scripts/update_release.py --tag v7.13.0
makepkg --printsrcinfo > .SRCINFO
```

The updater intentionally ignores the current and older versions; it does not provide a forced
downgrade or regeneration mode.

## Private repository and publication configuration

The repository automation manages GitHub releases and optional AUR publication:

- `publish-release.yml` creates or refreshes a private GitHub release after a merged
  `automation/tokensave-vX.Y.Z` pull request;
- AUR publication is optional and is skipped until `AUR_SSH_KEY` is configured;
- when enabled, the workflow publishes only `PKGBUILD` and `.SRCINFO` to the existing `tokensave-bin`
  AUR package, or initializes the first package submission, and verifies the pinned AUR host keys.

Configure these repository secrets only through GitHub's secret storage:

| Secret or variable | Purpose |
| --- | --- |
| `RELEASE_TOKEN` | GitHub token used for release branches/PRs and publication; the workflow falls back to the scoped `GITHUB_TOKEN` when testing without this secret. |
| `AUR_SSH_KEY` | Optional private SSH key already authorized for the AUR account. |
| `AUR_USERNAME` | AUR commit author name, required with `AUR_SSH_KEY`. |
| `AUR_EMAIL` | AUR commit author email, required with `AUR_SSH_KEY`. |
| `AUR_PKG_NAME` | Repository variable for the AUR package name; defaults to `tokensave-bin`. |

The AUR private key is never stored in this repository or printed by CI. The first publication creates
the package repository; later publications clone and update it.

The workflows never use secrets for pull-request validation. Package validation has read-only repository
permissions, while release and AUR publication run only after a same-repository automation pull request
is merged or an owner manually dispatches publication.

## Required local checks

Run these commands from the repository root:

```bash
# Verify PKGBUILD syntax and .SRCINFO
bash -n PKGBUILD
makepkg --printsrcinfo | diff -u .SRCINFO -

# Run Python unit tests
python3 -m unittest discover -s tests -v

# Verify and build x86_64 package
makepkg --verifysource --force
makepkg --cleanbuild --clean --force

# Verify and build aarch64 package
sed 's/CARCH=.*/CARCH="aarch64"/; s/CHOST=.*/CHOST="aarch64-unknown-linux-gnu"/' /etc/makepkg.conf > /tmp/makepkg-aarch64.conf
grep -q '^CARCH="aarch64"' /tmp/makepkg-aarch64.conf
makepkg --config /tmp/makepkg-aarch64.conf --verifysource --force
makepkg --config /tmp/makepkg-aarch64.conf --cleanbuild --clean --force

# Inspect both packages with namcap
namcap PKGBUILD tokensave-bin-*-x86_64.pkg.tar.zst tokensave-bin-*-aarch64.pkg.tar.zst
```

Inspect the resulting packages without installing them:

```bash
# Inspect x86_64 package and smoke-test executable
x86_pkgfile=$(find . -maxdepth 1 -type f -name 'tokensave-bin-*-x86_64.pkg.tar.*' -print -quit)
bsdtar -tf "$x86_pkgfile"
pacman -Qp --info "$x86_pkgfile"
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
bsdtar -xf "$x86_pkgfile" -C "$root"
"$root/usr/bin/tokensave" --version
"$root/usr/bin/tokensave" --help >/dev/null

# Inspect aarch64 package metadata and ELF headers
aarch64_pkgfile=$(find . -maxdepth 1 -type f -name 'tokensave-bin-*-aarch64.pkg.tar.*' -print -quit)
bsdtar -tf "$aarch64_pkgfile"
pacman -Qp --info "$aarch64_pkgfile"
root_arm=$(mktemp -d)
trap 'rm -rf "$root_arm"' EXIT
bsdtar -xf "$aarch64_pkgfile" -C "$root_arm"
readelf -h "$root_arm/usr/bin/tokensave" | grep -E 'Class:\s+ELF64'
readelf -h "$root_arm/usr/bin/tokensave" | grep -E 'Machine:\s+AArch64'
readelf -d "$root_arm/usr/bin/tokensave" | grep NEEDED
```

The package must contain `/usr/bin/tokensave` and `/usr/share/licenses/tokensave-bin/LICENSE`. Do not use `makepkg -si` in automated checks.

Package validation in `aur-package.yml` additionally runs `shellcheck` on `PKGBUILD`, `flake8` on the
Python automation, and a pinned (version + SHA-256) [aurscan](https://github.com/manticore-projects/aurscan)
static security audit of the repository on every relevant push and pull request. When bumping the pinned
aurscan version, download the new `aurscan-linux-amd64` asset, record its SHA-256, and update both the
URL and the checksum in the workflow together.

The CI workflow pins the Arch base image by digest. Refresh that digest deliberately when updating the workflow, and review the resulting package-tool versions before committing the change.

## Commit checklist

Before committing a release update:

- confirm the release archive and license checksums match upstream;
- confirm `.SRCINFO` matches `makepkg --printsrcinfo` exactly;
- review `git diff --check` and `git diff --cached --check`;
- ensure no downloaded archives, package artifacts, credentials, or local state are staged.
