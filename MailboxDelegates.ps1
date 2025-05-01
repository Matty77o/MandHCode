# Import the Exchange Online module
Import-Module ExchangeOnlineManagement

# Connect to Exchange Online
Connect-ExchangeOnline

# Prompt the user to enter the calendar owner's email
$CalendarOwner = Read-Host "Enter the calendar owner's email address"

# Prompt the user to enter the delegate user's email
$DelegateUser = Read-Host "Enter the delegate user's email address"

# Grant 'Reviewer' access to the delegate for the owner's calendar
Add-MailboxFolderPermission -Identity "${CalendarOwner}:\Calendar" -User $DelegateUser -AccessRights Reviewer

# Verify that the permission was applied
Get-MailboxFolderPermission -Identity "${CalendarOwner}:\Calendar" | Where-Object { $_.User -eq $DelegateUser }

# Disconnect from Exchange Online
Disconnect-ExchangeOnline -Confirm:$false
