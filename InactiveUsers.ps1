$drivePath = "\\MH-SA-FS02\Profiles\Production"  # Path to the shared drive on MH-SA-FS02

# Import the Active Directory module
Import-Module ActiveDirectory

# Query inactive users from Active Directory on the second server
$inactiveUsers = Get-ADUser -Filter {Enabled -eq $false} -Properties SamAccountName

# Get the list of user-related files/folders on the drive (e.g., by SAM Account Name)
$driveItems = Get-ChildItem -Path $drivePath

# Filter the drive items to only show those related to inactive users based on SAM Account Name
$inactiveUserFiles = $driveItems | Where-Object { 
    $userSAM = $_.Name  # Assuming file/folder names match SAMAccountName
    $inactiveUsers.SamAccountName -contains $userSAM
}

# Display results in a table
$inactiveUserFiles | Select-Object Name, FullName | Format-Table -AutoSize

# Optionally, export the results to a CSV file
$inactiveUserFiles | Select-Object Name, FullName | Export-Csv -Path "InactiveUserFiles.csv" -NoTypeInformation
