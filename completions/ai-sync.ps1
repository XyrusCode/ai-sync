# ai-sync PowerShell tab completions
# Ported from agents/completions/agent-limits.bash patterns
#
# Source this in your PowerShell profile:
#   . C:\path\to\ai-sync\completions\ai-sync.ps1

$script:aiSyncPasses = @('skills', 'memory', 'mcp', 'history', 'agent_limits')
$script:aiSyncFlags  = @('--apply', '--only', '--log', '--config', '--version')

Register-ArgumentCompleter -Native -CommandName 'python' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $words = $commandAst.CommandElements | ForEach-Object { $_.ToString() }
    $isAiSync = $false
    $aiSyncIdx = -1

    for ($i = 0; $i -lt $words.Count; $i++) {
        if ($words[$i] -eq '-m' -and ($i + 1) -lt $words.Count -and $words[$i + 1] -eq 'ai_sync') {
            $isAiSync = $true
            $aiSyncIdx = $i + 2
            break
        }
    }

    if (-not $isAiSync) { return $null }

    $current = $wordToComplete.TrimStart('-')

    # After --only, complete with pass names
    $prevIdx = $aiSyncIdx - 1
    if ($prevIdx -ge 0 -and $words[$prevIdx] -eq '--only') {
        return $script:aiSyncPasses | Where-Object { $_ -like "$current*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_)
        }
    }

    # Complete flags
    return $script:aiSyncFlags | Where-Object { $_ -like "-$current*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_)
    }
}
