# Working rules

Preserve the exact firmware scope and distinguish host simulation, emulator
evidence and physical vehicle evidence. Never install to a vehicle without the
owner's explicit authorization for that vehicle operation.

Run `python3 -m unittest discover -s tests -v` after code changes.
Validate/build a fresh release with `python3 tools/package_release.py`.
The builder refuses an existing output; use `--output` with a fresh filename.
Shell syntax check: `sh -n sd-card/mod/custom.sh sd-card/mod/command.sh sd-card/uk-localization/scripts/localization.sh`.

Keep the released action at CHECK. Do not silently broaden target fingerprints,
regenerate payload checksums after an unreviewed binary change, include emulator
timeout hooks or commit logs, vehicle identity, credentials or backups.

Do not commit or push unless the user requests it. Main README is bilingual:
Ukrainian and English. Package artifacts remain marked preview until actual QNX,
vehicle installation and restoration evidence is available.

## Unit-script rules (learned on the car, 2026-10-24)

- Entry chain: M.I.B. V3.6+ "Run individual script" -> `mod/command.sh` -> `mod/custom.sh` -> installer.
  Older M.I.B. runs `custom.sh` directly. `command.sh` must do nothing when sourced.
- Unit shell is pdksh: no alias names as functions (`hash`), no failing redirection on `:`; test with
  `UK_TEST_SHELL=oksh` and `mksh` besides `/bin/sh`.
- `/tmp` is `/dev/shmem` (files only): lock/arm/reader temp are plain files, never folders.
- SD1 is read-only until `mount -uw /net/mmx/fs/sda0`; SD logging is best-effort, INSTALL still needs the SD copy.
- Tools: SD `apps/sbin` has sed/xxd/sha1sum/reader; `awk` comes from the unit PATH (gawk). Check
  `analysis/car-harvest-20261022/listings/` in the workspace before adding any other utility.
- Compare against M.I.B. tag V3.7.1, not the old pinned commit in `package.json`.
- Copy files into `mod/`, never replace the folder (macOS Finder replaces; `mod/` holds M.I.B. files).

## Release procedure

1. `python3 -m unittest discover -s tests` under `/bin/sh`, `oksh` and `mksh`; shell syntax check of all three scripts.
2. Rehash `SHA1SUMS`/`package.json` only for scripts changed on purpose; bump the version in `tools/package_release.py`, README, guide.
3. `python3 tools/package_release.py`; commit; push only when asked.
4. Publish one pre-release with ZIP + `.sha256`, download it back and verify the checksum and key strings.
5. Keep a single current release; delete superseded releases and tags when the owner asks.

