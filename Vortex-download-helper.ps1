#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$JsonEvents,
    [string]$ControlPath,
    [ValidateSet('ru','en')][string]$Language = 'ru',
    [string]$VortexPath,
    [ValidateRange(1,240)][int]$IdleMinutes = 20,
    [ValidateRange(300,5000)][int]$PollMilliseconds = 750
)
Import-Module (Join-Path $PSScriptRoot 'Helper.Messages.psm1') -Force
function Message([string]$Key) { Get-HelperMessage -Language $Language -Key $Key }
if ($env:OS -ne 'Windows_NT') { throw (Message 'Windows') }
Import-Module (Join-Path $PSScriptRoot 'Helper.Core.psm1') -Force
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    throw (Message 'STA')
}
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
function Emit([string]$type, [hashtable]$data=@{}) {
    if ($JsonEvents) {
        $event=@{type=$type;time=[DateTime]::UtcNow.ToString('o');data=$data}
        [Console]::Out.WriteLine((ConvertTo-Json -InputObject $event -Depth 4 -Compress))
    }
}
$lastControl=''
$stopRequested=$false
function Read-Control {
    if (!$ControlPath -or ![IO.File]::Exists($ControlPath)) { return }
    $control=[IO.File]::ReadAllText($ControlPath)
    if ($control.Length -gt 100) { throw 'Invalid control message size' }
    if ($control -eq $script:lastControl) { return }
    $script:lastControl=$control
    $parts=$control.Trim().Split('|')
    if ($parts.Count -ne 2) { return }
    switch ($parts[1]) {
        'stop' { $script:stopRequested=$true }
        'pause' { $script:paused=$true; Emit 'paused' }
        'resume' { $script:paused=$false; $script:idleSince=Get-Date; Emit 'running' }
    }
}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System.Runtime.InteropServices;
public static class VortexHelperKeys {
  [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int key);
}
'@

if (!$VortexPath) {
    $candidates = @(Get-Process -Name Vortex -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.Path } |
        ForEach-Object { $_.Path } | Sort-Object -Unique)
    if ($candidates.Count -ne 1) { throw (Message 'Open') }
    $VortexPath = $candidates[0]
}
$expectedExe = (Resolve-Path -LiteralPath $VortexPath -ErrorAction Stop).ProviderPath
if ([IO.Path]::GetFileName($expectedExe) -ine 'Vortex.exe') { throw (Message 'Path') }
Write-Host ((Message 'Target') -f $expectedExe)
Emit 'target' @{path=$expectedExe}
$helperState = New-HelperState
$paused = $false
$pauseKeyHeld = $false
$count = 0
$idleSince = Get-Date
$lastMessage = ''
$logPath = Join-Path $env:TEMP 'Vortex-download-helper.log'

function Say([string]$message) {
    if ($script:lastMessage -ne $message) {
        Write-Host ('[{0:HH:mm:ss}] {1}' -f (Get-Date), $message)
        if (!$CheckOnly -and !$JsonEvents) { Add-Content -LiteralPath $logPath -Value ('[{0:yyyy-MM-dd HH:mm:ss}] {1}' -f (Get-Date), $message) -Encoding UTF8 }
        $script:lastMessage = $message
    }
}

function Find-ById($element, [string]$id) {
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, $id)
    return $element.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condition)
}

function Read-DownloadDialog {
    $windows = @(Get-Process -Name Vortex -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.Path -ieq $expectedExe })
    if ($windows.Count -ne 1) { return $null }
    $root = [System.Windows.Automation.AutomationElement]::FromHandle($windows[0].MainWindowHandle)
    if ($root.Current.ProcessId -ne $windows[0].Id) { return $null }
    $dialog = Find-ById $root 'free-user-dl-dialog'
    if ($null -eq $dialog) { return $null }
    $button = Find-ById $dialog 'download-mod-button'
    if ($null -eq $button -or $button.Current.Name -ne 'Download manually' -or !$button.Current.IsEnabled -or $button.Current.IsOffscreen) { return $null }
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Text)
    $texts = $dialog.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
    $names = @($texts | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
    $session = '{0}:{1}' -f $windows[0].Id,$windows[0].StartTime.Ticks
    $identity = Get-ModIdentity -Names $names -Session $session
    if (!$identity) { return $null }
    return [pscustomobject]@{ Key=$identity.Key; Mod=$identity.Mod; Progress=$identity.Progress; Button=$button }
}

Write-Host (Message 'Title')
Write-Host (Message 'Controls')
Write-Host (Message 'Scope')
Write-Host (Message 'Boundary')
Write-Host ''

if ($CheckOnly) {
    $item = Read-DownloadDialog
    if ($null -eq $item) { Write-Host (Message 'Absent'); Emit 'absent' }
    else { Write-Host ((Message 'Detected') -f $item.Progress,$item.Mod); Emit 'detected' @{mod=$item.Mod;progress=$item.Progress} }
    exit
}

$mutex = New-Object System.Threading.Mutex($false, 'Local\CodexVortexDownloadHelper')
if (!$mutex.WaitOne(0)) { Write-Host (Message 'Duplicate'); Emit 'duplicate'; $mutex.Dispose(); exit 3 }
try {
Say (Message 'Started')
Emit 'running'
while ($true) {
    Read-Control
    if ($stopRequested) { break }
    if (!$paused -and ((Get-Date)-$idleSince).TotalMinutes -ge $IdleMinutes) {
        Say (Message 'Timeout')
        Emit 'timeout'
        break
    }
    if ([VortexHelperKeys]::GetAsyncKeyState(0x77) -band 0x8000) { break }
    $pauseDown = [bool]([VortexHelperKeys]::GetAsyncKeyState(0x78) -band 0x8000)
    if ($pauseDown -and !$pauseKeyHeld) { $paused = !$paused; $idleSince=Get-Date; Say $(if($paused){(Message 'Paused')}else{(Message 'Resumed')}); Emit $(if($paused){'paused'}else{'running'}) }
    $pauseKeyHeld = $pauseDown
    if ($paused) { Start-Sleep -Milliseconds 250; continue }
    try {
        $item = Read-DownloadDialog
        if ($null -eq $item) {
            [void](Test-NewStableMod $helperState '')
            if ($lastMessage -ne (Message 'Waiting')) { Emit 'waiting' }
            Say (Message 'Waiting')
        } elseif ($helperState.Seen.Contains($item.Key)) {
            [void](Test-NewStableMod $helperState '')
            Say ((Message 'Same') -f $item.Progress,$item.Mod)
        } else {
            if (Test-NewStableMod $helperState $item.Key) {
                # Re-resolve the current dialog and button immediately before invoking it.
                $fresh = Read-DownloadDialog
                if ($null -ne $fresh -and $fresh.Key -eq $item.Key) {
                    Read-Control
                    if ($stopRequested -or $paused) { continue }
                    $pattern = $null
                    if (!$fresh.Button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) {
                        throw (Message 'Invoke')
                    }
                    # Mark before invoking so an uncertain result never causes duplicate clicks.
                    Confirm-HelperClick $helperState $fresh.Key
                    ([System.Windows.Automation.InvokePattern]$pattern).Invoke()
                    $count++
                    Emit 'clicked' @{count=$count;mod=$fresh.Mod;progress=$fresh.Progress}
                    Say ((Message 'Clicked') -f $count,$fresh.Progress,$fresh.Mod)
                    $idleSince=Get-Date
                }
            }
        }
    } catch [System.Windows.Automation.ElementNotAvailableException] {
        [void](Test-NewStableMod $helperState '')
    } catch {
        Emit 'error' @{message=$_.Exception.Message}
        Write-Host ((Message 'Failed') -f $_.Exception.Message) -ForegroundColor Yellow
        break
    }
    Start-Sleep -Milliseconds $PollMilliseconds
}
Write-Host ((Message 'Stopped') -f $count)
} finally {
    Emit 'stopped' @{count=$count}
    Say ((Message 'Stopped') -f $count)
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
