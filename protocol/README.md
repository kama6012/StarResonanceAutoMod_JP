# Module packet schema

`BlueProtobuf.descriptor.pb` is a FileDescriptorSet derived from the upstream
Python binding, extended with `Item.ModPartLevel` (message field **21**) and
`ModPartLevel.Levels` (`map<int32, int32>`, field **1**).

Reference: https://github.com/fudiyangjin/resonance-logs-cn/commit/c7a1b73649c3fda73f10d3fdd946027f5d548050
Also checked against reference repository HEAD
`ed85bbb2eef66727bdfa330d8cf687dac8e6bc1a` (2026-11-02).

Regenerate from the repository root (Python 3.10+):

```sh
python -m pip install grpcio-tools==1.80.0
python -m grpc_tools.protoc --descriptor_set_in=protocol/BlueProtobuf.descriptor.pb --python_out=. BlueProtobuf.proto
```

The new nonempty map is authoritative; missing attribute IDs are skipped.
Absent/empty maps fall back to `Mod.ModInfos[item_key].InitLinkNums` by position.
Unknown items and modules without readable values are skipped.
