"""Execute the SD installer only in isolated trees with simulated QNX tools."""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = os.environ.get('UK_TEST_SHELL', '/bin/sh')
spec = importlib.util.spec_from_file_location('sd_builder', ROOT / 'tools/package_release.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


GAWK_BUILTINS = {'and', 'or', 'xor', 'compl', 'lshift', 'rshift', 'strtonum', 'gensub', 'gsub', 'sub', 'match',
                 'split', 'sprintf', 'substr', 'index', 'length', 'tolower', 'toupper', 'systime', 'strftime',
                 'mktime', 'asort', 'asorti', 'patsplit', 'typeof', 'isarray', 'int', 'sqrt', 'exp', 'log',
                 'sin', 'cos', 'atan2', 'rand', 'srand', 'close', 'fflush', 'system', 'getline', 'printf', 'print',
                 'delete', 'exit', 'next', 'nextfile', 'return', 'function', 'func', 'while', 'for', 'if', 'else',
                 'do', 'in', 'BEGIN', 'END', 'bindtextdomain', 'dcgettext', 'dcngettext', 'strptime', 'stat'}


class AwkCompatibilityTests(unittest.TestCase):
    """The unit's awk is gawk: a user function named like a gawk builtin (xor) is a hard syntax error there."""
    def test_blob_awk_defines_no_function_named_like_a_gawk_builtin(self):
        import re
        text = (ROOT / 'sd-card/mod/uk-localization/scripts/blob.awk').read_text()
        names = set(re.findall(r'^function\s+(\w+)', text, re.M))
        self.assertTrue(names)
        self.assertFalse(names & GAWK_BUILTINS, names & GAWK_BUILTINS)

    def test_blob_awk_runs_under_every_installed_awk(self):
        awks = [w for w in (shutil.which('gawk'), shutil.which('mawk'), shutil.which('awk')) if w]
        flags = {'gawk': [[], ['--posix'], ['--traditional']]}
        base = ROOT / 'sd-card/mod/uk-localization'
        cases = [('target/2d00.original.hex', 389), ('target/2d00.uk.hex', 389), ('target/280.original.hex', 22)]
        for awk in awks:
            for extra in flags.get(Path(awk).name, [[]]):
                for name, size in cases:
                    value = (base / name).read_text().strip()
                    r = subprocess.run([awk, *extra, '-v', f'bytes={size}', '-f', str(base / 'scripts/blob.awk')],
                                       input=value + '\n', text=True, capture_output=True)
                    self.assertEqual(r.stdout.strip(), value.upper(), f'{awk} {extra} {name}: {r.stderr}')


class BlobParserTests(unittest.TestCase):
    def parse(self, text, size=389):
        return subprocess.run(['awk', '-v', f'bytes={size}', '-f', str(ROOT / 'sd-card/mod/uk-localization/scripts/blob.awk')],
                              input=text, text=True, capture_output=True)

    def test_contiguous_and_multiline_bytes(self):
        value = (ROOT / 'sd-card/mod/uk-localization/target/2d00.original.hex').read_text().strip()
        self.assertEqual(self.parse('blob: ' + value).stdout.strip(), value)
        tokens = ['0x' + value[i:i+2].lower() for i in range(0, len(value), 2)]
        text = 'blob:\n' + '\n'.join(' '.join(tokens[i:i+16]) for i in range(0, len(tokens), 16))
        self.assertEqual(self.parse(text).stdout.strip(), value)

    def test_bad_crc_and_ambiguity_fail(self):
        original = (ROOT / 'sd-card/mod/uk-localization/target/2d00.original.hex').read_text().strip()
        target = (ROOT / 'sd-card/mod/uk-localization/target/2d00.uk.hex').read_text().strip()
        self.assertNotEqual(self.parse(original[:-4] + '0000').returncode, 0)
        self.assertNotEqual(self.parse(original + '\n' + target).returncode, 0)


class SdInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = builder.validated_sources()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sd = self.root / 'sd'
        self.package = self.sd / 'mod/uk-localization'
        self.app = self.root / 'app'
        self.lsd = self.app / 'eso/hmi/lsd'
        self.state = self.app / 'root/uk-localization'
        self.bin = self.root / 'bin'
        self.busy = self.root / 'busy'
        self.store = self.root / 'persistence'
        for p in [self.bin, self.busy, self.store, self.sd / 'apps/sbin', self.package / 'logs',
                  self.lsd / 'jars', self.lsd / 'images/HMISettingsEvoHigh']:
            p.mkdir(parents=True, exist_ok=True)
        for name, blob in self.sources.items():
            p = self.package / name
            p.parent.mkdir(parents=True, exist_ok=True)
            if name == 'scripts/localization.sh':
                text = blob.decode()
                for before, after in [
                                      ('RUNTIME_DIRS="/tmp /dev/shmem /net/rcc/dev/shmem"', f'RUNTIME_DIRS="{self.root}/no-such-dir {self.root}"'),
                                      ('/net/rcc/mnt/efs-persist', str(self.root / 'persist')),
                                     ('/net/mmx/fs/sda0', str(self.sd)), ('/mnt/app', str(self.app)),
                                      ('/net/rcc/dev/shmem', str(self.busy)), 
                                      ('/eso/bin/dumb_persistence_writer', str(self.bin / 'writer')),
                                      ('/ifs/lsd.jxe', str(self.root / 'lsd.jxe'))]:
                    text = text.replace(before, after)
                text = text.replace('PATH=/proc/boot:', f'PATH={self.bin}:/proc/boot:')
                assert str(self.root) + '/no-such-dir' in text, 'RUNTIME_DIRS substitution did not apply'
                blob = text.encode()
            p.write_bytes(blob)
        (self.root / 'lsd.jxe').write_bytes(b'reviewed fixture HMI')
        (self.package / 'HMI.sha1').write_text(hashlib.sha1(b'reviewed fixture HMI').hexdigest() + '\n')
        self.manifest()
        for n in ['lang_data.zip', 'lang_hmi_builtin.config', 'language_lut_hmi.txt', '1100066.png']:
            dest = self.lsd / ('jars/' + n if n.endswith('.zip') else 'images/HMISettingsEvoHigh/' + n if n.endswith('.png') else n)
            shutil.copyfile(self.package / 'stock' / n, dest)
        for key, source in [('3221422086', '2d00.original.hex'), ('3221422085', '280.original.hex')]:
            shutil.copyfile(self.package / 'target' / source, self.store / key)
        self.tool(self.bin / 'on', '''#!/bin/sh
[ -z "${TEST_HANG_E2P:-}" ] || sleep 30
shift 2
[ "$1" = /net/rcc/usr/apps/modifyE2P ] || exit 1
python3 - "$3" <<'PY'
import os,sys
value=os.environ.get('TEST_TRAIN','MHI2_ER_AUG22_K3346') if sys.argv[1]=='3A0' else '1438'
data = value.encode()
fmt = os.environ.get('TEST_E2P_FORMAT', 'spaced')
hexes = [f'{x:02x}' for x in data]
if fmt == 'spaced':
    print('0x000003a0 ' + ' '.join(hexes))
elif fmt == 'colon':
    print('0x000003a0: ' + ' '.join(hexes))
elif fmt == 'grouped':
    print('0x000003a0  ' + ' '.join(''.join(hexes[i:i+2]) for i in range(0, len(hexes), 2)))
elif fmt == 'compact':
    print('0x000003a0 ' + ''.join(hexes))
elif fmt == 'rows16':
    for i in range(0, len(hexes), 16):
        print(f'0x{0x3a0 + i:08x}  ' + ' '.join(hexes[i:i+16]))
PY
''')
        self.tool(self.bin / 'mkdir', '#!/bin/sh\nfor a in "$@"; do case "$a" in "$TEST_ROOT"/uk-localization.*) echo "mkdir: $a: Operation not supported" >&2; exit 1 ;; esac; done\nexec /bin/mkdir "$@"\n')
        self.tool(self.bin / 'cp', '#!/bin/sh\nfor a in "$@"; do case "$a" in *"${TEST_CP_FAIL_ONCE:-@@none@@}") if [ ! -e "$TEST_ROOT/cp_failed" ]; then : > "$TEST_ROOT/cp_failed"; echo "cp: $a: I/O error" >&2; exit 1; fi ;; esac; case "$a" in */recovery/tools/*) [ -z "${TEST_FAIL_TOOL_COPY:-}" ] || { echo "cp: $a: No space left on device" >&2; exit 1; } ;; esac; done\nexec /bin/cp "$@"\n')
        self.tool(self.bin / 'mount', '#!/bin/sh\necho "$*" >> "$TEST_ROOT/mounts"\ncase "$2" in "$TEST_ROOT/sd") [ -n "${TEST_SD_STAYS_RO:-}" ] || chmod -R u+w "$2" ;; "$TEST_ROOT/app") [ "$1" != -uw ] || chmod -R u+w "$2" ;; esac\n[ -z "${TEST_FAIL_MOUNT:-}" ]\n')
        self.tool(self.bin / 'df', '''#!/bin/sh
SPACE=${TEST_SPACE:-90000}
case "${TEST_DF_FORMAT:-header}" in
    real) echo "/dev/mnand0t177           995280    716943 $SPACE      73%  /mnt/app/" ;;
    wrap) echo "Filesystem 1K-blocks Used Available Use% Mounted"; echo "/dev/a-very-long-device-name"; echo "    100000 1000 $SPACE 1% /mnt/app" ;;
    *) echo "Filesystem 1K-blocks Used Available Use% Mounted"; echo "disk 100000 1000 $SPACE 1% /mnt/app" ;;
esac
''')
        self.tool(self.bin / 'writer', '''#!/bin/sh
[ -z "${TEST_SLOW_WRITE:-}" ] || sleep "$TEST_SLOW_WRITE"
if [ -n "${TEST_FAIL_WRITE_ONCE:-}" ] && [ ! -e "$TEST_ROOT/writer_failed" ]; then : > "$TEST_ROOT/writer_failed"; exit 1; fi
echo "$4" >> "$TEST_ROOT/writes"
[ -z "${TEST_FAIL_WRITE:-}" ] || exit 1
[ -z "${TEST_SKIP_WRITE:-}" ] || exit 0
echo "$5" > "$TEST_ROOT/persistence/$4"
''')
        tools = self.sd / 'apps/sbin'
        self.tool(tools / 'sha1sum', '#!/bin/sh\n/usr/bin/shasum -a 1 "$@"\n')
        # the unit's awk is gawk (awk -> gawk), so prefer it; UK_TEST_AWK overrides
        real = {'awk': os.environ.get('UK_TEST_AWK') or shutil.which('gawk') or shutil.which('awk'),
                'sed': shutil.which('sed'), 'xxd': shutil.which('xxd')}
        for n, path in real.items():
            self.tool(tools / n, f'#!/bin/sh\n{path} "$@"\n')
        self.tool(tools / 'dumb_persistence_reader', '''#!/bin/sh
[ -z "${TEST_SLOW_READ:-}" ] || sleep "$TEST_SLOW_READ"
[ -z "${TEST_READER_PREFIX:-}" ] || echo blob:
if [ -n "${TEST_BAD_READ:-}" ]; then echo invalid; else cat "$TEST_ROOT/persistence/$2"; fi
''')

    def tool(self, path, content):
        path.write_text(content)
        path.chmod(0o755)

    def manifest(self):
        files = sorted(p for p in self.package.rglob('*') if p.is_file() and
                       (p.relative_to(self.package).parts[0] in ['scripts', 'stock', 'target', 'payload'] or p.name == 'HMI.sha1'))
        (self.package / 'SHA1SUMS').write_text(''.join(f'{hashlib.sha1(p.read_bytes()).hexdigest()}  {p.relative_to(self.package)}\n' for p in files))

    def run_action(self, action, package=None, **env):
        package = package or self.package
        (package / 'ACTION.txt').write_text(action + '\n')
        self.result = subprocess.run([SHELL, str(package / 'scripts/localization.sh')],
                                     env={**os.environ, 'TEST_ROOT': str(self.root), **env}, text=True, capture_output=True)
        return self.result

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_is_read_only_and_rejects_wrong_identity(self):
        self.success(self.run_action('CHECK'))
        self.assertFalse(self.state.exists())
        self.assertFalse((self.root / 'writes').exists())
        self.assertNotEqual(self.run_action('INSTALL', TEST_TRAIN='MHI2_ER_AU37x_P5089').returncode, 0)
        self.assertFalse(self.state.exists())

    def test_full_install_voice_restore_and_reinstall(self):
        self.success(self.run_action('INSTALL'))
        self.assertEqual((self.package / 'ACTION.txt').read_text().strip(), 'CHECK')
        self.assertIn(f'-ur {self.app}', (self.root / 'mounts').read_text())
        self.assertEqual((self.root / 'writes').read_text().splitlines(), ['3221422086'])
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['payload/lang_data.zip'])
        self.assertTrue(list((self.package / 'backups').glob('baseline-*')))
        self.success(self.run_action('CHECK'))
        self.success(self.run_action('VOICE_INSTALL'))
        self.success(self.run_action('VOICE_RESTORE'))
        self.assertTrue((self.lsd / 'jars/lang_uk_hook.jar').exists())
        self.success(self.run_action('VOICE_INSTALL'))
        self.success(self.run_action('RESTORE'))
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['stock/lang_data.zip'])
        self.assertFalse((self.lsd / 'jars/lang_uk_hook.jar').exists())
        self.assertFalse((self.lsd / 'jars/lang_uk_voice.jar').exists())
        self.success(self.run_action('CHECK'))
        baseline = (self.state / 'baseline/lang_data.zip').read_bytes()
        self.success(self.run_action('INSTALL'))
        self.assertEqual((self.state / 'baseline/lang_data.zip').read_bytes(), baseline)

    def test_corrupt_payload_unknown_baseline_and_low_space_do_not_write(self):
        (self.package / 'payload/lang_uk_hook.jar').write_bytes(b'corrupt')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        self.assertFalse(self.state.exists())
        (self.package / 'payload/lang_uk_hook.jar').write_bytes(self.sources['payload/lang_uk_hook.jar'])
        (self.lsd / 'lang_hmi_builtin.config').write_bytes(b'unknown modification')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        shutil.copyfile(self.package / 'stock/lang_hmi_builtin.config', self.lsd / 'lang_hmi_builtin.config')
        self.assertNotEqual(self.run_action('INSTALL', TEST_SPACE='100').returncode, 0)
        self.assertFalse((self.root / 'writes').exists())

    def test_failed_write_is_journalled_and_recoverable(self):
        self.assertNotEqual(self.run_action('INSTALL', TEST_FAIL_WRITE='1').returncode, 0)
        self.assertTrue((self.state / 'PENDING').exists())
        self.assertNotEqual(self.run_action('CHECK').returncode, 0)
        (self.store / '3221422086').write_text('corrupt')
        self.success(self.run_action('RESTORE'))
        self.assertFalse((self.state / 'PENDING').exists())

    def test_internal_recovery_without_sd(self):
        self.success(self.run_action('INSTALL'))
        recovery = self.state / 'recovery'
        self.sd.rename(self.root / 'removed-sd')
        self.success(self.run_action('RESTORE', package=recovery))
        self.assertFalse((self.lsd / 'jars/lang_uk_hook.jar').exists())

    def test_unmanaged_hooks_busy_operation_and_bad_crc_block_install(self):
        hook = self.lsd / 'jars/lang_uk_hook.jar'
        hook.write_bytes(b'existing owner modification')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        self.assertEqual(hook.read_bytes(), b'existing owner modification')
        hook.unlink()
        busy = self.busy / 'backup.mib'
        busy.touch()
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        busy.unlink()
        self.assertNotEqual(self.run_action('INSTALL', TEST_BAD_READ='1').returncode, 0)
        self.assertFalse(self.state.exists())

    def test_upgrade_from_baseline_without_flag_copy(self):
        self.success(self.run_action('INSTALL'))
        (self.state / 'baseline/1100066.png').unlink()
        flag = self.lsd / 'images/HMISettingsEvoHigh/1100066.png'
        flag.write_bytes(self.sources['stock/1100066.png'])
        self.assertNotIn('Baseline damaged', self.run_action('CHECK').stdout)
        self.success(self.run_action('RESTORE'))
        self.assertEqual(flag.read_bytes(), self.sources['stock/1100066.png'])
        self.success(self.run_action('CHECK'))
        # /mnt/app is read-only until the installer remounts it; the baseline copy must wait for that.
        subprocess.run(['chmod', '-R', 'a-w', str(self.state)], check=True)
        self.addCleanup(subprocess.run, ['chmod', '-R', 'u+w', str(self.state)])
        self.success(self.run_action('INSTALL'))
        self.assertEqual((self.state / 'baseline/1100066.png').read_bytes(), self.sources['stock/1100066.png'])
        self.assertEqual(flag.read_bytes(), self.sources['payload/1100076.png'])
        self.success(self.run_action('RESTORE'))
        self.assertEqual(flag.read_bytes(), self.sources['stock/1100066.png'])

    def test_missing_backup_and_symlink_destination_are_refused(self):
        flag = self.lsd / 'images/HMISettingsEvoHigh/1100076.png'
        flag.symlink_to(self.root / 'unrelated')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        flag.unlink()
        self.success(self.run_action('INSTALL'))
        (self.state / 'baseline/COMPLETE').unlink()
        self.assertNotEqual(self.run_action('RESTORE').returncode, 0)
        self.assertTrue((self.lsd / 'jars/lang_uk_hook.jar').exists())

    def test_truncated_manifest_and_readback_mismatch(self):
        (self.package / 'SHA1SUMS').write_text('')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        self.assertFalse(self.state.exists())
        self.manifest()
        result = self.run_action('INSTALL', TEST_SKIP_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLED BACK', result.stdout)
        self.assertFalse((self.state / 'PENDING').exists())
        self.success(self.run_action('RESTORE'))

    def test_mount_failure_and_stale_lock_are_reported(self):
        self.assertNotEqual(self.run_action('INSTALL', TEST_FAIL_MOUNT='1').returncode, 0)
        self.assertFalse(self.state.exists())
        lock = self.root / 'uk-localization.lock'
        sleeper = subprocess.Popen(['sleep', '60'])
        self.addCleanup(sleeper.kill)
        lock.write_text(f'{sleeper.pid}\n')
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        self.assertIn('is running', self.result.stdout)
        self.assertFalse(self.state.exists())

    def test_stale_lock_without_live_owner_is_replaced(self):
        lock = self.root / 'uk-localization.lock'
        lock.write_text('not a pid\n')
        self.success(self.run_action('CHECK'))
        self.assertIn('Replaced a stale lock', self.result.stdout)
        self.assertFalse(lock.exists())
        dead = subprocess.Popen(['true'])
        dead.wait()
        lock.write_text(f'{dead.pid}\n')
        self.success(self.run_action('INSTALL'))
        self.assertIn('Replaced a stale lock', self.result.stdout)
        self.assertFalse(lock.exists())
        # a leftover lock FOLDER (older releases) is replaced as well
        lock.mkdir()
        self.success(self.run_action('CHECK'))
        self.assertFalse(lock.exists())

    def test_runtime_files_work_when_the_unit_cannot_create_folders_there(self):
        """QNX /dev/shmem (behind /tmp) refuses mkdir: the car reported 'stale lock' for exactly that."""
        self.success(self.run_action('CHECK'))
        self.assertTrue((self.root / 'uk-localization.arm').is_file())
        self.assertFalse(list(self.root.glob('uk-localization.reader.*')))

    def test_lock_failure_explains_itself(self):
        (self.root / 'uk-localization.lock').write_text('x\n')
        self.root.chmod(0o555)
        self.addCleanup(lambda: self.root.chmod(0o755))
        result = self.run_action('CHECK')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Cannot create the lock file', result.stdout, f'rc={result.returncode} out={result.stdout!r} err={result.stderr!r}')
        self.assertIn('Diagnostics:', result.stdout)

    def test_eeprom_and_persistence_output_formats(self):
        """The car's real reader prints one bare hex line (seen in the car logs); E2P layout is unverified."""
        for fmt in ('spaced', 'colon', 'grouped', 'compact', 'rows16'):
            with self.subTest(e2p=fmt):
                self.success(self.run_action('CHECK', TEST_E2P_FORMAT=fmt))
        with self.subTest(reader='prefixed'):
            self.success(self.run_action('CHECK', TEST_READER_PREFIX='1'))
        with self.subTest(reader='bad'):
            self.assertNotEqual(self.run_action('CHECK', TEST_BAD_READ='1').returncode, 0)

    def test_unwritable_sd_does_not_stop_check_but_stops_install(self):
        """chefranov's installer logs only to RAM; an SD that stays read-only must not block a CHECK."""
        shutil.rmtree(self.package / 'logs')
        (self.package / 'ACTION.txt').write_text('CHECK\n')
        self.package.chmod(0o555)
        self.addCleanup(lambda: os.system(f'chmod -R u+w "{self.sd}"'))
        result = self.run_action('CHECK', TEST_SD_STAYS_RO='1')
        self.success(result)
        self.assertIn('WARNING: the SD card cannot be written', result.stdout)
        self.assertIn('CHECK PASS', result.stdout)
        self.assertTrue((self.root / 'uk-localization.log').exists())
        self.assertFalse(self.state.exists())
        # an explicit INSTALL must still refuse before changing anything
        self.assertNotEqual(self.run_action('INSTALL', TEST_SD_STAYS_RO='1').returncode, 0)
        self.assertFalse(self.state.exists())

    def test_slow_steps_show_a_heartbeat(self):
        result = self.run_action('CHECK', TEST_SLOW_READ='7')
        self.success(result)
        self.assertIn('still working', result.stdout)
        self.assertIn('Fingerprinting the HMI image', result.stdout)

    def test_unreadable_eeprom_only_warns_and_keeps_partial_output(self):
        """On the car modifyE2P never answered from GEM; the HMI fingerprint already pins the build."""
        result = self.run_action('CHECK', TEST_HANG_E2P='1', UK_PROBE_LIMIT='1')
        self.success(result)
        self.assertIn('did not finish within 1s', result.stdout)
        self.assertIn('partial output:', result.stdout)
        self.assertIn('WARNING: the firmware train/MU could not be read', result.stdout)
        self.assertIn('CHECK PASS', result.stdout)

    def test_train_from_cached_files_needs_no_eeprom(self):
        persist = self.root / 'persist/SWDL'
        persist.mkdir(parents=True)
        (persist / 'CachedTrain.txt').write_text('MHI2_ER_AUG22_K3346\r\n')
        (persist / 'CachedMuVersion.txt').write_text('MU1438\n')
        result = self.run_action('CHECK', TEST_HANG_E2P='1')
        self.success(result)
        self.assertIn('Verified identity: MHI2_ER_AUG22_K3346', result.stdout)
        self.assertNotIn('EEPROM', result.stdout)
        (persist / 'CachedTrain.txt').write_text('MHI2_ER_AU37x_P5089\n')
        wrong = self.run_action('CHECK', TEST_HANG_E2P='1')
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn('Wrong firmware train', wrong.stdout)

    def test_awk_symlink_to_gawk_like_the_unit_installs_and_restores(self):
        """On the unit awk -> gawk: the symlink must not reach the recovery copy (hash check refuses links)."""
        (self.sd / 'apps/sbin/awk').unlink()
        real = os.environ.get('UK_TEST_AWK') or shutil.which('gawk') or shutil.which('awk')
        self.tool(self.bin / 'gawk', f'#!/bin/sh\n{real} "$@"\n')
        (self.bin / 'awk').symlink_to(self.bin / 'gawk')
        self.success(self.run_action('CHECK'))
        self.success(self.run_action('INSTALL'))
        copied = self.state / 'recovery/tools/awk'
        self.assertTrue(copied.is_file() and not copied.is_symlink())
        self.success(self.run_action('RESTORE'))

    def test_only_a_symlinked_awk_is_refused_before_any_state_is_created(self):
        (self.sd / 'apps/sbin/awk').unlink()
        self.tool(self.bin / 'gawk-real', '#!/bin/sh\nexec awk "$@"\n')
        (self.bin / 'awk').symlink_to(self.bin / 'gawk-real')
        result = self.run_action('INSTALL')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.state.exists())

    def test_failed_backup_preparation_removes_its_unfinished_folder(self):
        result = self.run_action('INSTALL', TEST_FAIL_TOOL_COPY='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unfinished package folder', result.stdout)
        self.assertFalse(self.state.exists())
        self.success(self.run_action('CHECK'))
        self.success(self.run_action('INSTALL'))

    def test_install_and_restore_report_every_step_on_screen(self):
        result = self.run_action('INSTALL', TEST_SLOW_WRITE='6')
        self.success(result)
        out = result.stdout
        for needle in ('Saving the original language files', 'Staging the internal recovery copy',
                       'Saving a second copy of the originals on the SD card', 'Backups are complete',
                       'Remounting ', 'Starting INSTALL', 'writing 1100076.png', 'writing lang_data.zip',
                       'Writing persistence dataset 3221422086', 'persistence write 3221422086: still working',
                       'Reading dataset 3221422086 back', 'SUCCESS: INSTALL', 'NEXT: restart the MMI'):
            self.assertIn(needle, out)
        restore = self.run_action('RESTORE')
        self.success(restore)
        self.assertIn('Verifying the restored originals', restore.stdout)
        self.assertIn('NEXT: restart the MMI', restore.stdout)

    def test_a_hung_persistence_write_is_stopped_and_can_be_restored(self):
        result = self.run_action('INSTALL', TEST_SLOW_WRITE='20', UK_WRITE_LIMIT='2')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('did not finish within 2s', result.stdout)
        self.assertIn('Do not reboot', result.stdout)
        self.assertTrue((self.state / 'PENDING').exists())
        self.success(self.run_action('RESTORE'))
        self.assertFalse((self.state / 'PENDING').exists())

    def assert_back_to_stock(self):
        for name, dest in [('lang_data.zip', 'jars/lang_data.zip'), ('lang_hmi_builtin.config', 'lang_hmi_builtin.config'),
                           ('language_lut_hmi.txt', 'language_lut_hmi.txt'),
                           ('1100066.png', 'images/HMISettingsEvoHigh/1100066.png')]:
            self.assertEqual((self.lsd / dest).read_bytes(), self.sources['stock/' + name], name)
        self.assertFalse((self.lsd / 'jars/lang_uk_hook.jar').exists())
        self.assertFalse((self.lsd / 'images/HMISettingsEvoHigh/1100076.png').exists())
        self.assertEqual((self.store / '3221422086').read_text().strip().upper(),
                         (self.package / 'target/2d00.original.hex').read_text().strip().upper())
        self.assertFalse((self.state / 'PENDING').exists())
        self.assertTrue((self.state / 'RESTORED').exists())
        self.assertFalse((self.state / 'INSTALLED').exists())

    def test_failed_dataset_write_rolls_back_automatically(self):
        result = self.run_action('INSTALL', TEST_FAIL_WRITE_ONCE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('rolling back to the saved originals', result.stdout)
        self.assertIn('ROLLED BACK', result.stdout)
        self.assertNotIn('Changes may remain', result.stdout)
        self.assert_back_to_stock()
        again = self.run_action('CHECK')
        self.success(again)
        self.assertIn('package can be installed again', again.stdout)
        self.success(self.run_action('INSTALL'))

    def test_failed_resource_copy_rolls_back_automatically(self):
        result = self.run_action('INSTALL', TEST_CP_FAIL_ONCE='lang_data.zip.uk-new')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLED BACK', result.stdout)
        self.assert_back_to_stock()

    def test_failed_rollback_keeps_the_journal_and_manual_restore_still_works(self):
        result = self.run_action('INSTALL', TEST_FAIL_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Changes may remain', result.stdout)
        self.assertNotIn('ROLLED BACK', result.stdout)
        self.assertTrue((self.state / 'PENDING').exists())
        self.success(self.run_action('RESTORE'))
        self.assert_back_to_stock()

    def test_failed_voice_install_removes_the_voice_hook(self):
        self.success(self.run_action('INSTALL'))
        result = self.run_action('VOICE_INSTALL', TEST_CP_FAIL_ONCE='lang_uk_voice.jar.uk-new')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROLLED BACK', result.stdout)
        self.assertFalse((self.lsd / 'jars/lang_uk_voice.jar').exists())
        self.assertTrue((self.lsd / 'jars/lang_uk_hook.jar').exists())
        self.assertFalse((self.state / 'PENDING').exists())
        self.success(self.run_action('CHECK'))

    def test_df_output_formats_including_the_units_headerless_one(self):
        for fmt in ('real', 'header', 'wrap'):
            with self.subTest(df=fmt):
                self.success(self.run_action('CHECK', TEST_DF_FORMAT=fmt))
                low = self.run_action('CHECK', TEST_DF_FORMAT=fmt, TEST_SPACE='100')
                self.assertNotEqual(low.returncode, 0)
                self.assertIn('At least 40000 KiB', low.stdout)

    def press(self, **env):
        return self.run_action('CHECK', **env)

    def arm(self):
        path = self.root / 'uk-localization.arm'
        return path.read_text().strip() if path.exists() else None

    def test_menu_three_presses_install_then_restore(self):
        self.success(self.press())
        self.assertEqual(self.arm(), 'INSTALL 1')
        self.assertIn('run this same GEM item again', self.result.stdout)
        self.assertFalse(self.state.exists())
        self.success(self.press())
        self.assertEqual(self.arm(), 'INSTALL 2')
        self.assertIn('CONFIRM (step 2 of 3)', self.result.stdout)
        self.assertFalse(self.state.exists())
        self.assertFalse((self.root / 'writes').exists())
        self.success(self.press())
        self.assertIn('SUCCESS: INSTALL', self.result.stdout)
        self.assertIsNone(self.arm())
        self.assertEqual((self.package / 'ACTION.txt').read_text().strip(), 'CHECK')
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['payload/lang_data.zip'])
        self.success(self.press())
        self.assertEqual(self.arm(), 'RESTORE 1')
        self.assertIn('nothing needs to be done', self.result.stdout)
        self.success(self.press())
        self.success(self.press())
        self.assertIn('SUCCESS: RESTORE', self.result.stdout)
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['stock/lang_data.zip'])
        self.assertIsNone(self.arm())

    def test_restart_forgets_pending_step(self):
        self.success(self.press())
        self.success(self.press())
        (self.root / 'uk-localization.arm').unlink()
        self.success(self.press())
        self.assertEqual(self.arm(), 'INSTALL 1')
        self.assertFalse(self.state.exists())

    def test_explicit_action_and_failure_clear_pending_step(self):
        self.success(self.press())
        self.success(self.press())
        self.success(self.run_action('INSTALL'))
        self.assertIsNone(self.arm())
        self.success(self.run_action('RESTORE'))
        self.success(self.press())
        self.assertEqual(self.arm(), 'INSTALL 1')
        self.assertNotEqual(self.press(TEST_TRAIN='MHI2_ER_AU37x_P5089').returncode, 0)
        self.assertIsNone(self.arm())

    def test_argument_check_never_arms(self):
        result = subprocess.run([SHELL, str(self.package / 'scripts/localization.sh'), 'CHECK'],
                                env={**os.environ, 'TEST_ROOT': str(self.root)}, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIsNone(self.arm())

    def test_menu_offers_restore_for_interrupted_install(self):
        self.assertNotEqual(self.run_action('INSTALL', TEST_FAIL_WRITE='1').returncode, 0)
        self.assertNotEqual(self.press().returncode, 0)
        self.assertEqual(self.arm(), 'RESTORE 1')
        self.assertIn('Do NOT reboot', self.result.stdout)
        self.assertNotEqual(self.press().returncode, 0)
        self.assertEqual(self.arm(), 'RESTORE 2')
        self.success(self.press())
        self.assertIn('SUCCESS: RESTORE', self.result.stdout)
        self.assertFalse((self.state / 'PENDING').exists())
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['stock/lang_data.zip'])

    def test_menu_offers_restore_when_installed_files_differ(self):
        self.success(self.run_action('INSTALL'))
        (self.lsd / 'jars/lang_uk_hook.jar').write_bytes(b'tampered')
        self.assertNotEqual(self.press().returncode, 0)
        self.assertEqual(self.arm(), 'RESTORE 1')
        self.assertNotEqual(self.press().returncode, 0)
        self.assertEqual(self.arm(), 'RESTORE 2')
        self.success(self.press())
        self.assertFalse((self.lsd / 'jars/lang_uk_hook.jar').exists())
        self.assertEqual((self.lsd / 'jars/lang_data.zip').read_bytes(), self.sources['stock/lang_data.zip'])


class CommandWrapperTests(unittest.TestCase):
    def test_command_hands_over_to_custom_and_keeps_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / 'mod'
            mod.mkdir()
            shutil.copyfile(ROOT / 'sd-card/mod/command.sh', mod / 'command.sh')
            run = lambda: subprocess.run([SHELL, str(mod / 'command.sh')], text=True, capture_output=True)
            missing = run()
            self.assertEqual(missing.returncode, 1)
            self.assertIn('custom.sh is missing', missing.stdout)
            (mod / 'custom.sh').write_text('#!/bin/sh\necho handed-over\nexit 3\n')
            result = run()
            self.assertEqual(result.returncode, 3)
            self.assertIn('handed-over', result.stdout)


class QnxShellCompatibilityTests(unittest.TestCase):
    """The unit's QNX ksh (pdksh family) pre-defines aliases such as hash; defining or calling
    them by name breaks parsing (seen on the car: syntax error at `hash() {`)."""
    ALIASES = ['hash', 'autoload', 'functions', 'history', 'integer', 'local', 'login',
               'nohup', 'r', 'stop', 'suspend', 'type', 'command']

    def test_no_predefined_ksh_alias_names_in_package_scripts(self):
        import re
        for path in [ROOT / 'sd-card/mod/uk-localization/scripts/localization.sh',
                     ROOT / 'sd-card/mod/custom.sh', ROOT / 'sd-card/mod/command.sh']:
            text = path.read_text()
            for name in self.ALIASES:
                self.assertIsNone(re.search(r'^\s*' + name + r'\s*\(\)', text, re.M), (path.name, name))
                self.assertIsNone(re.search(r'(\$\(|`|^\s*|[;&|]\s*)' + name + r'\s+', text, re.M), (path.name, name))


class PdkshParseTests(unittest.TestCase):
    """oksh/mksh/pdksh reproduce the unit's ksh parsing (the `hash() {` failure seen on the car)."""
    def test_scripts_parse_in_every_available_ksh_variant(self):
        shells = [shutil.which(n) for n in ('oksh', 'mksh', 'pdksh', 'ksh')]
        shells = [s for s in shells if s]
        if not shells:
            self.skipTest('no ksh-family shell installed')
        for shell in shells:
            for path in [ROOT / 'sd-card/mod/uk-localization/scripts/localization.sh',
                         ROOT / 'sd-card/mod/custom.sh', ROOT / 'sd-card/mod/command.sh']:
                result = subprocess.run([shell, '-n', str(path)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, f'{shell} {path.name}: {result.stderr}')

    def test_sourcing_by_mib_launcher_does_nothing(self):
        """apps/launcher runs `. mod/command.sh` during M.I.B. setup; exec there would kill the launcher."""
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / 'mod'
            mod.mkdir()
            shutil.copyfile(ROOT / 'sd-card/mod/command.sh', mod / 'command.sh')
            (mod / 'custom.sh').write_text('#!/bin/sh\necho handed-over\nexit 3\n')
            launcher = Path(tmp) / 'launcher'
            launcher.write_text(f'#!/bin/sh\n. {mod}/command.sh\necho launcher-continues\n')
            result = subprocess.run([SHELL, str(launcher)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('launcher-continues', result.stdout)
            self.assertNotIn('handed-over', result.stdout)


class EntryScriptTests(unittest.TestCase):
    """command.sh -> custom.sh -> installer, with the package found next to custom.sh (SD1/mod/uk-localization)."""
    def build(self, tmp, with_package=True):
        sd = Path(tmp) / 'sd'
        mod = sd / 'mod'
        bin_dir = Path(tmp) / 'bin'
        for d in (mod, bin_dir):
            d.mkdir(parents=True)
        for name in ('command.sh', 'custom.sh'):
            shutil.copyfile(ROOT / 'sd-card/mod' / name, mod / name)
        (bin_dir / 'on').write_text('#!/bin/sh\nshift 2\nexec "$@"\n')
        (bin_dir / 'mount').write_text('#!/bin/sh\nexit 0\n')
        for f in bin_dir.iterdir():
            f.chmod(0o755)
        if with_package:
            scripts = mod / 'uk-localization/scripts'
            scripts.mkdir(parents=True)
            (scripts / 'localization.sh').write_text('#!/bin/sh\necho "ran:$0"\necho boom >&2\nexit 7\n')
        return mod, bin_dir

    def run_entry(self, mod, bin_dir, name='command.sh'):
        return subprocess.run([SHELL, str(mod / name)], text=True, capture_output=True,
                              env={**os.environ, 'PATH': f'{bin_dir}:{os.environ["PATH"]}'})

    def test_package_is_found_next_to_the_entry_script_and_errors_are_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod, bin_dir = self.build(tmp)
            for name in ('command.sh', 'custom.sh'):
                r = self.run_entry(mod, bin_dir, name)
                self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
                self.assertIn(f'ran:{mod}/uk-localization/scripts/localization.sh', r.stdout)
                self.assertIn('exit code: 7', r.stdout)
                self.assertIn('shell errors', r.stdout)
                self.assertEqual((mod / 'uk-localization/logs/launcher-errors.txt').read_text().strip(), 'boom')

    def test_missing_package_folder_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod, bin_dir = self.build(tmp, with_package=False)
            r = self.run_entry(mod, bin_dir, 'custom.sh')
            self.assertEqual(r.returncode, 1)
            self.assertIn('uk-localization folder is missing', r.stdout)

