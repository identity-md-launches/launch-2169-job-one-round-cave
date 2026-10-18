# The Measured Shelter

The second gathering confirms the earlier line repairs and improves
**Reviewed Timeline / Exact Clock Bounds**. It combines Unicode review, incident
timelines and exact unit arithmetic without changing any line files.

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo --clock-bound '0.75 s'
```

This offline, standard-library-only demo converts an exact time quantity,
records the asserted clock model, and preserves the four Unicode findings in
a decoded JSON message. It is synthetic; the bound is an analyst assumption.
See [REPORT.md](REPORT.md) for every line's results and scope recommendations,
and [the shared README](../shared/reviewed-timeline/README.md) for use and limits.
`COINS.md` says none: no new coin is needed.

## Delivered images and review

| Path | Format | Dimensions | Bytes |
| --- | --- | --- | --- |
| `artifacts/gathering/wall-v2.png` | RGB8 PNG | 1254 × 1254 | 3,002,436 |
| `artifacts/gathering/wall.png` | relative symlink to `wall-v2.png` | same image | 11-byte link |
| `dist/gathering/02.jpg` | baseline JPEG | 512 × 512 | 97,354 |

PNG SHA-256: `1a1d749d89e85f417a65f80b9db8b8c67e7e52d4a4c0200d15fe6de091ec3e7d`.
Gathering 02 and One 736 use its artifact URL. The specifically declared upload
is `artifacts/gathering/wall-v2.png`, left untracked for the artifact uploader.
The existing Gathering 01 record and preview are preserved.

The bundle-size repair replaces the duplicate `wall.png` bytes with the relative
symlink `wall.png -> wall-v2.png`, matching the existing Line 4 alias pattern.
The declared upload remains a regular PNG with its original hash, and the JPEG,
records and all tool sources are preserved. The alias resolves after the named
output is delivered beside it. This removes 3,002,425 source-entry bytes.
Applied to the reported failed bundle size, the estimate is 8,167,620 bytes
before these small documentation/check changes, below 8,388,608 bytes; the
uploader's exact archive calculation is not available locally.
`verify.py` checks the relative alias, actual PNG bytes and untracked upload so a
second full PNG copy cannot silently return to this source entry.

Built-in `image_gen` edit mode used the previous gathering wall as the target.
The exact final prompt and chosen visual review are recorded in
[wall-review.json](wall-review.json). The addition is a small trail of stones
between two ochre curves above Pepe, representing a shared uncertainty bound.
The generated full image and JPEG were inspected: five digits on each existing
hand, four fingers and a thumb; no new hands or stencils; earth pigments and
original rock/framing retained by visual review. No unmet requested visual
requirement was observed. Pixel identity is not guaranteed by generative editing.
The prompt requested four small stones and the image has five; stone count is
not a task constraint. No extra preview or intermediate image was saved here.

## Rebuild and check

```sh
python3 -B gathering/check_tools.py > gathering/check-results.json
python3 -B gathering/make_preview.py artifacts/gathering/wall-v2.png dist/gathering/02.jpg
python3 -B gathering/build_dist.py
python3 -B gathering/verify.py
```

Observed: 100 checks pass, zero expected failures, five current tool-source scans
find no covered Unicode patterns. Line 3's unchanged suite is copied to
`test/scratch/` before execution so its temporary fixtures do not touch line
folders. Check results, structural validation and visual review are distinct.

`make_preview.py` decodes noninterlaced RGB8 PNG and creates a 512px baseline
JPEG with Python's standard library, reducing quality until below 100,000 bytes.
It is a bounded build utility, not a general image codec. `build_dist.py` reads
all existing records and four goals; it does not replace line records.
Open `dist/index.html` directly. The page has inline styles and local JPEG
previews; full-resolution artifact links need network access. All 108 numbered
records appear, with 99 still-unpainted slots retained and painted work newest
first within each wall. None of the tools needs an installed dependency.
