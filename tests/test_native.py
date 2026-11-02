"""Integration checks with the real extension (required in CI)."""
import importlib.util
import unittest
from unittest.mock import patch

from BlueProtobuf_pb2 import CharSerialize
from module_parser import ModuleParser
from module_types import ModuleCategory, normalize_attribute_name

HAS_NATIVE = importlib.util.find_spec('cpp_extension.module_optimizer_cpp') is not None


@unittest.skipUnless(HAS_NATIVE, 'C++ extension has not been built locally')
class NativeIntegrationTests(unittest.TestCase):
    def test_current_packets_and_japanese_thresholds_reach_native_search(self):
        from module_optimizer import ModuleOptimizer
        data = CharSerialize()
        for key in range(1, 6):
            item = data.ItemPackage.Packages[5].Items[key]
            item.ConfigId = 5500103
            item.Uuid = key
            item.ModNewAttr.ModParts.extend([1110])
            item.ModPartLevel.Levels[1110] = key
        with patch.object(ModuleParser, '_optimize_module_combinations'):
            modules = ModuleParser(lang='ja').parse_module_info(CharSerialize.FromString(data.SerializeToString()))
        attr = normalize_attribute_name('筋力強化')
        engine = ModuleOptimizer(lang='ja', target_attributes=[attr], min_attr_sum_requirements={attr: 14})
        solutions = engine.enumerate_modules(modules, ModuleCategory.ATTACK, top_n=10)
        self.assertTrue(solutions)
        for solution in solutions:
            self.assertEqual(len(solution.modules), 4)
            self.assertGreaterEqual(solution.attr_breakdown[attr], 14)
            self.assertGreater(solution.score, 0)


if __name__ == '__main__':
    unittest.main()
