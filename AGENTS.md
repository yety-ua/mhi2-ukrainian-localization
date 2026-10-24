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
