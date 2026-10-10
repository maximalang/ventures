# Diagnose: is a Hermes source update genuinely running, or is the marker stale?
$ErrorActionPreference = 'Continue'
Write-Output '=== updater-ish processes (hermes/python with update in cmdline) ==='
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'hermes' -and $_.CommandLine -match 'update|install|pm' } |
    Select-Object ProcessId, CreationDate, @{n='Cmd';e={$_.CommandLine.Substring(0, [Math]::Min(160, $_.CommandLine.Length))}} |
    Format-List

Write-Output '=== installs state ==='
$inst = Join-Path $env:LOCALAPPDATA 'hermes\installs\f736b48cbb64a11b'
if (Test-Path $inst) {
    Get-ChildItem $inst -Force | Where-Object { $_.Name -match 'lock|pending|completion' } |
        Select-Object Name, LastWriteTime, Length | Format-Table -AutoSize
    $pend = Join-Path $inst 'source-completion-pending'
    if (Test-Path $pend) { Write-Output ("pending marker EXISTS, mtime: " + (Get-Item $pend).LastWriteTime) }
    else { Write-Output 'pending marker: absent' }
} else {
    Write-Output "installs dir missing: $inst"
}

Write-Output '=== recent desktop/update log lines ==='
$dlog = Join-Path $env:LOCALAPPDATA 'hermes\logs\desktop.log'
if (Test-Path $dlog) { Get-Content $dlog -Tail 40 | Select-String -Pattern 'update|install|apply' | Select-Object -Last 8 }
