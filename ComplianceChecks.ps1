# Install required modules
$requiredModules = @("Microsoft.Graph.Authentication", "Microsoft.Graph.DeviceManagement", "Microsoft.Graph.Users")
foreach ($mod in $requiredModules) {
    if (-not (Get-Module -ListAvailable -Name $mod)) {
        Install-Module $mod -Scope CurrentUser -Force
    }
}

Import-Module Microsoft.Graph.Authentication
Import-Module Microsoft.Graph.DeviceManagement
Import-Module Microsoft.Graph.Users

# Connect to Graph API
Connect-MgGraph -Scopes "DeviceManagementManagedDevices.Read.All", "User.Read.All"

# Output folder
$outputFolder = "$env:USERPROFILE\Desktop\NonCompliantDevices"
if (-not (Test-Path $outputFolder)) {
    New-Item -Path $outputFolder -ItemType Directory | Out-Null
}

# Get all non-compliant devices
$devices = Get-MgDeviceManagementManagedDevice -Filter "complianceState eq 'nonCompliant'" -All

# Containers
$windowsDevices = @()
$iosDevices     = @()
$androidDevices = @()

# Loop through each non-compliant device
foreach ($device in $devices) {
    Write-Host "Processing $($device.DeviceName)" -ForegroundColor Cyan

    $email = try {
        if ($device.UserId) {
            (Get-MgUser -UserId $device.UserId -Property Mail).Mail
        }
    } catch {
        "Unknown"
    }

    $entry = [PSCustomObject]@{
        DeviceName        = $device.DeviceName
        Email             = $email
        OS                = $device.OperatingSystem
        ComplianceState   = $device.ComplianceState
        LastSyncDateTime  = $device.LastSyncDateTime
    }

    switch ($device.OperatingSystem.ToLower()) {
        "windows" { $windowsDevices += $entry }
        "ios"     { $iosDevices     += $entry }
        "android" { $androidDevices += $entry }
    }
}

# Export to CSVs
$windowsDevices | Export-Csv "$outputFolder\NonCompliant_Windows.csv" -NoTypeInformation -Encoding UTF8
$iosDevices     | Export-Csv "$outputFolder\NonCompliant_iOS.csv" -NoTypeInformation -Encoding UTF8
$androidDevices | Export-Csv "$outputFolder\NonCompliant_Android.csv" -NoTypeInformation -Encoding UTF8

Write-Host "`n✅ Export complete! CSVs saved to: $outputFolder" -ForegroundColor Green
