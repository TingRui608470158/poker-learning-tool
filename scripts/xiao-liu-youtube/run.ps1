# Xiao Liu YouTube tools - PowerShell launcher
# Default: batch_download.py | Add "whisper" for batch_whisper.py

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$mode = "download"
$rest = @($args)
if ($args.Count -gt 0 -and $args[0] -eq "whisper") {
    $mode = "whisper"
    if ($args.Count -gt 1) {
        $rest = $args[1..($args.Length - 1)]
    } else {
        $rest = @()
    }
} elseif ($args.Count -gt 0 -and $args[0] -eq "to-srt") {
    $mode = "to-srt"
    if ($args.Count -gt 1) {
        $rest = @("--video-id", $args[1])
    } else {
        $rest = @()
    }
} elseif ($args.Count -gt 0 -and $args[0] -eq "all") {
    $mode = "all"
    if ($args.Count -gt 1) {
        $rest = $args[1..($args.Length - 1)]
    } else {
        $rest = @()
    }
}

if ($rest.Count -eq 0) {
    Write-Host "Examples:" -ForegroundColor Cyan
    if ($mode -eq "whisper") {
        Write-Host "  .\run.ps1 whisper --dry-run --limit 3"
        Write-Host "  .\run.ps1 whisper --limit 1"
        Write-Host "  .\run.ps1 whisper --only-no-subs"
    } elseif ($mode -eq "to-srt") {
        Write-Host "  .\run.ps1 to-srt"
        Write-Host "  .\run.ps1 to-srt 6ibZiZb2-2k"
    } elseif ($mode -eq "all") {
        Write-Host "  .\run.ps1 all --dry-run"
        Write-Host "  .\run.ps1 all --limit 10"
        Write-Host "  .\run.ps1 all"
        Write-Host "  .\run.ps1 all --skip-whisper"
    } else {
        Write-Host "  .\run.ps1 --dry-run --limit 5"
        Write-Host "  .\run.ps1 --limit 5"
        Write-Host "  .\run.ps1 all --dry-run"
        Write-Host "  .\run.ps1 whisper --limit 1"
    }
    Write-Host ""
    if (-not (Test-Path "cookies.txt")) {
        Write-Host "Tip: place cookies.txt in this folder" -ForegroundColor Yellow
    }
}

if ($mode -eq "whisper") {
    python batch_whisper.py @rest
} elseif ($mode -eq "to-srt") {
    python whisper_to_srt.py @rest
} elseif ($mode -eq "all") {
    python batch_all.py @rest
} else {
    python batch_download.py @rest
}
exit $LASTEXITCODE
