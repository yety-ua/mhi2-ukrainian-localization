#!/bin/sh
# M.I.B. V3.6+ "Run individual script" runs /mod/command.sh; hand over to custom.sh beside it.
case $0 in */*) SELF_DIR=${0%/*} ;; *) SELF_DIR=. ;; esac
if [ ! -f "$SELF_DIR/custom.sh" ]; then
    echo 'ERROR: custom.sh is missing next to command.sh in SD1/mod.'
    exit 1
fi
exec /bin/sh "$SELF_DIR/custom.sh"
