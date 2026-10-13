#!/bin/sh
# M.I.B. GEM entry point. Copy to SD1/mod/custom.sh; keep LF line endings.
PACKAGE=/net/mmx/fs/sda0/uk-localization
if [ ! -f "$PACKAGE/scripts/localization.sh" ]; then
    echo 'ERROR: uk-localization package is missing from SD1.'
    exit 1
fi
on -f mmx /bin/sh "$PACKAGE/scripts/localization.sh"
result=$?
echo "Ukrainian localization exit code: $result (0 means verified success)."
echo 'Read the localization log. Do not rely on the outer M.I.B. finished message.'
exit "$result"
