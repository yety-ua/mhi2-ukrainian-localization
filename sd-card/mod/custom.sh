#!/bin/sh
# M.I.B. GEM entry point. Copy to SD1/mod/custom.sh; keep LF line endings.
PACKAGE=/net/mmx/fs/sda0/uk-localization
if [ ! -f "$PACKAGE/scripts/localization.sh" ]; then
    echo 'ERROR: uk-localization package is missing from SD1.'
    exit 1
fi
# Keep shell errors (e.g. a parse error before the installer opens its own log) on the card.
ERRLOG=$PACKAGE/logs/launcher-errors.txt
if mkdir -p "$PACKAGE/logs" 2>/dev/null && : > "$ERRLOG" 2>/dev/null; then
    on -f mmx /bin/sh "$PACKAGE/scripts/localization.sh" 2> "$ERRLOG"
    result=$?
    if [ -s "$ERRLOG" ]; then
        echo '--- shell errors (also saved in uk-localization/logs/launcher-errors.txt) ---'
        cat "$ERRLOG"
    fi
else
    on -f mmx /bin/sh "$PACKAGE/scripts/localization.sh"
    result=$?
fi
echo "Ukrainian localization exit code: $result (0 means verified success)."
echo 'Read the localization log. Do not rely on the outer M.I.B. finished message.'
exit "$result"
