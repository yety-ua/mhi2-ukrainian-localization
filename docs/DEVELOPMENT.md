# Розробка / Development

[← README](../README.md)

```sh
python3 -m unittest discover -s tests -v
UK_TEST_SHELL=oksh python3 -m unittest discover -s tests   # also mksh: the unit's /bin/sh is a pdksh
python3 tools/audit_resources.py --output docs/resource-audit.json
sh -n sd-card/mod/custom.sh sd-card/mod/command.sh sd-card/mod/uk-localization/scripts/localization.sh
python3 tools/package_release.py
```

The packaging tool refuses existing output; use `--output` with a fresh filename. Runtime checks use M.I.B.'s SHA-1
utility; package metadata and the release sidecar also use SHA-256. Checksums detect transfer corruption, not
authenticity signatures. The released hook is the production hook, never the emulator timeout override.

**Технічна примітка щодо ACTION.txt / ACTION.txt note:** `ACTION.txt` has a single action word, no whitespace, ASCII or
UTF-8 without BOM, LF line endings (одне слово дії, без пробілів, без BOM, перенос LF). The supplied file is already
correct; no conversion is needed before `CHECK`.

## Джерела / References

[M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash),
[GEM custom entry](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/esd/scripts/custom.sh),
[GEM menu](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/esd/Launcher-sda0.esd),
[tools/node routing](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/config/GLOBALS),
[language parameterization](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/apps/setlang).

This is an independent localization project. Firmware-derived resources retain their existing third-party provenance;
no Audi approval/signature is implied. / Незалежний проєкт; жодного схвалення Audi не передбачається.
