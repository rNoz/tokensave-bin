# Maintenance

## Updating the packaged release manually

1. Check the upstream TokenSave releases at <https://github.com/aovestdipaperino/tokensave/releases>.
2. Set `pkgver` in `PKGBUILD` to the release number without the leading `v`.
3. Update the release archive URL if the upstream filename changes.
4. Obtain the matching archive and `LICENSE` SHA-256 values from the upstream release/tag.
5. Update both entries in `sha256sums`.
6. Regenerate `.SRCINFO`:

   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

Do not replace fixed release URLs with a moving `latest` URL, and do not add source compilation unless the upstream binary is unavailable or unusable.

## Automated release updates

The `update-release.yml` workflow checks the latest stable upstream release hourly and also accepts a
`repository_dispatch` event of type `tokensave-release-published`. It validates the release archive,
the upstream `SHA256SUMS` asset, and the tagged MIT license before updating:

- `PKGBUILD` version and checksums;
- generated `.SRCINFO`;
- the marked current-release and package-file sections in `README.md`; and
- `docs/releases/vX.Y.Z.md` with the upstream release notes and source link.

The workflow opens a pull request instead of committing directly to the default branch. Package validation
runs on that pull request, so a maintainer reviews the complete metadata change before merging it.

When `RELEASE_TOKEN` is configured, the workflow uses it for the release branch and pull request so ordinary
push and pull-request checks run normally. Without that secret, it falls back to the repository token and
explicitly dispatches package validation for the generated branch.

GitHub cannot deliver a release event from the unrelated upstream repository directly to this repository.
The scheduled check is therefore the self-contained fallback. An upstream workflow or GitHub App can
remove the polling delay by calling this repository's `repository_dispatch` endpoint with a
`tokensave-release-published` event and a `tag` payload such as `v7.13.0`.

To replay a specific release manually:

```bash
python3 scripts/update_release.py --tag v7.13.0
makepkg --printsrcinfo > .SRCINFO
```

## Private repository and publication configuration

The private GitHub repository follows the relevant factory-repository practices without copying its
project-specific patching or test tasks:

- `publish-release.yml` creates or refreshes a private GitHub release after a merged
  `automation/tokensave-vX.Y.Z` pull request;
- AUR publication is optional and is skipped until `AUR_SSH_KEY` is configured;
- when enabled, the workflow publishes only `PKGBUILD` and `.SRCINFO` to the existing `tokensave-bin`
  AUR package, or initializes the first package submission, and verifies the pinned AUR host keys.

Configure these repository secrets only through GitHub's secret storage:

| Secret or variable | Purpose |
| --- | --- |
| `RELEASE_TOKEN` | Optional GitHub token used to create release branches/PRs and trigger normal checks; the workflow falls back to `GITHUB_TOKEN` for testing. |
| `AUR_SSH_KEY` | Optional private SSH key already authorized for the AUR account. |
| `AUR_USERNAME` | AUR commit author name, required with `AUR_SSH_KEY`. |
| `AUR_EMAIL` | AUR commit author email, required with `AUR_SSH_KEY`. |
| `AUR_PKG_NAME` | Repository variable for the AUR package name; defaults to `tokensave-bin`. |

The AUR private key is never stored in this repository or printed by CI. The first publication creates
the package repository; later publications clone and update it.

## Required local checks

Run these commands from the repository root:

```bash
bash -n PKGBUILD
makepkg --printsrcinfo | diff -u .SRCINFO -
makepkg --verifysource --force
makepkg --cleanbuild --clean --force
namcap PKGBUILD
```

Inspect the resulting package without installing it:

```bash
pkgfile=$(find . -maxdepth 1 -type f -name 'tokensave-bin-*.pkg.tar.*' -print -quit)
bsdtar -tf "$pkgfile"
pacman -Qp --info "$pkgfile"
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
bsdtar -xf "$pkgfile" -C "$root"
"$root/usr/bin/tokensave" --version
"$root/usr/bin/tokensave" --help >/dev/null
```

The package must contain `/usr/bin/tokensave` and `/usr/share/licenses/tokensave-bin/LICENSE`. Do not use `makepkg -si` in automated checks.

The CI workflow pins the Arch base image by digest. Refresh that digest deliberately when updating the workflow, and review the resulting package-tool versions before committing the change.

## Commit checklist

Before committing a release update:

- confirm the release archive and license checksums match upstream;
- confirm `.SRCINFO` matches `makepkg --printsrcinfo` exactly;
- review `git diff --check` and `git diff --cached --check`;
- ensure no downloaded archives, package artifacts, credentials, or local state are staged.
