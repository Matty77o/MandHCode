# Required modules
Import-Module ExchangeOnlineManagement
Import-Module Microsoft.Graph.Users

# Connect to services
Connect-ExchangeOnline
Connect-MgGraph -Scopes "User.Read.All", "Directory.Read.All"

# Output path
$csvPath = "C:\Users\$env:USERPROFILE\Desktop\DeactivatedSharedMailboxes_OnePerRow.csv"
$mailboxReport = @()

# Get all shared mailboxes
$sharedMailboxes = Get-Mailbox -RecipientTypeDetails SharedMailbox -ResultSize Unlimited

# Get all disabled users
$disabledUsers = Get-MgUser -All -Filter "accountEnabled eq false"

# Loop through disabled users
foreach ($user in $disabledUsers) {
    $userUPN = $user.UserPrincipalName
    $userDisplayName = $user.DisplayName

    # Get on-prem AD info (for WhenChanged)
    $adUser = Get-ADUser -Filter "UserPrincipalName -eq '$userUPN'" -Properties WhenChanged -ErrorAction SilentlyContinue
    if (-not $adUser) { continue }

    $disabledDate = $adUser.WhenChanged
    $daysDisabled = (New-TimeSpan -Start $disabledDate -End (Get-Date)).Days

    if ($daysDisabled -lt 90) { continue }

    # Check for shared mailbox match
    foreach ($mailbox in $sharedMailboxes) {
        $match = $false

        if (
            $mailbox.DisplayName -like "*$userDisplayName*" -or
            $mailbox.Alias -like "*$($userUPN.Split('@')[0])*" -or
            $mailbox.EmailAddresses -match $userUPN
        ) {
            $match = $true
        }

        if ($match) {
            # Get FullAccess permissions (delegates)
            $delegates = (Get-MailboxPermission -Identity $mailbox.Identity | Where-Object {
                $_.AccessRights -contains "FullAccess" -and $_.User.ToString() -notmatch "NT AUTHORITY|S-1-5|SELF"
            }).User

            # Add one row per delegate
            foreach ($delegate in $delegates) {
                $mailboxReport += [PSCustomObject]@{
                    SharedMailbox   = $mailbox.PrimarySmtpAddress.ToString()
                    OriginalUserUPN = $userUPN
                    DisabledDate    = $disabledDate
                    DaysDisabled    = $daysDisabled
                    DelegateEmail   = $delegate.ToString()
                }
            }
        }
    }
}

# Export to CSV
$mailboxReport | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "`n✅ Report saved to: $csvPath" -ForegroundColor Green
