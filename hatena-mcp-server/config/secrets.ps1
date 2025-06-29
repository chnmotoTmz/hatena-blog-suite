# Hatena Agent v2 - Secure API Key Management
# クラウド環境対応セキュリティ設定

# Azure Key Vault integration
class AzureKeyVaultManager {
    [string]$VaultName
    [string]$TenantId
    [string]$ClientId
    [string]$ClientSecret
    
    AzureKeyVaultManager([string]$vaultName, [string]$tenantId, [string]$clientId, [string]$clientSecret) {
        $this.VaultName = $vaultName
        $this.TenantId = $tenantId
        $this.ClientId = $clientId
        $this.ClientSecret = $clientSecret
    }
    
    [string] GetSecret([string]$secretName) {
        try {
            # Azure PowerShell module required: Install-Module Az.KeyVault
            $secureSecret = ConvertTo-SecureString $this.ClientSecret -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential($this.ClientId, $secureSecret)
            
            Connect-AzAccount -ServicePrincipal -Credential $credential -Tenant $this.TenantId -WarningAction SilentlyContinue
            
            $secret = Get-AzKeyVaultSecret -VaultName $this.VaultName -Name $secretName
            return $secret.SecretValue | ConvertFrom-SecureString -AsPlainText
        } catch {
            Write-Warning "Failed to retrieve secret from Azure Key Vault: $($_.Exception.Message)"
            return $null
        }
    }
    
    [bool] SetSecret([string]$secretName, [string]$secretValue) {
        try {
            $secureSecret = ConvertTo-SecureString $this.ClientSecret -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential($this.ClientId, $secureSecret)
            
            Connect-AzAccount -ServicePrincipal -Credential $credential -Tenant $this.TenantId -WarningAction SilentlyContinue
            
            $secureValue = ConvertTo-SecureString $secretValue -AsPlainText -Force
            Set-AzKeyVaultSecret -VaultName $this.VaultName -Name $secretName -SecretValue $secureValue
            return $true
        } catch {
            Write-Warning "Failed to set secret in Azure Key Vault: $($_.Exception.Message)"
            return $false
        }
    }
}

# AWS Secrets Manager integration
class AWSSecretsManager {
    [string]$Region
    [string]$AccessKeyId
    [string]$SecretAccessKey
    
    AWSSecretsManager([string]$region, [string]$accessKeyId, [string]$secretAccessKey) {
        $this.Region = $region
        $this.AccessKeyId = $accessKeyId
        $this.SecretAccessKey = $secretAccessKey
    }
    
    [string] GetSecret([string]$secretId) {
        try {
            # AWS PowerShell module required: Install-Module AWS.Tools.SecretsManager
            Set-AWSCredential -AccessKey $this.AccessKeyId -SecretKey $this.SecretAccessKey -StoreAs "TempProfile"
            Set-DefaultAWSRegion -Region $this.Region
            
            $secretValue = Get-SECSecretValue -SecretId $secretId -ProfileName "TempProfile"
            return $secretValue.SecretString
        } catch {
            Write-Warning "Failed to retrieve secret from AWS Secrets Manager: $($_.Exception.Message)"
            return $null
        }
    }
    
    [bool] SetSecret([string]$secretId, [string]$secretValue) {
        try {
            Set-AWSCredential -AccessKey $this.AccessKeyId -SecretKey $this.SecretAccessKey -StoreAs "TempProfile"
            Set-DefaultAWSRegion -Region $this.Region
            
            Update-SECSecret -SecretId $secretId -SecretString $secretValue -ProfileName "TempProfile"
            return $true
        } catch {
            Write-Warning "Failed to set secret in AWS Secrets Manager: $($_.Exception.Message)"
            return $false
        }
    }
}

# Local secure storage (Windows Credential Manager)
class LocalSecureStorage {
    [string]$TargetPrefix
    
    LocalSecureStorage([string]$targetPrefix = "HatenaAgent") {
        $this.TargetPrefix = $targetPrefix
    }
    
    [string] GetSecret([string]$secretName) {
        try {
            $targetName = "$($this.TargetPrefix):$secretName"
            $credential = Get-StoredCredential -Target $targetName
            if ($credential) {
                return $credential.GetNetworkCredential().Password
            }
            return $null
        } catch {
            Write-Warning "Failed to retrieve secret from local storage: $($_.Exception.Message)"
            return $null
        }
    }
    
    [bool] SetSecret([string]$secretName, [string]$secretValue) {
        try {
            $targetName = "$($this.TargetPrefix):$secretName"
            $secureString = ConvertTo-SecureString $secretValue -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential("api-key", $secureString)
            
            # CredentialManager module required: Install-Module CredentialManager
            New-StoredCredential -Target $targetName -UserName "api-key" -Password $secretValue -Persist LocalMachine
            return $true
        } catch {
            Write-Warning "Failed to set secret in local storage: $($_.Exception.Message)"
            return $false
        }
    }
}

# Environment variable fallback
class EnvironmentSecureStorage {
    [string] GetSecret([string]$secretName) {
        return [Environment]::GetEnvironmentVariable($secretName, "Process")
    }
    
    [bool] SetSecret([string]$secretName, [string]$secretValue) {
        try {
            [Environment]::SetEnvironmentVariable($secretName, $secretValue, "Process")
            return $true
        } catch {
            return $false
        }
    }
}

# Main secret manager with fallback chain
class SecretManager {
    [System.Collections.ArrayList]$Providers
    [hashtable]$Cache
    [int]$CacheTTLSeconds
    
    SecretManager() {
        $this.Providers = New-Object System.Collections.ArrayList
        $this.Cache = @{}
        $this.CacheTTLSeconds = 300  # 5 minutes
        
        # Initialize providers based on environment
        $this.InitializeProviders()
    }
    
    [void] InitializeProviders() {
        # Azure Key Vault (if configured)
        $azureVaultName = [Environment]::GetEnvironmentVariable("AZURE_VAULT_NAME")
        $azureTenantId = [Environment]::GetEnvironmentVariable("AZURE_TENANT_ID")
        $azureClientId = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_ID")
        $azureClientSecret = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_SECRET")
        
        if ($azureVaultName -and $azureTenantId -and $azureClientId -and $azureClientSecret) {
            $azureProvider = [AzureKeyVaultManager]::new($azureVaultName, $azureTenantId, $azureClientId, $azureClientSecret)
            $this.Providers.Add($azureProvider) | Out-Null
            Write-Host "Azure Key Vault provider initialized" -ForegroundColor Green
        }
        
        # AWS Secrets Manager (if configured)
        $awsRegion = [Environment]::GetEnvironmentVariable("AWS_REGION")
        $awsAccessKeyId = [Environment]::GetEnvironmentVariable("AWS_ACCESS_KEY_ID")
        $awsSecretAccessKey = [Environment]::GetEnvironmentVariable("AWS_SECRET_ACCESS_KEY")
        
        if ($awsRegion -and $awsAccessKeyId -and $awsSecretAccessKey) {
            $awsProvider = [AWSSecretsManager]::new($awsRegion, $awsAccessKeyId, $awsSecretAccessKey)
            $this.Providers.Add($awsProvider) | Out-Null
            Write-Host "AWS Secrets Manager provider initialized" -ForegroundColor Green
        }
        
        # Local secure storage (Windows)
        if ($PSVersionTable.Platform -eq "Win32NT" -or [string]::IsNullOrEmpty($PSVersionTable.Platform)) {
            $localProvider = [LocalSecureStorage]::new()
            $this.Providers.Add($localProvider) | Out-Null
            Write-Host "Local secure storage provider initialized" -ForegroundColor Green
        }
        
        # Environment variables (always available as fallback)
        $envProvider = [EnvironmentSecureStorage]::new()
        $this.Providers.Add($envProvider) | Out-Null
        Write-Host "Environment variable provider initialized" -ForegroundColor Green
    }
    
    [string] GetSecret([string]$secretName) {
        # Check cache first
        $cacheKey = $secretName
        if ($this.Cache.ContainsKey($cacheKey)) {
            $cacheEntry = $this.Cache[$cacheKey]
            $elapsed = (Get-Date) - $cacheEntry.Timestamp
            if ($elapsed.TotalSeconds -lt $this.CacheTTLSeconds) {
                return $cacheEntry.Value
            } else {
                $this.Cache.Remove($cacheKey)
            }
        }
        
        # Try each provider in order
        foreach ($provider in $this.Providers) {
            try {
                $secret = $provider.GetSecret($secretName)
                if ($secret) {
                    # Cache the result
                    $this.Cache[$cacheKey] = @{
                        Value = $secret
                        Timestamp = Get-Date
                    }
                    
                    Write-Host "Secret '$secretName' retrieved from $($provider.GetType().Name)" -ForegroundColor Green
                    return $secret
                }
            } catch {
                Write-Warning "Provider $($provider.GetType().Name) failed: $($_.Exception.Message)"
                continue
            }
        }
        
        Write-Warning "Secret '$secretName' not found in any provider"
        return $null
    }
    
    [bool] SetSecret([string]$secretName, [string]$secretValue) {
        $success = $false
        
        # Try to set in the first available provider
        foreach ($provider in $this.Providers) {
            try {
                if ($provider.SetSecret($secretName, $secretValue)) {
                    Write-Host "Secret '$secretName' stored in $($provider.GetType().Name)" -ForegroundColor Green
                    
                    # Update cache
                    $cacheKey = $secretName
                    $this.Cache[$cacheKey] = @{
                        Value = $secretValue
                        Timestamp = Get-Date
                    }
                    
                    $success = $true
                    break
                }
            } catch {
                Write-Warning "Provider $($provider.GetType().Name) failed to set secret: $($_.Exception.Message)"
                continue
            }
        }
        
        return $success
    }
    
    [void] ClearCache() {
        $this.Cache.Clear()
        Write-Host "Secret cache cleared" -ForegroundColor Yellow
    }
    
    [hashtable] GetRequiredSecrets() {
        $requiredSecrets = @{
            "OPENAI_API_KEY" = "OpenAI API Key for chat completions"
            "BING_COOKIE" = "Bing Cookie for image generation"
            "HATENA_ID" = "Hatena Blog User ID"
            "HATENA_API_KEY" = "Hatena Blog API Key"
            "BLOG_URL" = "Hatena Blog URL"
        }
        
        return $requiredSecrets
    }
    
    [hashtable] ValidateSecrets() {
        $validation = @{}
        $requiredSecrets = $this.GetRequiredSecrets()
        
        foreach ($secretName in $requiredSecrets.Keys) {
            $secret = $this.GetSecret($secretName)
            $validation[$secretName] = @{
                Found = $secret -ne $null
                Description = $requiredSecrets[$secretName]
                Length = if ($secret) { $secret.Length } else { 0 }
            }
        }
        
        return $validation
    }
}

# Global secret manager instance
$global:SecretManager = [SecretManager]::new()

# Convenience functions
function Get-ApiSecret {
    param([string]$SecretName)
    return $global:SecretManager.GetSecret($SecretName)
}

function Set-ApiSecret {
    param([string]$SecretName, [string]$SecretValue)
    return $global:SecretManager.SetSecret($SecretName, $SecretValue)
}

function Test-ApiSecrets {
    $validation = $global:SecretManager.ValidateSecrets()
    
    Write-Host "`n=== API Secrets Validation ===" -ForegroundColor Cyan
    foreach ($secretName in $validation.Keys) {
        $info = $validation[$secretName]
        $status = if ($info.Found) { "✓ Found" } else { "✗ Missing" }
        $color = if ($info.Found) { "Green" } else { "Red" }
        
        Write-Host "$status $secretName ($($info.Description))" -ForegroundColor $color
        if ($info.Found) {
            Write-Host "  Length: $($info.Length) characters" -ForegroundColor Gray
        }
    }
    
    $missingCount = ($validation.Values | Where-Object { -not $_.Found }).Count
    if ($missingCount -eq 0) {
        Write-Host "`nAll required secrets are configured!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`n$missingCount required secrets are missing!" -ForegroundColor Red
        return $false
    }
}

function Clear-SecretCache {
    $global:SecretManager.ClearCache()
}

# Export functions for external use
Export-ModuleMember -Function Get-ApiSecret, Set-ApiSecret, Test-ApiSecrets, Clear-SecretCache