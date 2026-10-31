#!/bin/sh
# Standalone, exact-target M.I.B. SD installer. Never reboots or patches IFS.
set -u
PATH=/proc/boot:/bin:/usr/bin:/usr/sbin:/sbin:/mnt/app/media/gracenote/bin:/mnt/app/armle/bin:/mnt/app/armle/sbin:/mnt/app/armle/usr/bin:/mnt/app/armle/usr/sbin
LD_LIBRARY_PATH=/lib:/mnt/app/root/lib-target:/eso/lib:/mnt/app/usr/lib:/mnt/app/armle/lib:/mnt/app/armle/lib/dll:/mnt/app/armle/usr/lib
IPL_CONFIG_DIR=/etc/eso/production
export PATH LD_LIBRARY_PATH IPL_CONFIG_DIR
unset LD_PRELOAD
case $0 in */*) SCRIPT_DIR=${0%/*} ;; *) exit 1 ;; esac
PACKAGE=${SCRIPT_DIR%/*}
MIB=/net/mmx/fs/sda0
APP=/mnt/app
LSD=$APP/eso/hmi/lsd
STATE=$APP/root/uk-localization
BACKUP=$STATE/baseline
RECOVERY=$STATE/recovery
# RAM directory for the lock and the pending menu step. QNX /dev/shmem (often behind /tmp) holds only
# files, never folders, so everything here is a plain file; the first candidate that accepts one wins.
RUNTIME_DIRS="/tmp /dev/shmem /net/rcc/dev/shmem"
RUNTIME=
for RUNTIME_CANDIDATE in $RUNTIME_DIRS; do
    # { ...; } 2>/dev/null: a failed redirection of a special builtin (:) would end a POSIX ksh script.
    if [ -d "$RUNTIME_CANDIDATE" ] && { echo probe > "$RUNTIME_CANDIDATE/uk-localization.probe.$$"; } 2>/dev/null; then
        rm -f "$RUNTIME_CANDIDATE/uk-localization.probe.$$"
        RUNTIME=$RUNTIME_CANDIDATE
        break
    fi
done
[ -n "$RUNTIME" ] || RUNTIME=${RUNTIME_DIRS%% *}
LOCK=$RUNTIME/uk-localization.lock
READER_TMP=$RUNTIME/uk-localization.reader.$$
ARM=$RUNTIME/uk-localization.arm
SHA=$MIB/apps/sbin/sha1sum
AWK=$MIB/apps/sbin/awk
SED=$MIB/apps/sbin/sed
XXD=$MIB/apps/sbin/xxd
READER=$MIB/apps/sbin/dumb_persistence_reader
# M.I.B. V3.7+ no longer ships apps/sbin/awk and uses the unit's own awk from this PATH.
if [ ! -x "$AWK" ]; then
    OLD_IFS=$IFS
    IFS=:
    for FIND_DIR in $PATH; do
        # On the unit awk is a symlink to gawk; use the real file (it is copied into the recovery tools).
        if [ -f "$FIND_DIR/gawk" ] && [ ! -L "$FIND_DIR/gawk" ] && [ -x "$FIND_DIR/gawk" ]; then AWK=$FIND_DIR/gawk; break; fi
        if [ -f "$FIND_DIR/awk" ] && [ ! -L "$FIND_DIR/awk" ] && [ -x "$FIND_DIR/awk" ]; then AWK=$FIND_DIR/awk; break; fi
    done
    IFS=$OLD_IFS
fi
if [ -d "$PACKAGE/tools" ]; then
    SHA=$PACKAGE/tools/sha1sum
    AWK=$PACKAGE/tools/awk
    SED=$PACKAGE/tools/sed
    XXD=$PACKAGE/tools/xxd
    READER=$PACKAGE/tools/dumb_persistence_reader
fi
KEY=3221422086
KEY280=3221422085
MUTATING=0
MENU=0
KEEP_ARM=0
STATE_NEW=0
LOG=/dev/null

say() { echo "$*"; echo "$*" >> "$LOG"; }
# Progress goes to fd 3, so it reaches the screen even inside $( ... ), and into the log.
exec 3>&1
# Keep the caller's stdin on fd 4 (a failing redirection of exec would end the script, so test it first).
if cat /dev/null <&0 2>/dev/null; then exec 4<&0; else exec 4< /dev/null; fi
SECONDS=${SECONDS:-0}
progress() { echo "$*" >&3; echo "$*" >> "$LOG"; }
# tick MESSAGE: a status line with the elapsed seconds, on the screen and in the log.
tick() { say "[${SECONDS}s] $*"; }
# run_timed LABEL LIMIT OUTFILE COMMAND...: run COMMAND in the background (stdin /dev/null, output to
# OUTFILE), print a heartbeat every 5 s so the screen shows it is alive, and stop it after LIMIT seconds.
run_timed() {
    RT_LABEL=$1
    RT_LIMIT=$2
    RT_OUT=$3
    shift 3
    "$@" < /dev/null > "$RT_OUT" 2>&1 &
    RT_PID=$!
    RT_START=$SECONDS
    RT_LAST=$SECONDS
    while kill -0 "$RT_PID" 2>/dev/null; do
        sleep .2
        if [ $((SECONDS - RT_START)) -ge "$RT_LIMIT" ] && kill -0 "$RT_PID" 2>/dev/null; then
            kill "$RT_PID" 2>/dev/null
            progress "ERROR: $RT_LABEL did not finish within ${RT_LIMIT}s; it was stopped."
            return 1
        fi
        if [ $((SECONDS - RT_LAST)) -ge 5 ]; then
            RT_LAST=$SECONDS
            progress "  [${SECONDS}s] $RT_LABEL: still working..."
        fi
    done
    wait "$RT_PID"
}
die() {
    [ "$KEEP_ARM" = 1 ] || rm -f "$ARM"
    say "ERROR: $*"
    if [ "$STATE_NEW" = 1 ]; then
        STATE_NEW=0
        rm -rf "$STATE" 2>/dev/null
        say 'The unfinished package folder on the unit was removed; nothing else was changed.'
    fi
    if [ "$MUTATING" = 1 ]; then
        if [ -f "$READER_TMP.rb" ] && [ "$(cat "$READER_TMP.rb")" = done ]; then
            say 'ROLLED BACK: the unit is back to its original language files and datasets; nothing is installed.'
            exit 1
        fi
        case $ACTION in
            INSTALL|VOICE_INSTALL)
                if [ ! -e "$READER_TMP.rb" ]; then
                    { echo started > "$READER_TMP.rb"; } 2>/dev/null
                    say 'The install stopped part-way: rolling back to the saved originals. Do not press Back or remove the SD card...'
                    if rollback_install; then
                        { echo done > "$READER_TMP.rb"; } 2>/dev/null
                        MUTATING=0
                        say 'ROLLED BACK: the unit is back to its original language files and datasets; nothing is installed.'
                        say 'Fix the reason above and try again. Restarting the MMI is not required.'
                        exit 1
                    fi
                fi ;;
        esac
        say 'Changes may remain. Do not reboot. Run RESTORE (this GEM item three times) or use the recovery instructions.'
    fi
    exit 1
}
# GEM-only flow: run the same item three times (CHECK -> checklist -> action). The pending
# step lives in RAM, so a restart of the unit cancels it. ACTION.txt other than CHECK wins.
menu_step() {
    MENU_TARGET=$1
    MENU_STEP=0
    if [ -f "$ARM" ]; then
        ARM_ROW=$(cat "$ARM")
        set -- $ARM_ROW
        if [ "$#" -eq 2 ] && [ "$1" = "$MENU_TARGET" ]; then
            case $2 in 1|2) MENU_STEP=$2 ;; esac
        fi
    fi
    if [ "$MENU_STEP" = 2 ]; then
        say "Step 3 of 3 confirmed: running $MENU_TARGET now."
        ACTION=$MENU_TARGET
        PROBLEM=
        return 0
    fi
    MENU_NEXT=$((MENU_STEP + 1))
    echo "$MENU_TARGET $MENU_NEXT" > "$ARM" || die 'Cannot record the pending menu step'
    if [ -n "$PROBLEM" ]; then MENU_CODE=1; else MENU_CODE=0; fi
    say ''
    if [ "$MENU_STEP" = 0 ]; then
        if [ "$MENU_TARGET" = INSTALL ]; then
            say 'Nothing was changed. To INSTALL, run this same GEM item again (step 1 of 3 done).'
            say 'The next run only shows a checklist; the run after it installs.'
            say 'To cancel, do nothing: the pending step is forgotten when the MMI restarts.'
        elif [ -n "$PROBLEM" ]; then
            say 'To RESTORE the original files, run this same GEM item again (step 1 of 3 done).'
            say 'Do NOT reboot the unit before restoring.'
        else
            say 'Ukrainian is installed and verified; nothing needs to be done.'
            say 'To go back to the original language files, run this item again (step 1 of 3 done).'
        fi
    else
        say "CONFIRM (step 2 of 3) before $MENU_TARGET. Continue only if ALL of these are true:"
        say ' - stable external power is connected'
        say ' - recovery access (telnet or SSH from a laptop) was verified'
        say ' - a full M.I.B. backup was made and copied off the SD'
        say "Run this item ONE more time to $MENU_TARGET now."
        if [ -n "$PROBLEM" ]; then
            say 'Do NOT reboot the unit before restoring.'
        else
            say 'To cancel, restart the MMI.'
        fi
    fi
    [ -z "$PROBLEM" ] || say "ERROR: $PROBLEM"
    exit $MENU_CODE
}
file_sha1() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    HASH_ROW=$("$SHA" "$1" < /dev/null) || return 1
    set -- $HASH_ROW
    [ "$#" -ge 1 ] || return 1
    case $1 in *[!0-9a-fA-F]*|'') return 1 ;; esac
    [ "${#1}" -eq 40 ] || return 1
    echo "$1"
}
# run_timed_pipe LABEL LIMIT OUTFILE STDIN COMMAND...: like run_timed, but the command's output goes through a
# pipe (as M.I.B. and chefranov capture it) instead of a file redirection, which a command spawned on another
# node (on -f rcc) may not like; STDIN is "null" or "inherit". Partial output is kept for the log.
run_timed_pipe() {
    RT_LABEL=$1
    RT_LIMIT=$2
    RT_OUT=$3
    RT_STDIN=$4
    shift 4
    if [ "$RT_STDIN" = inherit ]; then
        { "$@" 2>&1 <&4 | cat > "$RT_OUT"; } &
    else
        { "$@" 2>&1 < /dev/null | cat > "$RT_OUT"; } &
    fi
    RT_PID=$!
    RT_START=$SECONDS
    RT_LAST=$SECONDS
    while kill -0 "$RT_PID" 2>/dev/null; do
        sleep .2
        if [ $((SECONDS - RT_START)) -ge "$RT_LIMIT" ] && kill -0 "$RT_PID" 2>/dev/null; then
            kill "$RT_PID" 2>/dev/null
            progress "  $RT_LABEL did not finish within ${RT_LIMIT}s (stdin $RT_STDIN); it was stopped."
            progress "  partial output: $(head -3 "$RT_OUT" 2>/dev/null | tr '\n' '|')"
            return 1
        fi
        if [ $((SECONDS - RT_LAST)) -ge 5 ]; then
            RT_LAST=$SECONDS
            progress "  [${SECONDS}s] $RT_LABEL: still working..."
        fi
    done
    wait "$RT_PID"
}
# sync_progress: `sync` can take a while on flash; show that it is alive and give up after a long time.
sync_progress() { run_timed "writing to flash (sync)" "${UK_SYNC_LIMIT:-300}" "$READER_TMP.sync" sync; }
# hash_progress FILE LABEL LIMIT: like file_sha1 for a big file, with a heartbeat; sets HASH_RESULT.
hash_progress() {
    [ -f "$1" ] && [ ! -L "$1" ] || return 1
    run_timed "$2" "$3" "$READER_TMP.hash" "$SHA" "$1" || return 1
    HASH_ROW=$(cat "$READER_TMP.hash")
    rm -f "$READER_TMP.hash"
    set -- $HASH_ROW
    [ "$#" -ge 1 ] || return 1
    case $1 in *[!0-9a-fA-F]*|'') return 1 ;; esac
    [ "${#1}" -eq 40 ] || return 1
    HASH_RESULT=$1
}
equal() {
    LEFT=$(file_sha1 "$1") || return 1
    RIGHT=$(file_sha1 "$2") || return 1
    [ "$LEFT" = "$RIGHT" ]
}
copy_checked() {
    [ ! -L "$2" ] && [ ! -d "$2" ] || die "Unsafe destination: $2"
    cp -p "$1" "$2" || die "Cannot copy $1"
    equal "$1" "$2" || die "Copy verification failed: $2"
}
# Flat folder copy by glob: a card written on macOS/Windows can carry a broken "." entry that makes `cp -R` fail on QNX
# ("Filename too long" for dir/...). Names starting with a dot (AppleDouble ._ files) are skipped by the glob on purpose.
copy_flat_dir() {
    mkdir "$2" || return 1
    for ITEM in "$1"/*; do
        [ -f "$ITEM" ] && [ ! -L "$ITEM" ] || return 1
        cp -p "$ITEM" "$2/" || return 1
    done
}
activate() {
    tick "  writing ${2##*/}"
    [ ! -L "$2" ] && [ ! -d "$2" ] || die "Unsafe destination: $2"
    copy_checked "$1" "$2.uk-new"
    mv "$2.uk-new" "$2" || die "Cannot activate $2"
    equal "$1" "$2" || die "Active file verification failed: $2"
}
blob() {
    run_timed "persistence read $1" "${UK_PROBE_LIMIT:-60}" "$READER_TMP" "$READER" 0 "$1" || die "Cannot read persistence key $1"
    "$AWK" -v bytes="$2" -f "$PACKAGE/scripts/blob.awk" "$READER_TMP" || die "Ambiguous or invalid CRC for key $1"
}
write_blob() {
    VALUE=$(cat "$2") || die "Cannot read $2"
    tick "Writing persistence dataset $1 ($3 bytes)..."
    run_timed "persistence write $1" "${UK_WRITE_LIMIT:-300}" "$READER_TMP.wr" /eso/bin/dumb_persistence_writer -f -P 0 "$1" "$VALUE" || die "Persistence write failed: $1"
    cat "$READER_TMP.wr" >> "$LOG" 2>/dev/null
    sync_progress || die 'Sync failed'
    tick "Reading dataset $1 back to verify it..."
    READBACK=$(blob "$1" "$3") || die "Read-back failed: $1"
    [ "$READBACK" = "$VALUE" ] || die "Persistence read-back differs: $1"
}
verify_manifest() {
    COUNT=0
    SEEN='|'
    while read -r EXPECTED REL; do
        case $REL in
            payload/lang_data.zip|payload/lang_uk_hook.jar|payload/lang_uk_voice.jar|payload/lang_hmi_builtin.config|payload/1100076.png|stock/lang_data.zip|stock/lang_hmi_builtin.config|stock/language_lut_hmi.txt|stock/1100066.png|scripts/localization.sh|scripts/blob.awk|target/2d00.original.hex|target/2d00.uk.hex|target/280.original.hex|HMI.sha1) ;;
            *) die 'Invalid manifest path' ;;
        esac
        case $SEEN in *"|$REL|"*) die 'Duplicate manifest path' ;; esac
        SEEN=$SEEN$REL'|'
        COUNT=$((COUNT + 1))
        ACTUAL=$(file_sha1 "$PACKAGE/$REL") || die "Missing/unreadable package file: $REL"
        [ "$ACTUAL" = "$EXPECTED" ] || die "Package checksum mismatch: $REL"
        say "  [${SECONDS}s] ok $REL"
    done < "$PACKAGE/SHA1SUMS"
    [ "$COUNT" -eq 15 ] || die 'Incomplete package manifest'
}
verify_stock() {
    equal "$LSD/jars/lang_data.zip" "$PACKAGE/stock/lang_data.zip" || die 'Language ZIP is not the reviewed stock baseline'
    equal "$LSD/lang_hmi_builtin.config" "$PACKAGE/stock/lang_hmi_builtin.config" || die 'Builtin config is not stock'
    equal "$LSD/language_lut_hmi.txt" "$PACKAGE/stock/language_lut_hmi.txt" || die 'Language LUT is not stock'
    equal "$LSD/images/HMISettingsEvoHigh/1100066.png" "$PACKAGE/stock/1100066.png" || die 'Flag 1100066.png is not the reviewed stock file'
}
verify_ui() {
    equal "$LSD/jars/lang_data.zip" "$PACKAGE/payload/lang_data.zip" || die 'Installed language ZIP differs'
    equal "$LSD/jars/lang_uk_hook.jar" "$PACKAGE/payload/lang_uk_hook.jar" || die 'Installed UI hook differs'
    equal "$LSD/lang_hmi_builtin.config" "$PACKAGE/payload/lang_hmi_builtin.config" || die 'Installed builtin config differs'
    equal "$LSD/images/HMISettingsEvoHigh/1100076.png" "$PACKAGE/payload/1100076.png" || die 'Installed flag differs'
    equal "$LSD/images/HMISettingsEvoHigh/1100066.png" "$PACKAGE/payload/1100076.png" || die 'Installed settings-row flag differs'
    equal "$LSD/language_lut_hmi.txt" "$PACKAGE/stock/language_lut_hmi.txt" || die 'Language LUT differs'
    [ "$CURRENT" = "$TARGET" ] || die 'Installed visible-language dataset differs'
}
verify_backup() {
    [ -f "$BACKUP/COMPLETE" ] || die 'No complete package baseline; installation is refused'
    MARKER=$(cat "$BACKUP/COMPLETE") || die 'Cannot read baseline marker'
    [ "$MARKER" = STOCK_AND_ABSENT_HOOKS ] || die 'Unknown baseline marker'
    for FILE in lang_data.zip lang_hmi_builtin.config language_lut_hmi.txt; do
        equal "$BACKUP/$FILE" "$PACKAGE/stock/$FILE" || die "Baseline damaged: $FILE"
    done
    # A baseline made by an older package has no copy of the flag; INSTALL adds it after verifying the live file.
    if [ -e "$BACKUP/1100066.png" ]; then
        equal "$BACKUP/1100066.png" "$PACKAGE/stock/1100066.png" || die 'Baseline damaged: 1100066.png'
    fi
    equal "$BACKUP/2d00.hex" "$PACKAGE/target/2d00.original.hex" || die 'Dataset baseline damaged'
    equal "$BACKUP/280.hex" "$PACKAGE/target/280.original.hex" || die 'Default-language baseline damaged'
}
require_space() {
    # QNX `df -k` prints NO header line (the unit: "/dev/mnand0t177 995280 716943 278337 73% /mnt/app/"), and a
    # long device name may wrap. So take the first run of three plain numbers (blocks, used, available).
    AVAIL=$(df -k "$APP" < /dev/null | "$AWK" '
        { for (i = 1; i <= NF; i++) tok[++n] = $i }
        END {
            for (i = 1; i <= n - 2; i++)
                if (tok[i] ~ /^[0-9]+$/ && tok[i+1] ~ /^[0-9]+$/ && tok[i+2] ~ /^[0-9]+$/) { print tok[i+2]; exit }
            exit 1
        }') || die 'Cannot read free space (unrecognized df output)'
    case $AVAIL in ''|*[!0-9]*) die 'Unrecognized available space' ;; esac
    [ "$AVAIL" -ge 40000 ] || die "At least 40000 KiB free in /mnt/app is required (available: $AVAIL)"
}
# restore_baseline: put the saved originals back (the body of RESTORE, also used by the automatic rollback).
restore_baseline() {
    # Baseline requires these hooks/flag to have been absent before install.
    # Also covers a corrupt or half-written managed hook after interruption.
    for FILE in "$LSD/jars/lang_uk_voice.jar" "$LSD/jars/lang_uk_hook.jar" "$LSD/images/HMISettingsEvoHigh/1100076.png"; do
        [ ! -L "$FILE" ] && [ ! -d "$FILE" ] || die "Unsafe restore destination: $FILE"
        rm -f "$FILE" "$FILE.uk-new" || die "Cannot restore original absence: $FILE"
    done
    activate "$BACKUP/lang_data.zip" "$LSD/jars/lang_data.zip"
    activate "$BACKUP/lang_hmi_builtin.config" "$LSD/lang_hmi_builtin.config"
    activate "$BACKUP/language_lut_hmi.txt" "$LSD/language_lut_hmi.txt"
    # A baseline made by an older package has no copy of this file; the live one was not touched then (verified below).
    if [ -f "$BACKUP/1100066.png" ]; then activate "$BACKUP/1100066.png" "$LSD/images/HMISettingsEvoHigh/1100066.png"; fi
    write_blob "$KEY" "$BACKUP/2d00.hex" 389
    write_blob "$KEY280" "$BACKUP/280.hex" 22
    tick "Verifying the restored originals..."
    verify_stock
    rm -f "$STATE/INSTALLED" || die 'Cannot clear installation marker'
    echo 'RESTORED' > "$STATE/RESTORED" || die 'Cannot record restoration'
}
# rollback_install: undo a failed INSTALL / VOICE_INSTALL; returns 0 when the unit is back to the originals.
rollback_install() {
    case $ACTION in
        INSTALL) restore_baseline ;;
        VOICE_INSTALL) rm -f "$LSD/jars/lang_uk_voice.jar" "$LSD/jars/lang_uk_voice.jar.uk-new" || return 1 ;;
    esac
    rm -f "$STATE/PENDING" || return 1
    sync_progress || return 1
    return 0
}
prepare_backup() {
    [ ! -e "$STATE" ] || die 'Existing package state: use CHECK or RESTORE; do not overwrite it'
    mkdir -p "$BACKUP" "$RECOVERY" || die 'Cannot create recovery directories'
    STATE_NEW=1
    tick "Saving the original language files and datasets on the unit..."
    # Store the reviewed originals from the live unit, not just supplied copies.
    for FILE in lang_data.zip lang_hmi_builtin.config language_lut_hmi.txt 1100066.png; do
        case $FILE in lang_data.zip) SOURCE=$LSD/jars/$FILE ;; 1100066.png) SOURCE=$LSD/images/HMISettingsEvoHigh/$FILE ;; *) SOURCE=$LSD/$FILE ;; esac
        copy_checked "$SOURCE" "$BACKUP/$FILE"
    done
    echo "$CURRENT" > "$BACKUP/2d00.hex" || die 'Cannot save visible languages'
    echo "$CURRENT280" > "$BACKUP/280.hex" || die 'Cannot save default languages'
    tick "Staging the internal recovery copy (works without the SD card)..."
    for DIR in scripts payload stock target; do
        copy_flat_dir "$PACKAGE/$DIR" "$RECOVERY/$DIR" || die 'Cannot stage internal recovery package'
    done
    copy_checked "$PACKAGE/SHA1SUMS" "$RECOVERY/SHA1SUMS"
    copy_checked "$PACKAGE/HMI.sha1" "$RECOVERY/HMI.sha1"
    mkdir "$RECOVERY/tools" || die 'Cannot create recovery tools directory'
    for TOOL_NAME in sha1sum awk sed xxd dumb_persistence_reader; do
        case $TOOL_NAME in
            sha1sum) TOOL=$SHA ;;
            awk) TOOL=$AWK ;;
            sed) TOOL=$SED ;;
            xxd) TOOL=$XXD ;;
            *) TOOL=$READER ;;
        esac
        copy_checked "$TOOL" "$RECOVERY/tools/$TOOL_NAME"
    done
    echo 'CHECK' > "$RECOVERY/ACTION.txt" || die 'Cannot stage recovery action'
    mkdir "$RECOVERY/logs" || die 'Cannot create recovery log directory'
    tick "Verifying the recovery copy..."
    ORIGINAL_PACKAGE=$PACKAGE
    PACKAGE=$RECOVERY
    verify_manifest
    PACKAGE=$ORIGINAL_PACKAGE
    echo 'STOCK_AND_ABSENT_HOOKS' > "$BACKUP/COMPLETE" || die 'Cannot seal baseline'
    sync_progress || die 'Cannot sync baseline'
    verify_backup
    tick "Saving a second copy of the originals on the SD card..."
    # Off-device originals remain available on SD1 as well.
    [ ! -L "$PACKAGE/backups" ] || die 'Unsafe SD backup directory'
    mkdir -p "$PACKAGE/backups" || die 'Cannot create SD baseline folder'
    SD_BACKUP=$PACKAGE/backups/baseline-${LOG##*/}
    mkdir "$SD_BACKUP" || die 'Cannot create a fresh SD baseline'
    for FILE in lang_data.zip lang_hmi_builtin.config language_lut_hmi.txt 1100066.png 2d00.hex 280.hex COMPLETE; do
        copy_checked "$BACKUP/$FILE" "$SD_BACKUP/$FILE"
    done
    sync_progress || die 'Cannot sync SD baseline'
    tick "Backups are complete."
    STATE_NEW=0
}

# No source of M.I.B. GLOBALS: it has unrelated write/side effects.
for TOOL in "$SHA" "$AWK" "$SED" "$XXD" "$READER"; do
    [ -x "$TOOL" ] || { echo "ERROR: Required M.I.B. tool is missing: $TOOL"; exit 1; }
    if [ -L "$TOOL" ] || [ ! -f "$TOOL" ]; then echo "ERROR: Required tool is not a regular file: $TOOL"; exit 1; fi
done
[ -x /eso/bin/dumb_persistence_writer ] || { echo 'ERROR: Persistence writer is missing.'; exit 1; }
# The SD is mounted read-only by default; logs, ACTION.txt and the SD baseline need it writable.
mount -uw "$MIB" 2>/dev/null
# The internal recovery copy logs under /mnt/app, which is read-only until remounted.
case $PACKAGE in
    "$APP"/*) [ "${1:-}" = CHECK ] || mount -uw "$APP" 2>/dev/null ;;
esac
[ ! -L "$PACKAGE/logs" ] || exit 1
# A log on the SD is a convenience, not a requirement: if the card cannot be written, log in RAM and go on.
LOG=
if mkdir -p "$PACKAGE/logs" 2>/dev/null; then
    LOG_CANDIDATE=$PACKAGE/logs/run-$$.log
    INDEX=0
    while [ -e "$LOG_CANDIDATE" ] || [ -L "$LOG_CANDIDATE" ]; do
        INDEX=$((INDEX + 1))
        LOG_CANDIDATE=$PACKAGE/logs/run-$$-$INDEX.log
    done
    if { cat /dev/null > "$LOG_CANDIDATE"; } 2>/dev/null; then LOG=$LOG_CANDIDATE; fi
fi
if [ -z "$LOG" ]; then
    LOG=$RUNTIME/uk-localization.log
    { cat /dev/null > "$LOG"; } 2>/dev/null || LOG=/dev/null
    say "WARNING: the SD card cannot be written; logging to $LOG (lost at reboot)."
fi
# The lock is a file holding its owner's PID, created atomically (noclobber). A lock whose owner is
# gone (killed run) is stale and is replaced.
make_lock() { ( set -C; echo $$ > "$LOCK" ) 2>/dev/null; }
if ! make_lock; then
    LOCK_OWNER=$(cat "$LOCK" 2>/dev/null)
    case $LOCK_OWNER in
        ''|*[!0-9]*) LOCK_OWNER= ;;
    esac
    if [ -n "$LOCK_OWNER" ] && kill -0 "$LOCK_OWNER" 2>/dev/null; then
        say "ERROR: Another localization operation is running (process $LOCK_OWNER)"
        exit 1
    fi
    rm -rf "$LOCK" 2>/dev/null
    if ! make_lock; then
        say "ERROR: Cannot create the lock file $LOCK"
        say "Diagnostics: user=$(id 2>&1); $(ls -ld "$RUNTIME" "$LOCK" 2>&1)"
        exit 1
    fi
    say 'Replaced a stale lock left by an interrupted run.'
fi
trap 'rm -f "$LOCK" "$READER_TMP" "$READER_TMP.hash" "$READER_TMP.wr" "$READER_TMP.sync" "$READER_TMP.rb"' 0
trap 'exit 1' 1 2 15

if [ "$#" -eq 1 ]; then
    ACTION=$1
else
    ACTION=$(cat "$PACKAGE/ACTION.txt") || die 'Missing ACTION.txt'
    [ "$ACTION" != CHECK ] || MENU=1
fi
case $ACTION in CHECK|INSTALL|RESTORE|VOICE_INSTALL|VOICE_RESTORE) ;; *) die 'Invalid action; use CHECK, INSTALL, RESTORE, VOICE_INSTALL or VOICE_RESTORE' ;; esac
say "Ukrainian localization 1.0 / action=$ACTION"
say "[${SECONDS}s] Checking the package files (15)..."
verify_manifest
EXPECTED_HMI=$(cat "$PACKAGE/HMI.sha1") || die 'Missing HMI fingerprint'
say "[${SECONDS}s] Fingerprinting the HMI image (about 58 MB, this can take a minute)..."
hash_progress /ifs/lsd.jxe 'HMI fingerprint' "${UK_HASH_LIMIT:-600}" || die 'Cannot fingerprint live HMI'
ACTUAL_HMI=$HASH_RESULT
say "[${SECONDS}s] HMI image hashed."
[ "$ACTUAL_HMI" = "$EXPECTED_HMI" ] || die 'HMI is not the exact reviewed K3346/MU1438 binary'
# Same EEPROM offsets as upstream GLOBALS; require exactly the requested bytes.
read_eeprom() {
    EEPROM_VALUE=
    for EEPROM_STDIN in null inherit; do
        if [ "$EEPROM_STDIN" = inherit ]; then cat /dev/null <&4 2>/dev/null || continue; fi
        run_timed_pipe "EEPROM read $1" "${UK_PROBE_LIMIT:-20}" "$READER_TMP" "$EEPROM_STDIN" on -f rcc /net/rcc/usr/apps/modifyE2P r "$1" "$2" || continue
        EEPROM_VALUE=$("$AWK" -v expected="$2" '
            $1 ~ /^0x[0-9a-fA-F]+:?$/ {
                for (i=2;i<=NF;i++) {
                    if ($i ~ /[^0-9a-fA-F]/ || length($i) % 2) break
                    out=out $i
                }
            }
            END { if (length(out) != expected * 2) exit 1; print out }
        ' "$READER_TMP" | "$XXD" -r -p | "$SED" 's/[^a-zA-Z0-9_-]//g')
        [ -z "$EEPROM_VALUE" ] || return 0
        progress "  EEPROM output not understood: $(head -3 "$READER_TMP" 2>/dev/null | tr '\n' '|')"
    done
    return 1
}
# Firmware identity. The exact HMI fingerprint above already pins the reviewed K3346/MU1438 build; the train
# and MU are a second opinion. Read them from the text files software updates leave on rcc, then from the
# EEPROM. A readable value that differs stops everything; an unreadable one is only a warning.
TRAIN=
MU=
for IDENT_FILE in /net/rcc/mnt/efs-persist/SWDL/CachedTrain.txt /mnt/efs-persist/SWDL/CachedTrain.txt; do
    if [ -f "$IDENT_FILE" ]; then read -r TRAIN < "$IDENT_FILE"; break; fi
done
for IDENT_FILE in /net/rcc/mnt/efs-persist/SWDL/CachedMuVersion.txt /mnt/efs-persist/SWDL/CachedMuVersion.txt; do
    if [ -f "$IDENT_FILE" ]; then read -r MU < "$IDENT_FILE"; break; fi
done
if [ -z "$TRAIN" ] || [ -z "$MU" ]; then
    say "[${SECONDS}s] Reading the firmware identity from the EEPROM..."
    if read_eeprom 3A0 19; then
        [ -n "$TRAIN" ] || TRAIN=$EEPROM_VALUE
        read_eeprom 3B9 4 && { [ -n "$MU" ] || MU=$EEPROM_VALUE; }
    fi
fi
case $TRAIN in
    MHI2_ER_AUG22_K3346*) ;;
    '') ;;
    *) die "Wrong firmware train: $TRAIN" ;;
esac
case $MU in
    1438*|MU1438*) ;;
    '') ;;
    *) die "Wrong firmware MU version: $MU" ;;
esac
if [ -n "$TRAIN" ] && [ -n "$MU" ]; then
    say "[${SECONDS}s] Verified identity: $TRAIN / MU1438 / exact HMI fingerprint"
else
    say "[${SECONDS}s] WARNING: the firmware train/MU could not be read (train='${TRAIN:-?}', MU='${MU:-?}')."
    say "          Identity rests on the exact HMI fingerprint, the stock language files and the datasets."
fi
for BUSY in backup.mib reboot.mib flash.mib; do
    [ ! -f "/net/rcc/dev/shmem/$BUSY" ] || die 'M.I.B. backup/reboot/flash is running'
done
[ -d "$LSD/images/HMISettingsEvoHigh" ] || die 'EvoHigh flag directory missing'
[ ! -L "$STATE" ] && [ ! -L "$BACKUP" ] && [ ! -L "$RECOVERY" ] || die 'Unsafe state directory'
say "[${SECONDS}s] Reading the language datasets..."
CURRENT=$(blob "$KEY" 389) || {
    [ "$ACTION" = RESTORE ] || die 'Cannot read visible-language dataset'
    CURRENT=UNREADABLE
    say 'RESTORE will recover the trusted baseline despite unreadable current visible languages.'
}
CURRENT280=$(blob "$KEY280" 22) || {
    [ "$ACTION" = RESTORE ] || die 'Cannot read default-language dataset'
    CURRENT280=UNREADABLE
    say 'RESTORE will recover the trusted baseline despite unreadable current defaults.'
}
ORIGINAL=$(cat "$PACKAGE/target/2d00.original.hex") || die 'Missing original dataset'
TARGET=$(cat "$PACKAGE/target/2d00.uk.hex") || die 'Missing target dataset'
ORIGINAL280=$(cat "$PACKAGE/target/280.original.hex") || die 'Missing original defaults'
say "[${SECONDS}s] Persistence values read and CRC-checked."

if [ "$ACTION" = CHECK ]; then
    require_space
    OFFER=
    PROBLEM=
    if [ -e "$STATE" ]; then
        verify_backup
        if [ -f "$STATE/PENDING" ]; then
            PROBLEM='Interrupted operation recorded; run RESTORE before rebooting'
            OFFER=RESTORE
        elif [ -f "$STATE/INSTALLED" ]; then
            KEEP_ARM=1
            if ( verify_ui ); then
                if [ -f "$LSD/jars/lang_uk_voice.jar" ]; then
                    equal "$LSD/jars/lang_uk_voice.jar" "$PACKAGE/payload/lang_uk_voice.jar" || die 'Unknown voice hook'
                    say 'English voice fallback is installed; actual speech needs vehicle validation.'
                fi
                say 'CHECK PASS: Ukrainian UI installation matches this package.'
            else
                PROBLEM='Installed files differ from this package; the original baseline can be restored'
            fi
            KEEP_ARM=0
            OFFER=RESTORE
        elif [ -f "$STATE/RESTORED" ]; then
            verify_stock
            [ "$CURRENT" = "$ORIGINAL" ] && [ "$CURRENT280" = "$ORIGINAL280" ] || die 'Restored datasets differ'
            say 'CHECK PASS: stock baseline restored; package can be installed again.'
            OFFER=INSTALL
        else die 'Unfinished package state exists; inspect the recovery log'; fi
    else
        verify_stock
        [ "$CURRENT" = "$ORIGINAL" ] && [ "$CURRENT280" = "$ORIGINAL280" ] || die 'Datasets differ from reviewed originals'
        for FILE in "$LSD/jars/lang_uk_hook.jar" "$LSD/jars/lang_uk_voice.jar" "$LSD/images/HMISettingsEvoHigh/1100076.png"; do
            [ ! -e "$FILE" ] && [ ! -L "$FILE" ] || die "Existing unmanaged localization file: $FILE"
        done
        say 'CHECK PASS: exact stock baseline, valid package, tools and free space.'
        OFFER=INSTALL
    fi
    if [ "$MENU" = 1 ] && [ -n "$OFFER" ]; then menu_step "$OFFER"; fi
    [ -z "$PROBLEM" ] || die "$PROBLEM"
    if [ "$ACTION" = CHECK ]; then
        say 'CHECK performs no remount, firmware file write, persistence write or reboot.'
        exit 0
    fi
fi

# One-shot action: reset ACTION.txt to CHECK before writing; menu steps are forgotten.
rm -f "$ARM"
echo CHECK > "$PACKAGE/ACTION.txt.new" || die 'Cannot reset action on SD'
mv "$PACKAGE/ACTION.txt.new" "$PACKAGE/ACTION.txt" || die 'Cannot reset action'
if [ "$ACTION" = INSTALL ]; then
    require_space
    verify_stock
    [ "$CURRENT" = "$ORIGINAL" ] && [ "$CURRENT280" = "$ORIGINAL280" ] || die 'Datasets are not the reviewed originals'
    for FILE in "$LSD/jars/lang_uk_hook.jar" "$LSD/jars/lang_uk_voice.jar" "$LSD/images/HMISettingsEvoHigh/1100076.png"; do
        [ ! -e "$FILE" ] && [ ! -L "$FILE" ] || die "Existing unmanaged file: $FILE"
    done
    if [ -e "$STATE" ]; then
        [ -f "$STATE/RESTORED" ] && [ ! -f "$STATE/PENDING" ] || die 'Package state already exists; use CHECK or RESTORE'
        verify_backup
    fi
else
    verify_backup
    if [ "$ACTION" != RESTORE ]; then
        [ -f "$STATE/INSTALLED" ] && [ ! -f "$STATE/PENDING" ] || die 'UI must be successfully installed first'
        verify_ui
    fi
fi
if [ "$ACTION" = VOICE_INSTALL ]; then
    require_space
    [ ! -e "$LSD/jars/lang_uk_voice.jar" ] && [ ! -L "$LSD/jars/lang_uk_voice.jar" ] || die 'Voice hook already exists'
elif [ "$ACTION" = VOICE_RESTORE ]; then
    equal "$LSD/jars/lang_uk_voice.jar" "$PACKAGE/payload/lang_uk_voice.jar" || die 'Voice hook differs or is absent'
fi
tick "Remounting /mnt/app read-write..."
mount -uw "$APP" || die 'Cannot remount /mnt/app read-write'
if [ "$ACTION" = INSTALL ]; then
    if [ ! -e "$STATE" ]; then
        prepare_backup
    elif [ ! -f "$BACKUP/1100066.png" ]; then
        # Baseline from an older package (/mnt/app is writable only now): the unit's flag was verified as stock above.
        copy_checked "$LSD/images/HMISettingsEvoHigh/1100066.png" "$BACKUP/1100066.png"
        verify_backup
    fi
    RECHECK=$(blob "$KEY" 389) || die 'Cannot recheck visible languages'
    RECHECK280=$(blob "$KEY280" 22) || die 'Cannot recheck default languages'
    [ "$RECHECK" = "$CURRENT" ] && [ "$RECHECK280" = "$CURRENT280" ] || die 'Datasets changed during preparation'
fi
echo "$ACTION" > "$STATE/PENDING" || die 'Cannot journal operation'
sync_progress || die 'Cannot sync journal'
MUTATING=1
tick "Starting $ACTION. Do not press Back or remove the SD card; a line appears at least every 5 seconds."
case $ACTION in
    INSTALL)
        activate "$PACKAGE/payload/1100076.png" "$LSD/images/HMISettingsEvoHigh/1100076.png"
        activate "$PACKAGE/payload/1100076.png" "$LSD/images/HMISettingsEvoHigh/1100066.png"
        activate "$PACKAGE/payload/lang_hmi_builtin.config" "$LSD/lang_hmi_builtin.config"
        activate "$PACKAGE/payload/lang_data.zip" "$LSD/jars/lang_data.zip"
        activate "$PACKAGE/payload/lang_uk_hook.jar" "$LSD/jars/lang_uk_hook.jar"
        sync_progress || die 'Cannot sync resources'
        tick "Resource files are in place; now the language list dataset (written last)."
        write_blob "$KEY" "$PACKAGE/target/2d00.uk.hex" 389
        tick "Verifying the installed files..."
        CURRENT=$(blob "$KEY" 389) || die 'Cannot verify dataset'
        verify_ui
        echo 'UI' > "$STATE/INSTALLED" || die 'Cannot record installation'
        rm -f "$STATE/RESTORED" || die 'Cannot clear restoration marker'
        ;;
    VOICE_INSTALL)
        activate "$PACKAGE/payload/lang_uk_voice.jar" "$LSD/jars/lang_uk_voice.jar"
        ;;
    VOICE_RESTORE)
        rm "$LSD/jars/lang_uk_voice.jar" || die 'Cannot remove managed voice hook'
        ;;
    RESTORE)
        restore_baseline
        ;;
esac
sync_progress || die 'Final sync failed'
rm "$STATE/PENDING" || die 'Cannot clear pending journal'
sync_progress || die 'Journal sync failed'
MUTATING=0
say "SUCCESS: $ACTION completed and file/dataset read-back verified. No automatic reboot."
say 'Vehicle UI, persistence after cold boot, speech and Virtual Cockpit remain to be tested.'
case $ACTION in
    INSTALL) say "NEXT: restart the MMI yourself (ignition off, wait until it is fully off, ignition on), then choose Ukrainian in Settings > Language." ;;
    RESTORE) say "NEXT: restart the MMI yourself (ignition off, wait until it is fully off, ignition on)." ;;
esac
# Like M.I.B., hand /mnt/app back read-only once everything (including the log) is written.
mount -ur "$APP" 2>/dev/null
