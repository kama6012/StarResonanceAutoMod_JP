import unittest
from pathlib import Path
from unittest.mock import patch

from BlueProtobuf_pb2 import CharSerialize, Item
from module_parser import ModuleParser


def add_module(data, key=9, parts=(1110, 1410), levels=None, legacy=None, config=5500103):
    item = data.ItemPackage.Packages[5].Items[key]
    item.Uuid = key
    item.ConfigId = config
    item.Quality = 4
    item.ModNewAttr.ModParts.extend(parts)
    if levels is not None:
        item.ModPartLevel.Levels.update(levels)
    if legacy is not None:
        data.Mod.ModInfos[key].InitLinkNums.extend(legacy)
    return item


class PacketTests(unittest.TestCase):
    def parse(self, data):
        # Exercise protobuf serialization too, without running the optimizer or exiting.
        decoded = CharSerialize.FromString(data.SerializeToString())
        with patch.object(ModuleParser, '_optimize_module_combinations'):
            return ModuleParser().parse_module_info(decoded)

    def test_field_21_wire_fixture(self):
        raw = bytes.fromhex('aa01070a0508da081006')
        item = Item.FromString(raw)
        self.assertEqual(dict(item.ModPartLevel.Levels), {1114: 6})
        self.assertEqual(item.SerializeToString(), raw)

    def test_new_map_without_mod_infos_uses_attribute_ids_in_parts_order(self):
        data = CharSerialize()
        add_module(data, parts=(1114, 1410, 1408), levels={1408: 3, 1114: 6, 1410: 10})
        self.assertFalse(data.HasField('Mod'))
        modules = self.parse(data)
        self.assertEqual([(p.id, p.value) for p in modules[0].parts], [(1114, 6), (1410, 10), (1408, 3)])

    def test_legacy_fallback_for_absent_and_empty_maps(self):
        for levels in (None, {}):
            with self.subTest(levels=levels):
                data = CharSerialize()
                add_module(data, levels=levels, legacy=(4, 7))
                self.assertEqual([p.value for p in self.parse(data)[0].parts], [4, 7])

    def test_new_map_is_authoritative_and_does_not_fill_missing_ids_from_legacy(self):
        data = CharSerialize()
        add_module(data, levels={1410: 0}, legacy=(99, 99))
        self.assertEqual([(p.id, p.value) for p in self.parse(data)[0].parts], [(1410, 0)])

    def test_partial_legacy_values(self):
        data = CharSerialize()
        add_module(data, legacy=(3,))
        self.assertEqual([(p.id, p.value) for p in self.parse(data)[0].parts], [(1110, 3)])

    def test_mixed_inventory_skips_non_modules_unknown_configs_and_missing_values(self):
        data = CharSerialize()
        data.ItemPackage.Packages[5].Items[1].ConfigId = 1010
        add_module(data, key=2, levels={1110: 5})
        add_module(data, key=3)
        add_module(data, key=4, config=999999, levels={1110: 5})
        add_module(data, key=5, parts=(), levels={1110: 5})
        add_module(data, key=6, levels={1110: 8})
        self.assertEqual(sorted(m.uuid for m in self.parse(data)), [2, 6])

    def test_empty_container(self):
        self.assertEqual(self.parse(CharSerialize()), [])

    def test_bundled_legacy_snapshot(self):
        data = CharSerialize.FromString((Path(__file__).resolve().parents[1] / 'modules.vdata').read_bytes())
        modules = self.parse(data)
        self.assertTrue(modules)
        self.assertTrue(all(m.parts for m in modules))


if __name__ == '__main__':
    unittest.main()
