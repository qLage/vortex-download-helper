Set-StrictMode -Version Latest

function Get-ModIdentity {
    param([string[]]$Names, [string]$Session)
    $progress = @($Names | Where-Object { $_ -match '^\s*\d+\s*/\s*\d+\s*$' })
    $heading = [array]::IndexOf($Names, 'Download mod')
    if ($progress.Count -ne 1 -or $heading -lt 0 -or $heading+1 -ge $Names.Count) { return $null }
    $title = $Names[$heading+1].Trim()
    if (!$title -or $title -in @('Free','Download one by one','Download mod')) { return $null }
    $counter = $progress[0] -replace '\s',''
    $numbers = $counter.Split('/')
    if ([long]$numbers[0] -lt 1 -or [long]$numbers[0] -gt [long]$numbers[1]) { return $null }
    # JSON encoding avoids delimiter collisions in mod titles.
    $key = ConvertTo-Json -InputObject @($Session,$counter,$title) -Compress
    return [pscustomobject]@{ Key=$key; Mod=$title; Progress=$counter }
}

function New-HelperState {
    return @{ Candidate=''; Stable=0; Seen=(New-Object 'System.Collections.Generic.HashSet[string]') }
}

function Test-NewStableMod {
    param([hashtable]$State, [string]$Key)
    if (!$Key -or $State.Seen.Contains($Key)) {
        $State.Candidate=''; $State.Stable=0
        return $false
    }
    if ($State.Candidate -eq $Key) { $State.Stable++ }
    else { $State.Candidate=$Key; $State.Stable=1 }
    return $State.Stable -ge 2
}

function Confirm-HelperClick {
    param([hashtable]$State, [string]$Key)
    # Reserve BEFORE invoking: an uncertain invoke result must never be retried automatically.
    [void]$State.Seen.Add($Key)
    $State.Candidate=''; $State.Stable=0
}

Export-ModuleMember -Function Get-ModIdentity,New-HelperState,Test-NewStableMod,Confirm-HelperClick
