#!/bin/sh
# M.I.B. GEM entry point. Copy to SD1/mod/custom.sh; keep LF line endings.
# The package lives next to this file: SD1/mod/uk-localization (M.I.B. runs us as /net/mmx/fs/sda0/mod/custom.sh).
case $0 in
    */*) SELF_DIR=${0%/*} ;;
    *) SELF_DIR=/net/mmx/fs/sda0/mod ;;
esac
PACKAGE=$SELF_DIR/uk-localization
if [ ! -f "$PACKAGE/scripts/localization.sh" ]; then
    echo 'ERROR: the uk-localization folder is missing from SD1/mod.'
    exit 1
fi
# The SD is mounted read-only by default; the log folder and ACTION.txt need it writable.
mount -uw /net/mmx/fs/sda0 2>/dev/null
# Keep shell errors (e.g. a parse error before the installer opens its own log) on the card.
ERRLOG=$PACKAGE/logs/launcher-errors.txt
if mkdir -p "$PACKAGE/logs" 2>/dev/null && { cat /dev/null > "$ERRLOG"; } 2>/dev/null; then
    on -f mmx /bin/sh "$PACKAGE/scripts/localization.sh" 2> "$ERRLOG"
    result=$?
    if [ -s "$ERRLOG" ]; then
        echo '--- shell errors (also saved in mod/uk-localization/logs/launcher-errors.txt) ---'
        cat "$ERRLOG"
    fi
else
    on -f mmx /bin/sh "$PACKAGE/scripts/localization.sh"
    result=$?
fi
echo "Ukrainian localization exit code: $result (0 means verified success)."
echo 'Read the localization log. Do not rely on the outer M.I.B. finished message.'
exit "$result"
