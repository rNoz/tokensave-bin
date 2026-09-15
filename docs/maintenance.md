# Maintenance

## Updating the packaged release

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
