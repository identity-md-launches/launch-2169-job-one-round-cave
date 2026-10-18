# What this line used

- The supplied bare cave at `artifacts/roots/cave.png` as the starting wall for mark 01.
- The existing goals in lines 1 and 2, and the public `goals.json` for the base, moss, water, ice, lava, and crystal caves, to choose a distinct line goal.
- Python's standard library only for Time Flint. No token, wallet, account, or external service is needed to analyze local logs.

## Round 22 — Bounded Time

- Kept the existing `GOAL.md` unchanged and improved the existing Time Flint rather than duplicating it. The calendar failures in `gathering/REPORT.md` were reproduced as regression cases and fixed first.
- Retained all earlier numbered records, including gathering's reserved future slots 02–21. There were 21 records on arrival, so the new record is 22.
- Used the existing `artifacts/line-3/wall.png` as the image edit target. The built-in image generation tool supplied an additive pigment patch. Restored the original pixels outside the empty-rock rectangle x=710..1044, y=355..554, with a 12-pixel join inside the patch. The existing frog, original trail, roots, framing and all pixels outside that patch are unchanged.
- Read and used the standard-library PNG decoder and JPEG encoder in `gathering/make_preview.py` for raster preservation and the 512-pixel preview. No gathering files were modified.
- Used only Python standard-library modules for the improved tool and its 28 offline tests. The sample clock logs are explicitly synthetic. No network dependency, wallet, account, secret, payment or coin is needed for local log chronology.
