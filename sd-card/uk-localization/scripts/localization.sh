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
        if [ -f "$FIND_DIR/awk" ] && [ -x "$FIND_DIR/awk" ]; then AWK=$FIND_DIR/awk; break; fi
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
LOG=/dev/null

say() { echo "$*"; echo "$*" >> "$LOG"; }
die() {
    [ "$KEEP_ARM" = 1 ] || rm -f "$ARM"
    say "ERROR: $*"
    if [ "$MUTATING" = 1 ]; then
        say 'Changes may remain. Do not reboot. Run RESTORE or use the recovery instructions.'
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
    HASH_ROW=$("$SHA" "$1") || return 1
    set -- $HASH_ROW
    [ "$#" -ge 1 ] || return 1
    case $1 in *[!0-9a-fA-F]*|'') return 1 ;; esac
    [ "${#1}" -eq 40 ] || return 1
    echo "$1"
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
activate() {
    [ ! -L "$2" ] && [ ! -d "$2" ] || die "Unsafe destination: $2"
    copy_checked "$1" "$2.uk-new"
    mv "$2.uk-new" "$2" || die "Cannot activate $2"
    equal "$1" "$2" || die "Active file verification failed: $2"
}
blob() {
    "$READER" 0 "$1" > "$READER_TMP" 2>&1 || die "Cannot read persistence key $1"
    "$AWK" -v bytes="$2" -f "$PACKAGE/scripts/blob.awk" "$READER_TMP" || die "Ambiguous or invalid CRC for key $1"
}
write_blob() {
    VALUE=$(cat "$2") || die "Cannot read $2"
    /eso/bin/dumb_persistence_writer -f -P 0 "$1" "$VALUE" >> "$LOG" 2>&1 || die "Persistence write failed: $1"
    sync || die 'Sync failed'
    READBACK=$(blob "$1" "$3") || die "Read-back failed: $1"
    [ "$READBACK" = "$VALUE" ] || die "Persistence read-back differs: $1"
}
verify_manifest() {
    COUNT=0
    SEEN='|'
    while read -r EXPECTED REL; do
        case $REL in
            payload/lang_data.zip|payload/lang_uk_hook.jar|payload/lang_uk_voice.jar|payload/lang_hmi_builtin.config|payload/1100076.png|stock/lang_data.zip|stock/lang_hmi_builtin.config|stock/language_lut_hmi.txt|scripts/localization.sh|scripts/blob.awk|target/2d00.original.hex|target/2d00.uk.hex|target/280.original.hex|HMI.sha1) ;;
            *) die 'Invalid manifest path' ;;
        esac
        case $SEEN in *"|$REL|"*) die 'Duplicate manifest path' ;; esac
        SEEN=$SEEN$REL'|'
        COUNT=$((COUNT + 1))
        ACTUAL=$(file_sha1 "$PACKAGE/$REL") || die "Missing/unreadable package file: $REL"
        [ "$ACTUAL" = "$EXPECTED" ] || die "Package checksum mismatch: $REL"
    done < "$PACKAGE/SHA1SUMS"
    [ "$COUNT" -eq 14 ] || die 'Incomplete package manifest'
}
verify_stock() {
    equal "$LSD/jars/lang_data.zip" "$PACKAGE/stock/lang_data.zip" || die 'Language ZIP is not the reviewed stock baseline'
    equal "$LSD/lang_hmi_builtin.config" "$PACKAGE/stock/lang_hmi_builtin.config" || die 'Builtin config is not stock'
    equal "$LSD/language_lut_hmi.txt" "$PACKAGE/stock/language_lut_hmi.txt" || die 'Language LUT is not stock'
}
verify_ui() {
    equal "$LSD/jars/lang_data.zip" "$PACKAGE/payload/lang_data.zip" || die 'Installed language ZIP differs'
    equal "$LSD/jars/lang_uk_hook.jar" "$PACKAGE/payload/lang_uk_hook.jar" || die 'Installed UI hook differs'
    equal "$LSD/lang_hmi_builtin.config" "$PACKAGE/payload/lang_hmi_builtin.config" || die 'Installed builtin config differs'
    equal "$LSD/images/HMISettingsEvoHigh/1100076.png" "$PACKAGE/payload/1100076.png" || die 'Installed flag differs'
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
    equal "$BACKUP/2d00.hex" "$PACKAGE/target/2d00.original.hex" || die 'Dataset baseline damaged'
    equal "$BACKUP/280.hex" "$PACKAGE/target/280.original.hex" || die 'Default-language baseline damaged'
}
require_space() {
    # Join all lines after the header: a long device name may wrap onto its own line.
    SPACE=$(df -k "$APP" | "$AWK" 'NR > 1 { printf "%s ", $0 }') || die 'Cannot read free space'
    set -- $SPACE
    [ "$#" -ge 4 ] || die 'Unrecognized df output'
    case $4 in ''|*[!0-9]*) die 'Unrecognized available space' ;; esac
    [ "$4" -ge 40000 ] || die 'At least 40000 KiB free in /mnt/app is required'
}
prepare_backup() {
    [ ! -e "$STATE" ] || die 'Existing package state: use CHECK or RESTORE; do not overwrite it'
    mkdir -p "$BACKUP" "$RECOVERY" || die 'Cannot create recovery directories'
    # Store the reviewed originals from the live unit, not just supplied copies.
    for FILE in lang_data.zip lang_hmi_builtin.config language_lut_hmi.txt; do
        case $FILE in lang_data.zip) SOURCE=$LSD/jars/$FILE ;; *) SOURCE=$LSD/$FILE ;; esac
        copy_checked "$SOURCE" "$BACKUP/$FILE"
    done
    echo "$CURRENT" > "$BACKUP/2d00.hex" || die 'Cannot save visible languages'
    echo "$CURRENT280" > "$BACKUP/280.hex" || die 'Cannot save default languages'
    for DIR in scripts payload stock target; do
        cp -Rp "$PACKAGE/$DIR" "$RECOVERY/" || die 'Cannot stage internal recovery package'
    done
    copy_checked "$PACKAGE/SHA1SUMS" "$RECOVERY/SHA1SUMS"
    copy_checked "$PACKAGE/HMI.sha1" "$RECOVERY/HMI.sha1"
    mkdir "$RECOVERY/tools" || die 'Cannot create recovery tools directory'
    for TOOL in "$SHA" "$AWK" "$SED" "$XXD" "$READER"; do
        copy_checked "$TOOL" "$RECOVERY/tools/${TOOL##*/}"
    done
    echo 'CHECK' > "$RECOVERY/ACTION.txt" || die 'Cannot stage recovery action'
    mkdir "$RECOVERY/logs" || die 'Cannot create recovery log directory'
    ORIGINAL_PACKAGE=$PACKAGE
    PACKAGE=$RECOVERY
    verify_manifest
    PACKAGE=$ORIGINAL_PACKAGE
    echo 'STOCK_AND_ABSENT_HOOKS' > "$BACKUP/COMPLETE" || die 'Cannot seal baseline'
    sync || die 'Cannot sync baseline'
    verify_backup
    # Off-device originals remain available on SD1 as well.
    [ ! -L "$MIB/uk-localization/backups" ] || die 'Unsafe SD backup directory'
    mkdir -p "$MIB/uk-localization/backups" || die 'Cannot create SD baseline folder'
    SD_BACKUP=$MIB/uk-localization/backups/baseline-${LOG##*/}
    mkdir "$SD_BACKUP" || die 'Cannot create a fresh SD baseline'
    for FILE in lang_data.zip lang_hmi_builtin.config language_lut_hmi.txt 2d00.hex 280.hex COMPLETE; do
        copy_checked "$BACKUP/$FILE" "$SD_BACKUP/$FILE"
    done
    sync || die 'Cannot sync SD baseline'
}

# No source of M.I.B. GLOBALS: it has unrelated write/side effects.
for TOOL in "$SHA" "$AWK" "$SED" "$XXD" "$READER"; do
    [ -x "$TOOL" ] || { echo "ERROR: Required M.I.B. tool is missing: $TOOL"; exit 1; }
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
trap 'rm -f "$LOCK" "$READER_TMP"' 0
trap 'exit 1' 1 2 15

if [ "$#" -eq 1 ]; then
    ACTION=$1
else
    ACTION=$(cat "$PACKAGE/ACTION.txt") || die 'Missing ACTION.txt'
    [ "$ACTION" != CHECK ] || MENU=1
fi
case $ACTION in CHECK|INSTALL|RESTORE|VOICE_INSTALL|VOICE_RESTORE) ;; *) die 'Invalid action; use CHECK, INSTALL, RESTORE, VOICE_INSTALL or VOICE_RESTORE' ;; esac
say "Ukrainian localization 1.0 / action=$ACTION"
verify_manifest
EXPECTED_HMI=$(cat "$PACKAGE/HMI.sha1") || die 'Missing HMI fingerprint'
ACTUAL_HMI=$(file_sha1 /ifs/lsd.jxe) || die 'Cannot fingerprint live HMI'
[ "$ACTUAL_HMI" = "$EXPECTED_HMI" ] || die 'HMI is not the exact reviewed K3346/MU1438 binary'
# Same EEPROM offsets as upstream GLOBALS; require exactly the requested bytes.
read_eeprom() {
    on -f rcc /net/rcc/usr/apps/modifyE2P r "$1" "$2" > "$READER_TMP" 2>&1 || return 1
    "$AWK" -v expected="$2" '
        $1 ~ /^0x[0-9a-fA-F]+:?$/ {
            for (i=2;i<=NF;i++) {
                if ($i ~ /[^0-9a-fA-F]/ || length($i) % 2) break
                out=out $i
            }
        }
        END { if (length(out) != expected * 2) exit 1; print out }
    ' "$READER_TMP" | "$XXD" -r -p | "$SED" 's/[^a-zA-Z0-9_-]//g'
}
TRAIN=$(read_eeprom 3A0 19) || die 'Cannot read real firmware train'
MU=$(read_eeprom 3B9 4) || die 'Cannot read MU version'
[ "$TRAIN" = MHI2_ER_AUG22_K3346 ] && [ "$MU" = 1438 ] || die "Wrong firmware: $TRAIN / MU$MU"
say "Verified identity: $TRAIN / MU$MU / exact HMI fingerprint"
for BUSY in backup.mib reboot.mib flash.mib; do
    [ ! -f "/net/rcc/dev/shmem/$BUSY" ] || die 'M.I.B. backup/reboot/flash is running'
done
[ -d "$LSD/images/HMISettingsEvoHigh" ] || die 'EvoHigh flag directory missing'
[ ! -L "$STATE" ] && [ ! -L "$BACKUP" ] && [ ! -L "$RECOVERY" ] || die 'Unsafe state directory'
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
say 'Persistence values read and CRC-checked.'

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
mount -uw "$APP" || die 'Cannot remount /mnt/app read-write'
if [ "$ACTION" = INSTALL ]; then
    if [ ! -e "$STATE" ]; then prepare_backup; fi
    RECHECK=$(blob "$KEY" 389) || die 'Cannot recheck visible languages'
    RECHECK280=$(blob "$KEY280" 22) || die 'Cannot recheck default languages'
    [ "$RECHECK" = "$CURRENT" ] && [ "$RECHECK280" = "$CURRENT280" ] || die 'Datasets changed during preparation'
fi
echo "$ACTION" > "$STATE/PENDING" || die 'Cannot journal operation'
sync || die 'Cannot sync journal'
MUTATING=1
case $ACTION in
    INSTALL)
        activate "$PACKAGE/payload/1100076.png" "$LSD/images/HMISettingsEvoHigh/1100076.png"
        activate "$PACKAGE/payload/lang_hmi_builtin.config" "$LSD/lang_hmi_builtin.config"
        activate "$PACKAGE/payload/lang_data.zip" "$LSD/jars/lang_data.zip"
        activate "$PACKAGE/payload/lang_uk_hook.jar" "$LSD/jars/lang_uk_hook.jar"
        sync || die 'Cannot sync resources'
        write_blob "$KEY" "$PACKAGE/target/2d00.uk.hex" 389
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
        # Baseline requires these hooks/flag to have been absent before install.
        # Also covers a corrupt or half-written managed hook after interruption.
        for FILE in "$LSD/jars/lang_uk_voice.jar" "$LSD/jars/lang_uk_hook.jar" "$LSD/images/HMISettingsEvoHigh/1100076.png"; do
            [ ! -L "$FILE" ] && [ ! -d "$FILE" ] || die "Unsafe restore destination: $FILE"
            rm -f "$FILE" "$FILE.uk-new" || die "Cannot restore original absence: $FILE"
        done
        activate "$BACKUP/lang_data.zip" "$LSD/jars/lang_data.zip"
        activate "$BACKUP/lang_hmi_builtin.config" "$LSD/lang_hmi_builtin.config"
        activate "$BACKUP/language_lut_hmi.txt" "$LSD/language_lut_hmi.txt"
        write_blob "$KEY" "$BACKUP/2d00.hex" 389
        write_blob "$KEY280" "$BACKUP/280.hex" 22
        verify_stock
        rm -f "$STATE/INSTALLED" || die 'Cannot clear installation marker'
        echo 'RESTORED' > "$STATE/RESTORED" || die 'Cannot record restoration'
        ;;
esac
sync || die 'Final sync failed'
rm "$STATE/PENDING" || die 'Cannot clear pending journal'
sync || die 'Journal sync failed'
MUTATING=0
say "SUCCESS: $ACTION completed and file/dataset read-back verified. No automatic reboot."
say 'Vehicle UI, persistence after cold boot, speech and Virtual Cockpit remain to be tested.'
# Like M.I.B., hand /mnt/app back read-only once everything (including the log) is written.
mount -ur "$APP" 2>/dev/null
