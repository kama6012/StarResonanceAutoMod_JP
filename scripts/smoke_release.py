"""Exercise the frozen catalog, protobuf and native optimizer without Npcap/GPU."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from BlueProtobuf_pb2 import CharSerialize

exe = Path(sys.argv[1]).resolve()
def run(*args):
    result = subprocess.run([str(exe), *args], capture_output=True, encoding='utf-8',
                            errors='replace', timeout=120)
    output = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(f'Executable exited {result.returncode}: {output}')
    return output

assert 'Star Resonance Module Filter' in run('--help')
assert 'モジュール最適化' in run('--lang', 'ja', '--help')
assert '星痕共鸣模组筛选器' in run('--lang', 'zh', '--help')
snapshot = exe.parent / 'modules.vdata'
original = snapshot.read_bytes()
try:
    data = CharSerialize()
    for key in range(1, 5):
        item = data.ItemPackage.Packages[5].Items[key]
        item.Uuid = key
        item.ConfigId = 5500104
        item.Quality = 4
        item.ModNewAttr.ModParts.extend([1409, 2405])
        item.ModPartLevel.Levels.update({1409: 2, 2405: 2})
    snapshot.write_bytes(data.SerializeToString())
    output = run('--load-vdata', '--lang', 'ja', '-attr', '集中会心', 'HP吸収', '-mas', 'HP吸収', '8')
    assert 'EXC攻撃型モジュール・精選' in output, output
    assert '極・HP吸収' in output and '集中・会心' in output, output
    assert 'スコア:' in output, output
finally:
    snapshot.write_bytes(original)
# Do not ship smoke-test logs.
for log in (exe.parent / 'logs').glob('*.log'):
    log.unlink()
print('Frozen executable smoke tests passed (en/ja/zh and current module packets).')
