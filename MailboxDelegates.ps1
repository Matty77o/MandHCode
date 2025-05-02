# Import the Exchange Online module
Import-Module ExchangeOnlineManagement

# Connect to Exchange Online
Connect-ExchangeOnline

# Prompt the user to enter the calendar owner's email
$CalendarOwner = Read-Host "Enter the calendar owner's email address"

# Prompt the user to enter the delegate user's email
$DelegateUser = Read-Host "Enter the delegate user's email address"

# Define the folder identity
$CalendarFolder = "${CalendarOwner}:\Calendar"

# Grant access based on whether the user is 'Default' or not
if ($DelegateUser -eq "Default") {
    # Modify existing permission for 'Default'
    Set-MailboxFolderPermission -Identity $CalendarFolder -User Default -AccessRights Reviewer
}
else {
    # Grant new permission to a specific delegate
    Add-MailboxFolderPermission -Identity $CalendarFolder -User $DelegateUser -AccessRights Reviewer
}

# Verify that the permission was applied
Get-MailboxFolderPermission -Identity $CalendarFolder | Where-Object { $_.User -eq $DelegateUser }

# Disconnect from Exchange Online
Disconnect-ExchangeOnline -Confirm:$false
