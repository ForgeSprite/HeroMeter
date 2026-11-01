# Builds dist\HeroMeter.exe (one portable file).
# Needs Python 3.10+:  pip install pyinstaller numpy pillow
$ErrorActionPreference = "Stop"
$src = Join-Path $PSScriptRoot "src"
python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name "HeroMeter" `
    --icon (Join-Path $src "icon.ico") `
    --add-data "$(Join-Path $src 'fonts');fonts" `
    --add-data "$(Join-Path $src 'icon.ico');." `
    --hidden-import numpy --hidden-import PIL.ImageGrab --hidden-import PIL.ImageDraw --hidden-import PIL.ImageTk `
    --distpath (Join-Path $PSScriptRoot "dist") `
    --workpath (Join-Path $PSScriptRoot "build") `
    --specpath (Join-Path $PSScriptRoot "build") `
    (Join-Path $src "meter.py")
Write-Host "Built: $(Join-Path $PSScriptRoot 'dist\HeroMeter.exe')"
