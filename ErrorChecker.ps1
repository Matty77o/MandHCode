# Connect to services
Connect-ExchangeOnline
Connect-AzureAD
Connect-MgGraph -Scopes "DeviceManagementConfiguration.Read.All", "AuditLog.Read.All", "Directory.Read.All"

# Set timeframe
$startDate = (Get-Date).AddDays(-31)
$endDate = Get-Date
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Add-Type -AssemblyName System.Windows.Forms

# Generate timestamped filename
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$defaultFileName = "Error_Report_$timestamp.txt"

# Create and configure SaveFileDialog
$dialog = New-Object System.Windows.Forms.SaveFileDialog
$dialog.Title = "Save Error Report As"
$dialog.InitialDirectory = [Environment]::GetFolderPath("Desktop")
$dialog.FileName = $defaultFileName
$dialog.Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*"

# Show dialog and get selected path
if ($dialog.ShowDialog() -eq "OK") {
    $outputPath = $dialog.FileName
} else {
    Write-Host "Operation cancelled by user." -ForegroundColor Yellow
    return
}


# Create log file
"=== Error Report: Last 31 Days ($startDate to $endDate) ===`n" | Out-File $outputPath

# Corrected Exchange range (10-day limit)
$exchangeStartDate = (Get-Date).AddDays(-10)
"--- Exchange Online: Message Trace Failures (last 10 days) ---" | Out-File -Append $outputPath
Get-MessageTrace -StartDate $exchangeStartDate -EndDate $endDate -PageSize 5000 |
    Where-Object { $_.Status -ne "Delivered" } |
    Select-Object Received, SenderAddress, RecipientAddress, Status |
    Format-Table -AutoSize | Out-String | Out-File -Append $outputPath

$formattedStart = $startDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Sign-in Failures (Graph)
"`n--- Azure AD: Sign-In Failures (Last 31 Days) ---" | Out-File -Append $outputPath
Get-MgAuditLogSignIn -Filter "createdDateTime ge $formattedStart" -Top 999 |
    Where-Object { $_.Status.ErrorCode -ne 0 } |
    Select-Object CreatedDateTime, UserDisplayName, UserPrincipalName, Status |
    Format-Table -AutoSize | Out-String | Out-File -Append $outputPath

# Directory Audit Errors (Graph)
"`n--- Azure AD: Directory Audit Errors (Last 31 Days) ---" | Out-File -Append $outputPath
Get-MgAuditLogDirectoryAudit -Filter "activityDateTime ge $formattedStart" -Top 999 |
    Where-Object { $_.Result -match "fail|error" } |
    Select-Object ActivityDateTime, ActivityDisplayName, InitiatedBy, Result |
    Format-Table -AutoSize | Out-String | Out-File -Append $outputPath

# Intune: Non-Compliant Devices
"`n--- Intune / Endpoint: Non-Compliant Devices ---" | Out-File -Append $outputPath
Get-MgDeviceManagementManagedDevice -All |
    Where-Object {
        $_.ComplianceState -and
        $_.ComplianceState -eq "noncompliant"
    } |
    Select-Object DeviceName, UserDisplayName, ComplianceState, LastContactedDateTime, OperatingSystem |
    Format-Table -AutoSize | Out-String | Out-File -Append $outputPath


# Done
"`nReport saved to: $outputPath" | Out-File -Append $outputPath
Write-Host "✅ Report generated: $outputPath"
