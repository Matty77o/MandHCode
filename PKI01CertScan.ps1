# Get all SSL certificates from the local machine store
$certificates = Get-ChildItem -Path Cert:\LocalMachine\My

# Select the relevant properties and display them
$certificates | Select-Object Subject, Thumbprint, NotAfter | Format-Table -AutoSize

# Export to CSV in the current user's Desktop folder
$exportPath = Join-Path -Path $env:USERPROFILE -ChildPath "Desktop\SSL_Certificates_Expiry.csv"
$certificates | Select-Object Subject, Thumbprint, NotAfter | Export-Csv -Path $exportPath -NoTypeInformation
