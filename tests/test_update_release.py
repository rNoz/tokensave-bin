import os
import unittest
from unittest.mock import patch

from scripts.update_release import (
    fetch_bytes,
    is_newer_version,
    parse_sha256sums,
    render_readme_metadata,
    render_package_command,
    render_release_notes,
    validate_mit_license,
    validate_release_archive,
    update_pkgbuild_text,
)


class UpdateReleaseTests(unittest.TestCase):
    def test_fetch_bytes_uses_github_token_only_for_github_api_requests(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return b"response"

        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}, clear=False),
            patch("scripts.update_release.urlopen", return_value=Response()) as urlopen,
        ):
            self.assertEqual(
                fetch_bytes("https://api.github.com/repos/example/project"),
                b"response",
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

    def test_parse_sha256sums_selects_the_named_archive(self):
        sums = """\
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  tokensave-v7.12.1-aarch64-linux.tar.gz
184612db16800e384a1bcdc7fadcc53fa73bda70240f9c0416ac4b88c7e924fb *tokensave-v7.12.1-x86_64-linux.tar.gz
"""

        self.assertEqual(
            parse_sha256sums(sums, "tokensave-v7.12.1-x86_64-linux.tar.gz"),
            "184612db16800e384a1bcdc7fadcc53fa73bda70240f9c0416ac4b88c7e924fb",
        )

    def test_update_pkgbuild_text_changes_release_values_only(self):
        original = """\
pkgver=7.12.1
pkgrel=7
source=(
  "https://example.invalid/v$pkgver/tokensave-v$pkgver-$CARCH-linux.tar.gz"
  "tokensave-license-$pkgver::https://example.invalid/v$pkgver/LICENSE"
)
sha256sums=(
  'old-archive'
  'old-license'
)
"""

        updated = update_pkgbuild_text(
            original,
            version="7.13.0",
            archive_sha256="1" * 64,
            license_sha256="2" * 64,
        )

        self.assertIn("pkgver=7.13.0", updated)
        self.assertIn("pkgrel=1", updated)
        self.assertIn(f"  '{'1' * 64}'", updated)
        self.assertIn(f"  '{'2' * 64}'", updated)
        self.assertNotIn("old-archive", updated)
        self.assertNotIn("old-license", updated)
        self.assertIn("tokensave-v$pkgver-$CARCH-linux.tar.gz", updated)

    def test_only_a_newer_upstream_version_is_an_update(self):
        self.assertTrue(is_newer_version("7.13.0", "7.12.1"))
        self.assertFalse(is_newer_version("7.12.1", "7.12.1"))
        self.assertFalse(is_newer_version("7.12.0", "7.12.1"))

    def test_render_readme_metadata_is_deterministic(self):
        rendered = render_readme_metadata(
            version="7.13.0",
            archive_name="tokensave-v7.13.0-x86_64-linux.tar.gz",
            release_url="https://github.com/aovestdipaperino/tokensave/releases/tag/v7.13.0",
        )

        self.assertEqual(
            rendered,
            """\
<!-- release-metadata:start -->
- Packaged release: `v7.13.0`
- Release archive: `tokensave-v7.13.0-x86_64-linux.tar.gz`
- Upstream release: <https://github.com/aovestdipaperino/tokensave/releases/tag/v7.13.0>
<!-- release-metadata:end -->""",
        )

    def test_render_package_command_keeps_markers_outside_the_code_fence(self):
        self.assertEqual(
            render_package_command(version="7.13.0"),
            """\
<!-- package-file:start -->
```bash
sudo pacman -U tokensave-bin-7.13.0-1-x86_64.pkg.tar.zst
```
<!-- package-file:end -->""",
        )

    def test_render_release_notes_preserves_upstream_body_with_provenance(self):
        rendered = render_release_notes(
            version="7.13.0",
            release_url="https://github.com/aovestdipaperino/tokensave/releases/tag/v7.13.0",
            body="Fixed indexing.",
        )

        self.assertIn("# TokenSave v7.13.0", rendered)
        self.assertIn("Source release: <https://github.com/aovestdipaperino/tokensave/releases/tag/v7.13.0>", rendered)
        self.assertIn("Fixed indexing.", rendered)

    def test_validate_mit_license_requires_mit_grant_text(self):
        validate_mit_license(
            b"MIT License\n\nPermission is hereby granted, free of charge, to any person."
        )
        with self.assertRaises(ValueError):
            validate_mit_license(b"Apache License")

    def test_validate_release_archive_checks_downloaded_bytes(self):
        archive = b"release archive"
        release = {
            "archive_url": "https://example.invalid/archive.tar.gz",
            "archive_sha256": __import__("hashlib").sha256(archive).hexdigest(),
        }

        validate_release_archive(release, downloader=lambda _: archive)
        with self.assertRaises(ValueError):
            validate_release_archive(
                {**release, "archive_sha256": "0" * 64},
                downloader=lambda _: archive,
            )


if __name__ == "__main__":
    unittest.main()
