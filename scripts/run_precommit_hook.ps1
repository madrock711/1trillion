[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $bash = Get-Command bash -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $bash) {
        throw 'bash를 찾지 못했습니다. 확장자 없는 .githooks/pre-commit을 직접 실행하지 말고 Git for Windows Bash를 설치하거나 PATH를 복구하세요.'
    }

    & bash '.githooks/pre-commit'
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
