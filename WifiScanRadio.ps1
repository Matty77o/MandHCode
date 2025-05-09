# --- Self-elevate if not already running as admin ---
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrator")) {
    Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs

}

# --- Prompt for subnet ---
$subnet = Read-Host "Enter subnet (example: 192.168.0)"
$results = @()

Write-Host "Scanning devices on subnet $subnet.0/24..." -ForegroundColor Cyan

# --- Ping scan and gather WiFi info ---
1..254 | ForEach-Object {
    $ip = "$subnet.$_"
    if (Test-Connection -ComputerName $ip -Count 1 -Quiet) {
        try {
            $wifiInfo = Invoke-Command -ComputerName $ip -ScriptBlock {
                $netsh = netsh wlan show interfaces
                $output = [PSCustomObject]@{
                    ComputerName   = $env:COMPUTERNAME
                    IPAddress      = $using:ip
                    SSID           = ($netsh | Select-String '^\s*SSID\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
                    RadioType      = ($netsh | Select-String '^\s*Radio type\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
                    SignalStrength = ($netsh | Select-String '^\s*Signal\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
                }
                return $output
            } -ErrorAction Stop

            $results += $wifiInfo
        } catch {
            Write-Host "Could not get info from $ip." -ForegroundColor Yellow
        }
    } else {
        Write-Host "No response from $ip" -ForegroundColor DarkGray
    }
}

# --- Export results to CSV ---
$outputPath = "$env:USERPROFILE\Desktop\WiFiScanResults.csv"
$results | Export-Csv -Path $outputPath -NoTypeInformation
Write-Host "`nScan complete. Results saved to $outputPath" -ForegroundColor Green

Pause 
