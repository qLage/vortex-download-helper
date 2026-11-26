#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string]$VortexPath,
    [ValidateRange(1,240)][int]$IdleMinutes = 20,
    [ValidateRange(300,5000)][int]$PollMilliseconds = 750
)
if ($env:OS -ne 'Windows_NT') { throw 'This helper requires Windows.' }
Import-Module (Join-Path $PSScriptRoot 'Helper.Core.psm1') -Force
if ([Threading.Thread]::CurrentThread.ApartmentState -ne 'STA') {
    throw 'Use Windows PowerShell with -STA. See README.'
}
$ErrorActionPreference = 'Stop'
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
    if ($candidates.Count -ne 1) { throw 'Open exactly one Vortex instance, or specify -VortexPath.' }
    $VortexPath = $candidates[0]
}
$expectedExe = (Resolve-Path -LiteralPath $VortexPath -ErrorAction Stop).ProviderPath
if ([IO.Path]::GetFileName($expectedExe) -ine 'Vortex.exe') { throw 'Expected a Vortex.exe path.' }
Write-Host ('Target: '+$expectedExe)
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
        if (!$CheckOnly) { Add-Content -LiteralPath $logPath -Value ('[{0:yyyy-MM-dd HH:mm:ss}] {1}' -f (Get-Date), $message) -Encoding UTF8 }
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

Write-Host 'Vortex download helper'
Write-Host 'F8: stop. F9: pause/resume. Closing this console also stops the helper.'
Write-Host 'Only the Download manually button in the Vortex collection dialog is used.'
Write-Host 'No screen coordinates, browser clicks, Premium buttons or Skip buttons.'
Write-Host ''

if ($CheckOnly) {
    $item = Read-DownloadDialog
    if ($null -eq $item) { Write-Host 'No eligible Vortex download dialog found.' }
    else { Write-Host ('Detected without clicking: {0} - {1}' -f $item.Progress,$item.Mod) }
    exit
}

$mutex = New-Object System.Threading.Mutex($false, 'Local\CodexVortexDownloadHelper')
if (!$mutex.WaitOne(0)) { Write-Host 'The helper is already running.'; $mutex.Dispose(); exit }
try {
Say 'Helper started. F8 stops; F9 pauses. Waiting for a NEW mod.'
while ($true) {
    if (!$paused -and ((Get-Date)-$idleSince).TotalMinutes -ge $IdleMinutes) {
        Say 'Idle timeout. Check Vortex for completion or errors; this does not confirm all files downloaded.'
        break
    }
    if ([VortexHelperKeys]::GetAsyncKeyState(0x77) -band 0x8000) { break }
    $pauseDown = [bool]([VortexHelperKeys]::GetAsyncKeyState(0x78) -band 0x8000)
    if ($pauseDown -and !$pauseKeyHeld) { $paused = !$paused; $idleSince=Get-Date; Say $(if($paused){'Paused (F9 to resume).'}else{'Resumed.'}) }
    $pauseKeyHeld = $pauseDown
    if ($paused) { Start-Sleep -Milliseconds 250; continue }
    try {
        $item = Read-DownloadDialog
        if ($null -eq $item) {
            [void](Test-NewStableMod $helperState '')
            Say 'Waiting for the next Vortex download dialog. F8 stops the helper.'
        } elseif ($helperState.Seen.Contains($item.Key)) {
            [void](Test-NewStableMod $helperState '')
            Say ('Waiting for the mod to change: {0} - {1}' -f $item.Progress,$item.Mod)
        } else {
            if (Test-NewStableMod $helperState $item.Key) {
                # Re-resolve the current dialog and button immediately before invoking it.
                $fresh = Read-DownloadDialog
                if ($null -ne $fresh -and $fresh.Key -eq $item.Key) {
                    $pattern = $null
                    if (!$fresh.Button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) {
                        throw 'Vortex does not expose the Invoke pattern for this button. No coordinate fallback is used.'
                    }
                    # Mark before invoking so an uncertain result never causes duplicate clicks.
                    Confirm-HelperClick $helperState $fresh.Key
                    ([System.Windows.Automation.InvokePattern]$pattern).Invoke()
                    $count++
                    Say ('Clicked #{0}: {1} - {2}' -f $count,$fresh.Progress,$fresh.Mod)
                    $idleSince=Get-Date
                }
            }
        }
    } catch [System.Windows.Automation.ElementNotAvailableException] {
        [void](Test-NewStableMod $helperState '')
    } catch {
        Write-Host ('Stopped safely: '+$_.Exception.Message) -ForegroundColor Yellow
        break
    }
    Start-Sleep -Milliseconds $PollMilliseconds
}
Write-Host ('Stopped. Download buttons pressed: '+$count)
} finally {
    Say ('Helper stopped. Download buttons pressed: '+$count)
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
