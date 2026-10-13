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
                for before, after in [('/net/mmx/fs/sda0', str(self.sd)), ('/mnt/app', str(self.app)),
                                      ('/net/rcc/dev/shmem', str(self.busy)), ('/tmp/uk-localization.lock', str(self.root / 'lock')),
                                      ('/eso/bin/dumb_persistence_writer', str(self.bin / 'writer')),
                                      ('/ifs/lsd.jxe', str(self.root / 'lsd.jxe'))]:
                    text = text.replace(before, after)
                text = text.replace('PATH=/proc/boot:', f'PATH={self.bin}:/proc/boot:')
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
print('0x000003a0 ' + ' '.join(f'{x:02x}' for x in value.encode()))
PY
''')
        self.tool(self.bin / 'mount', '#!/bin/sh\n[ -z "${TEST_FAIL_MOUNT:-}" ]\n')
        self.tool(self.bin / 'df', '#!/bin/sh\necho "disk blocks used avail"\necho "disk 100000 1000 ${TEST_SPACE:-90000}"\n')
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
echo blob:
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
        self.result = subprocess.run(['/bin/sh', str(package / 'scripts/localization.sh')],
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
        (self.root / 'lock').mkdir()
        self.assertNotEqual(self.run_action('INSTALL').returncode, 0)
        self.assertFalse(self.state.exists())
