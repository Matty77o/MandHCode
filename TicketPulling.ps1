# Function to retrieve tickets from Freshservice API
function Get-Tickets {
    param (
        [string]$url
    )
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -ContentType 'application/json'
    } catch {
        Write-Host "Error retrieving data from Freshservice: $_"
        exit
    }
    
    return $response
}

# Function to process and display ticket information
function Process-Tickets {
    param (
        [array]$tickets,
        [int]$page
    )
    
    # Initialize a flag to track if any matching tickets are found on the current page
    $pageHasMatches = $false

    # Define an array of keyword variations related to password resets
    $keywords = @(
        'password reset', 
        'reset password', 
        'change password', 
        'password recovery', 
        'forgot password', 
        'password help', 
        'password assistance'
    )

    foreach ($ticket in $tickets) {
        $subject = $ticket.subject
        $description = $ticket.description_text
        $ticketId = $ticket.id

        # Check if subject or description contains any of the password reset-related keywords
        $matchFound = $false
        foreach ($keyword in $keywords) {
            if ($subject -match "(?i)$keyword" -or $description -match "(?i)$keyword") {
                $matchFound = $true
                break
            }
        }

        # If a match is found, print the ticket ID and mark the page as having matches
        if ($matchFound) {
            Write-Host "Page $page - Matching ticket found - Ticket ID: $ticketId"
            $pageHasMatches = $true
        }
    }

    # If no matching tickets were found on the current page, print a message
    if (-not $pageHasMatches) {
        Write-Host "Page $page - No matching tickets found."
    }
}

# Function to open file dialog and return selected path
function Get-FilePath {
    Add-Type -AssemblyName System.Windows.Forms
    $fileDialog = New-Object System.Windows.Forms.SaveFileDialog
    $fileDialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
    $fileDialog.Title = "Select Output File"
    
    if ($fileDialog.ShowDialog() -eq 'OK') {
        return $fileDialog.FileName
    } else {
        Write-Host "No file selected. Exiting script."
        exit
    }
}

# Prompt user to choose output file location
$outputFilePath = Get-FilePath

# Check if the file path is valid and accessible
if (-not (Test-Path (Split-Path -Path $outputFilePath -Parent))) {
    Write-Host "The directory path is not valid. Exiting script."
    exit
}

# Define Freshservice API credentials
$apiKey = 'lJhSbxO9hBnUPatPzBwh'
$domain = 'mercerhole.freshservice.com'
$headers = @{
    'Authorization' = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:X" -f $apiKey)))
}

# Initialize an array to store unique ticket IDs
$ticketIds = @()

# Fetch tickets from Freshservice API with pagination
$page = 1
$hasMore = $true

Write-Host "Starting pagination over tickets..."
while ($page -le 767) {  # Ensure the loop runs until page 767
    $url = "https://$domain/api/v2/tickets?page=$page"
    $response = Get-Tickets -url $url
    
    # Process and display only tickets that match the "password reset" keywords
    Process-Tickets -tickets $response.tickets -page $page

    # Increment the page count
    $page++

    # Add delay to avoid rate limiting (adjust delay if needed)
    Start-Sleep -Seconds 1
}

Write-Host "Processing complete."
