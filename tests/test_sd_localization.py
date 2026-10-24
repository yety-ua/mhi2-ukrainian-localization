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


class BlobParserTests(unittest.TestCase):
    def parse(self, text, size=389):
        return subprocess.run(['awk', '-v', f'bytes={size}', '-f', str(ROOT / 'sd-card/uk-localization/scripts/blob.awk')],
                              input=text, text=True, capture_output=True)

    def test_contiguous_and_multiline_bytes(self):
        value = (ROOT / 'sd-card/uk-localization/target/2d00.original.hex').read_text().strip()
        self.assertEqual(self.parse('blob: ' + value).stdout.strip(), value)
        tokens = ['0x' + value[i:i+2].lower() for i in range(0, len(value), 2)]
        text = 'blob:\n' + '\n'.join(' '.join(tokens[i:i+16]) for i in range(0, len(tokens), 16))
        self.assertEqual(self.parse(text).stdout.strip(), value)

    def test_bad_crc_and_ambiguity_fail(self):
        original = (ROOT / 'sd-card/uk-localization/target/2d00.original.hex').read_text().strip()
        target = (ROOT / 'sd-card/uk-localization/target/2d00.uk.hex').read_text().strip()
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
        self.package = self.sd / 'uk-localization'
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
        for n in ['lang_data.zip', 'lang_hmi_builtin.config', 'language_lut_hmi.txt']:
            dest = self.lsd / ('jars/' + n if n.endswith('.zip') else n)
            shutil.copyfile(self.package / 'stock' / n, dest)
        for key, source in [('3221422086', '2d00.original.hex'), ('3221422085', '280.original.hex')]:
            shutil.copyfile(self.package / 'target' / source, self.store / key)
        self.tool(self.bin / 'on', '''#!/bin/sh
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
        self.tool(self.bin / 'mount', '#!/bin/sh\necho "$*" >> "$TEST_ROOT/mounts"\ncase "$2" in "$TEST_ROOT/sd") [ -n "${TEST_SD_STAYS_RO:-}" ] || chmod -R u+w "$2" ;; esac\n[ -z "${TEST_FAIL_MOUNT:-}" ]\n')
        self.tool(self.bin / 'df', '#!/bin/sh\necho "Filesystem 1K-blocks Used Available Use% Mounted"\nif [ -n "${TEST_DF_WRAP:-}" ]; then echo "/dev/a-very-long-device-name"; echo "    100000 1000 ${TEST_SPACE:-90000} 1% /mnt/app"; else echo "disk 100000 1000 ${TEST_SPACE:-90000} 1% /mnt/app"; fi\n')
        self.tool(self.bin / 'writer', '''#!/bin/sh
echo "$4" >> "$TEST_ROOT/writes"
[ -z "${TEST_FAIL_WRITE:-}" ] || exit 1
[ -z "${TEST_SKIP_WRITE:-}" ] || exit 0
echo "$5" > "$TEST_ROOT/persistence/$4"
''')
        tools = self.sd / 'apps/sbin'
        self.tool(tools / 'sha1sum', '#!/bin/sh\n/usr/bin/shasum -a 1 "$@"\n')
        for n in ['awk', 'sed', 'xxd']:
            self.tool(tools / n, f'#!/bin/sh\n{shutil.which(n)} "$@"\n')
        self.tool(tools / 'dumb_persistence_reader', '''#!/bin/sh
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
        self.assertNotEqual(self.run_action('INSTALL', TEST_SKIP_WRITE='1').returncode, 0)
        self.assertTrue((self.state / 'PENDING').exists())
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

    def test_wrapped_df_output_is_understood(self):
        self.success(self.run_action('CHECK', TEST_DF_WRAP='1'))
        self.assertNotEqual(self.run_action('CHECK', TEST_DF_WRAP='1', TEST_SPACE='100').returncode, 0)

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
        for path in [ROOT / 'sd-card/uk-localization/scripts/localization.sh',
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
            for path in [ROOT / 'sd-card/uk-localization/scripts/localization.sh',
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
