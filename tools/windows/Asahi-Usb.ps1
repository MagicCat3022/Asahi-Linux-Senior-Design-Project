param(
    [ValidateSet('list', 'bind', 'attach', 'detach')]
    [string]$Action = 'list',
    [string]$BusId,
    [switch]$Once
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    throw 'Install usbipd-win in Windows: winget install --interactive --exact dorssel.usbipd-win'
}
if ($Action -eq 'list') {
    & usbipd list
    exit $LASTEXITCODE
}
if (-not $BusId) {
    $MatchesFound = @(& usbipd list | Select-String '^\s*(\d+-\d+)\s+1209:316d\s')
    if ($MatchesFound.Count -ne 1) {
        throw 'Expected one connected m1n1 device. Run list, or provide -BusId (for example 3-6).'
    }
    $BusId = $MatchesFound[0].Matches[0].Groups[1].Value
}
if ($BusId -notmatch '^\d+-\d+$') {
    throw 'Invalid USB bus ID'
}
switch ($Action) {
    'bind' { & usbipd bind --busid $BusId }
    'detach' { & usbipd detach --busid $BusId }
    'attach' {
        if ($Once) {
            & usbipd attach --wsl --busid $BusId
        } else {
            & usbipd attach --wsl --busid $BusId --auto-attach --unplugged
        }
    }
}
exit $LASTEXITCODE
