# Connect to Microsoft Teams
Connect-MicrosoftTeams

# Connect to Microsoft Graph
Connect-AzureAD

# Get all Teams users with phone numbers (Teams users)
$teamsUsers = Get-CsOnlineUser | Where-Object { $_.LineURI -like "tel:*" }

# Get all call queues to identify users who belong to call queues
$callQueues = Get-CsCallQueue

# Create an output array
$results = $teamsUsers | ForEach-Object {
    # Check if user is part of a call queue starting with "AA_"
    $isCallQueueMember = $callQueues | Where-Object { $_.Identity -like "AA_*" -and $_.Members -contains $_.Identity }

    # Extract the phone number and remove 'tel:' prefix
    $phone = $_.LineURI -replace "tel:", ""

    # Replace +44 with 0 (for UK phone numbers)
    if ($phone -like "+44*") {
        $phone = "0" + $phone.Substring(3)
    }

    $digits = $phone -replace '[^\d]'  # Remove non-digit characters

    # Initialize Job Title and Office as N/A
    $jobTitle = "N/A"
    $office = "N/A"

    # Only get Job Title and Office if the user is not part of a call queue starting with "AA_"
    if (-not $isCallQueueMember) {
        # Fetch user details from Microsoft Graph API
        $user = Get-AzureADUser -ObjectId $_.UserPrincipalName

        if ($user) {
            $jobTitle = $user.JobTitle
            $office = $user.PhysicalDeliveryOfficeName
        }
    }

    # Set department based on whether it's a call queue member
    $department = if ($isCallQueueMember) {
        "N/A"
    } elseif ($_.Department) {
        $_.Department
    } else {
        "Unknown"
    }

    # Create an object for each user
    [PSCustomObject]@{
        FullName    = $_.DisplayName
        PhoneNumber = $phone
        Extension   = if ($digits.Length -ge 4) { $digits.Substring($digits.Length - 4) } else { "N/A" }
        Department  = $department
        JobTitle    = $jobTitle
        Office      = $office
    }
}

# Export results to CSV
$results | Export-Csv -Path "$env:USERPROFILE\Desktop\Teams_Phone_Directory.csv" -NoTypeInformation -Force
