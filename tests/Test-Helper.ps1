$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot '..\Helper.Core.psm1') -Force
$checks=0
function Assert($condition,[string]$message) {
    if (!$condition) { throw $message }
    $script:checks++
}
$names=@('Download mod','Example Mod','by','Example Author','1/44','Free','Download one by one')
$one=Get-ModIdentity -Names $names -Session '100:200'
Assert ($one.Mod -eq 'Example Mod') 'Extract the title from the scoped dialog'
Assert ($one.Progress -eq '1/44') 'Use slash counter, not carousel position'
Assert ($null -eq (Get-ModIdentity @('Download mod','Mod','0/44') 's')) 'Reject zero progress'
Assert ($null -eq (Get-ModIdentity @('Download mod','Mod','45/44') 's')) 'Reject invalid progress'
Assert ($null -eq (Get-ModIdentity @('Download mod','Mod','1/44','2/44') 's')) 'Reject ambiguous counters'
Assert ($null -eq (Get-ModIdentity @('Download mod','Free','1/44') 's')) 'Reject incomplete title'
$state=New-HelperState
Assert (!(Test-NewStableMod $state $one.Key)) 'Do not click on first observation'
Assert (Test-NewStableMod $state $one.Key) 'Allow a stable second observation'
Confirm-HelperClick $state $one.Key
Assert (!(Test-NewStableMod $state $one.Key)) 'Never retry a reserved/invoked key'
Assert (!(Test-NewStableMod $state $one.Key)) 'Moving the same button must not trigger a repeat'
$two=Get-ModIdentity @('Download mod','Another Mod','1/44') '100:200'
Assert ($two.Key -ne $one.Key) 'Changed mod at the same counter is a new identity'
Assert (!(Test-NewStableMod $state $two.Key)) 'Debounce a changed mod'
[void](Test-NewStableMod $state '')
Assert (!(Test-NewStableMod $state $two.Key)) 'Dialog disappearance resets debounce'
Assert (Test-NewStableMod $state $two.Key) 'New mod becomes stable again'
$three=Get-ModIdentity @('Download mod','Another Mod','2/44') '100:200'
Assert (!(Test-NewStableMod $state $three.Key)) 'Changed counter resets debounce'
$restart=Get-ModIdentity $names '100:201'
Assert ($restart.Key -ne $one.Key) 'Process start time prevents PID reuse collisions'
foreach ($scriptFile in Get-ChildItem (Join-Path $PSScriptRoot '..') -Include '*.ps1','*.psm1' -Recurse) {
    $parseErrors=$null; $tokens=$null
    [void][Management.Automation.Language.Parser]::ParseFile($scriptFile.FullName,[ref]$tokens,[ref]$parseErrors)
    Assert (@($parseErrors).Count -eq 0) ('PowerShell parser: '+$scriptFile.Name)
}
Write-Host ('PASS: '+$checks+' checks. No UI input, network access or downloads performed.')
