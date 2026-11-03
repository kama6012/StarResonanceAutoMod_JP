param([ValidateSet('CPU','CUDA')][string]$Variant)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if ($Variant -eq 'CPU') { $env:FORCE_CPU='1'; $env:FORCE_CUDA='0' }
else { $env:FORCE_CPU='0'; $env:FORCE_CUDA='1' }
# CUDA distribution includes CPU fallback. OpenCL is not built in this release.
$env:FORCE_NO_OPENCL='1'
Push-Location cpp_extension
try {
    python setup.py build_ext --inplace
    if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
} finally { Pop-Location }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed' }
python -m PyInstaller --noconfirm --clean --onefile --console --python-option u --python-option 'X utf8' --name StarResonanceAutoMod --add-data 'locales/ja.json;locales' --hidden-import cpp_extension.module_optimizer_cpp --collect-all scapy star_railway_monitor.py
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed' }
$folder = "package/StarResonanceAutoMod_Release_$Variant"
New-Item -ItemType Directory -Force -Path $folder | Out-Null
Copy-Item dist/StarResonanceAutoMod.exe $folder
Copy-Item modules.vdata $folder
Copy-Item LICENSE $folder
Copy-Item README_JA.md "$folder/README.txt"
python scripts/smoke_release.py "$folder/StarResonanceAutoMod.exe"
if ($LASTEXITCODE -ne 0) { throw 'Packaged executable smoke test failed' }
