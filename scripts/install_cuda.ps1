# Minimal NVIDIA CUDA 12.9.1 toolkit for the Windows release runner.
$ErrorActionPreference = 'Stop'
$cudaRoot = Join-Path $env:RUNNER_TEMP 'cuda-12.9'
New-Item -ItemType Directory -Force -Path $cudaRoot | Out-Null
$packages = @(
    @{path='cuda_nvcc/windows-x86_64/cuda_nvcc-windows-x86_64-12.9.86-archive.zip'; sha='227b109663b5e57d2718bcabb24a4ba0d9d4e52d958e327dc476f7c28691be85'},
    @{path='cuda_cudart/windows-x86_64/cuda_cudart-windows-x86_64-12.9.79-archive.zip'; sha='179e9c43b0735ffe67207b3da556eb5a0c50f3047961882b7657d3b822d34ef8'}
)
foreach ($package in $packages) {
    $archive = Join-Path $env:RUNNER_TEMP ([IO.Path]::GetFileName($package.path))
    Invoke-WebRequest "https://developer.download.nvidia.com/compute/cuda/redist/$($package.path)" -OutFile $archive
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLower() -ne $package.sha) { throw 'CUDA package checksum mismatch' }
    $unpack = "$archive-unpacked"
    Expand-Archive -LiteralPath $archive -DestinationPath $unpack
    $content = @(Get-ChildItem -LiteralPath $unpack -Directory)
    if ($content.Count -ne 1) { throw 'Unexpected CUDA package structure' }
    Copy-Item -Path "$($content[0].FullName)/*" -Destination $cudaRoot -Recurse -Force
}
"CUDA_HOME=$cudaRoot" | Out-File $env:GITHUB_ENV -Append
"CUDA_PATH=$cudaRoot" | Out-File $env:GITHUB_ENV -Append
"$cudaRoot/bin" | Out-File $env:GITHUB_PATH -Append
