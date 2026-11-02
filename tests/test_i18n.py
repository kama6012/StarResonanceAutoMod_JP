import ast
import contextlib
import importlib
import io
import json
from pathlib import Path
import string
import sys
import types
import unittest
from unittest.mock import Mock, patch

from i18n import normalize_language, t
from module_parser import ModuleParser
from module_types import (
    MODULE_ATTR_NAMES, MODULE_ATTR_NAMES_EN, MODULE_ATTR_NAMES_JA,
    MODULE_NAMES_JA, display_attr, display_module, display_category,
    normalize_attribute_name, normalize_category, ModuleInfo, ModulePart,
)
from network_interface_util import select_network_interface
from star_railway_monitor import parse_args, StarResonanceMonitor
from packet_capture import PacketCapture

ROOT = Path(__file__).resolve().parents[1]


class LanguageTests(unittest.TestCase):
    def test_english_default_and_japanese_selection(self):
        self.assertEqual(parse_args([]).lang, 'en')
        self.assertEqual(ModuleParser().lang, 'en')
        self.assertEqual(PacketCapture().lang, 'en')
        self.assertEqual(normalize_language(None), 'en')
        args = parse_args(['--lang', 'JA', '-c', '攻撃', '-attr', '集中・会心', '-mas', '集中・幸運', '8'])
        self.assertEqual(args.lang, 'ja')
        self.assertEqual(normalize_category(args.category), '攻击')
        self.assertEqual(normalize_attribute_name(args.attributes[0]), '暴击专注')
        self.assertEqual(normalize_attribute_name(args.min_attr_sum[0][0]), '幸运专注')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(['--lang', 'invalid'])

    def test_help_language_independent_of_flag_order(self):
        for args in (['--help'], ['--lang', 'ja', '--help'], ['--help', '--lang=ja'], ['-lang', 'zh', '--help']):
            out = io.StringIO()
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                parse_args(args)
            expected = 'モジュール最適化' if 'ja' in ' '.join(args) else '星痕共鸣模组筛选器' if 'zh' in args else 'Star Resonance Module Filter'
            self.assertIn(expected, out.getvalue())

    def test_all_attributes_round_trip_without_changing_internal_keys(self):
        self.assertEqual(set(MODULE_ATTR_NAMES), set(MODULE_ATTR_NAMES_JA))
        for attr_id, cn in MODULE_ATTR_NAMES.items():
            for label in (cn, MODULE_ATTR_NAMES_EN[attr_id], MODULE_ATTR_NAMES_JA[attr_id]):
                self.assertEqual(normalize_attribute_name(label), cn)
            self.assertEqual(display_attr(cn, 'ja'), MODULE_ATTR_NAMES_JA[attr_id])
        for config, name in MODULE_NAMES_JA.items():
            self.assertEqual(display_module(config, lang='ja'), name)
        for ja, cn in [('攻撃','攻击'), ('防御','守护'), ('支援','辅助'), ('すべて','全部')]:
            self.assertEqual(normalize_category(ja), cn)
            self.assertEqual(display_category(cn,'ja'), ja)

    def test_templates_keep_user_values_literal(self):
        self.assertEqual(t('ja', 'Saved module data to: {p0}', p0='{private}/file'), 'モジュールデータを保存しました: {private}/file')
        self.assertEqual(t('zh', 'Score: {p0:.2f}', zh='战斗力: 1.00', p0=1), '战斗力: 1.00')
        self.assertEqual(t('en', 'Score: {p0:.2f}', p0=1), 'Score: 1.00')

    def test_wiki_names_and_previous_japanese_input_aliases(self):
        self.assertEqual(display_module(5500101, lang='ja'), '基本 攻撃型 モジュール')
        self.assertEqual(display_module(5500303, lang='ja'), '卓越 防御型 モジュール')
        for current, previous, canonical in (
            ('特攻ダメージ強化', '特殊攻撃', '特攻伤害'),
            ('精鋭打撃', 'エリート打撃', '精英打击'),
            ('集中・会心', '会心集中', '暴击专注'),
            ('極・適応力', '極・機敏な身のこなし', '极-灵活身法'),
            ('極・幸運会心', '極・チーム幸運会心', '极-全队幸暴'),
        ):
            self.assertEqual(normalize_attribute_name(current), canonical)
            self.assertEqual(normalize_attribute_name(previous), canonical)
            self.assertEqual(display_attr(canonical, 'ja'), current)
        for name in ('防御', '防御型', '守護'):
            self.assertEqual(normalize_category(name), '守护')

    def test_catalog_covers_every_template_and_preserves_placeholders(self):
        catalog = json.loads((ROOT / 'locales/ja.json').read_text(encoding='utf-8'))
        fields = lambda value: sorted((field, spec, conversion) for _, field, spec, conversion in string.Formatter().parse(value) if field is not None)
        for en, ja in catalog.items():
            self.assertTrue(ja, en)
            self.assertEqual(fields(en), fields(ja), en)
        for path in ROOT.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id == 't':
                    self.assertIn(node.args[1].value, catalog, str(path))

    def test_interactive_network_selection_is_japanese(self):
        output = io.StringIO()
        interfaces = [{'name': 'test', 'description': 'test', 'addresses': [], 'is_up': True}]
        with contextlib.redirect_stdout(output), patch('builtins.input', side_effect=['x', '0']) as prompt:
            self.assertEqual(select_network_interface(interfaces, lang='ja'), 0)
        self.assertIn('利用可能なネットワーク', output.getvalue())
        self.assertIn('有効な数値', output.getvalue())
        self.assertIn('番号を入力', prompt.call_args.args[0])

    def test_monitor_propagates_language_to_capture_and_parser(self):
        with patch('star_railway_monitor.get_network_interfaces', return_value=[]):
            monitor = StarResonanceMonitor(lang='ja')
        self.assertEqual(monitor.packet_capture.lang, 'ja')
        self.assertEqual(monitor.module_parser.lang, 'ja')

    def test_solution_console_and_log_use_japanese(self):
        # The display code can be tested without a local C++ toolchain. Do not
        # substitute the native optimizer when actually running a search.
        try:
            optimizer = importlib.import_module('module_optimizer')
        except ModuleNotFoundError as exc:
            if exc.name != 'cpp_extension.module_optimizer_cpp':
                raise
            stub = types.ModuleType('cpp_extension.module_optimizer_cpp')
            for name in ('ModulePart','ModuleInfo','ModuleSolution','strategy_enumeration_gpu_cpp','strategy_beam_search_cpp','test_cuda'):
                setattr(stub, name, Mock())
            with patch.dict(sys.modules, {'cpp_extension.module_optimizer_cpp': stub}):
                optimizer = importlib.import_module('module_optimizer')
            sys.modules.pop('module_optimizer', None)
        engine = optimizer.ModuleOptimizer(lang='ja')
        engine._log_result = Mock()
        module = ModuleInfo(name='卓越攻击', config_id=5500103, uuid=9, quality=4,
                            parts=[ModulePart(id=1110,name='力量加持',value=8)])
        solution = optimizer.ModuleSolution([module], 123.5, {'力量加持': 8})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            engine.print_solution_details(solution, 1)
        self.assertIn('第 1 位', output.getvalue())
        self.assertIn('卓越 攻撃型 モジュール', output.getvalue())
        self.assertIn('筋力強化+8', output.getvalue())
        self.assertIn('スコア: 123.50', output.getvalue())
        self.assertEqual('\n'.join(c.args[0] for c in engine._log_result.call_args_list)+'\n', output.getvalue())


if __name__ == '__main__':
    unittest.main()
