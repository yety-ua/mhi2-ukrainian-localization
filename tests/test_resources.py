import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('resource_audit', ROOT / 'tools/audit_resources.py')
resource_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resource_audit)


class ResourceTests(unittest.TestCase):
    def test_released_tables_preserve_a4_target_structure(self):
        report = resource_audit.audit()
        self.assertEqual(report['modules'], 22)
        self.assertEqual(report['nonempty_stock_counterpart_slots'], 15400)
        self.assertEqual(report['errors'], [])
        self.assertTrue(all(row['tokens_already_in_target_source'] for row in report['model_token_audit']))

    def test_connectivity_statuses_are_ukrainian(self):
        import zipfile
        with zipfile.ZipFile(ROOT / 'sd-card/mod/uk-localization/payload/lang_data.zip') as archive:
            strings, _ = resource_audit.unpack(archive.read('resources/HMIConnectivityEvoHigh/strings_uk_UA.data'))
        self.assertEqual(strings[586:593], ['Видимий', 'Невидимий', 'Вимкнено', 'Точка доступу', 'Режим модема', 'Без мережі', 'У мережі'])
        self.assertEqual(strings[888], 'Wi-Fi')
        self.assertEqual(strings[954], 'Wi-Fi')
