# PowerShell REST API Server for Hatena Agent v2
# Cloud Desktop & Cloud Code Compatible

param(
    [int]$Port = 8080,
    [string]$Host = "localhost"
)

# Import required modules
Add-Type -AssemblyName System.Web

# Configuration
$script:Config = @{
    Port = $Port
    Host = $Host
    ApiKeys = @{}
    AllowedOrigins = @("http://localhost", "https://localhost", "https://*.github.io")
}

# Load secure API key management
. "$PSScriptRoot/../config/secrets.ps1"

# Load environment variables for API keys
function Load-Environment {
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                $script:Config.ApiKeys[$name] = $value
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
    
    # Load secrets using secure secret manager
    $requiredSecrets = @("OPENAI_API_KEY", "BING_COOKIE", "HATENA_ID", "HATENA_API_KEY", "BLOG_URL")
    foreach ($secretName in $requiredSecrets) {
        $secretValue = Get-ApiSecret -SecretName $secretName
        if ($secretValue) {
            $script:Config.ApiKeys[$secretName] = $secretValue
            [Environment]::SetEnvironmentVariable($secretName, $secretValue, "Process")
        }
    }
}

# Security and rate limiting
$script:RateLimitStore = @{}
$script:SecurityConfig = @{
    MaxRequestsPerMinute = 60
    MaxRequestsPerHour = 1000
    RequireApiKey = $false
    ValidApiKeys = @()
    BlockedIPs = @()
    AllowedUserAgents = @("*")
}

# Rate limiting function
function Test-RateLimit {
    param($ClientIP)
    
    $currentTime = Get-Date
    $minuteKey = "$ClientIP-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')"
    $hourKey = "$ClientIP-$(Get-Date -Format 'yyyy-MM-dd-HH')"
    
    # Check minute limit
    if ($script:RateLimitStore.ContainsKey($minuteKey)) {
        $script:RateLimitStore[$minuteKey]++
    } else {
        $script:RateLimitStore[$minuteKey] = 1
    }
    
    # Check hour limit
    if ($script:RateLimitStore.ContainsKey($hourKey)) {
        $script:RateLimitStore[$hourKey]++
    } else {
        $script:RateLimitStore[$hourKey] = 1
    }
    
    # Clean old entries
    $script:RateLimitStore.Keys | Where-Object { $_ -match '\d{4}-\d{2}-\d{2}-\d{2}-\d{2}$' } | ForEach-Object {
        $entryTime = [DateTime]::ParseExact($_.Split('-')[1..4] -join '-', 'yyyy-MM-dd-HH-mm', $null)
        if ((Get-Date) - $entryTime > [TimeSpan]::FromMinutes(5)) {
            $script:RateLimitStore.Remove($_)
        }
    }
    
    # Check limits
    if ($script:RateLimitStore[$minuteKey] -gt $script:SecurityConfig.MaxRequestsPerMinute) {
        return @{ Allowed = $false; Reason = "Rate limit exceeded: $($script:SecurityConfig.MaxRequestsPerMinute) requests per minute" }
    }
    
    if ($script:RateLimitStore[$hourKey] -gt $script:SecurityConfig.MaxRequestsPerHour) {
        return @{ Allowed = $false; Reason = "Rate limit exceeded: $($script:SecurityConfig.MaxRequestsPerHour) requests per hour" }
    }
    
    return @{ Allowed = $true; Reason = "" }
}

# Security validation
function Test-SecurityConstraints {
    param($Request)
    
    $clientIP = $Request.RemoteEndPoint.Address.ToString()
    $userAgent = $Request.Headers["User-Agent"]
    
    # Check blocked IPs
    if ($clientIP -in $script:SecurityConfig.BlockedIPs) {
        return @{ Allowed = $false; Reason = "IP address blocked" }
    }
    
    # Check rate limits
    $rateLimitResult = Test-RateLimit -ClientIP $clientIP
    if (-not $rateLimitResult.Allowed) {
        return $rateLimitResult
    }
    
    # Check API key if required
    if ($script:SecurityConfig.RequireApiKey) {
        $apiKey = $Request.Headers["X-API-Key"]
        if (-not $apiKey -or $apiKey -notin $script:SecurityConfig.ValidApiKeys) {
            return @{ Allowed = $false; Reason = "Invalid or missing API key" }
        }
    }
    
    # Check User-Agent
    $allowedUserAgents = $script:SecurityConfig.AllowedUserAgents
    if ($allowedUserAgents -notcontains "*" -and $userAgent) {
        $userAgentAllowed = $false
        foreach ($pattern in $allowedUserAgents) {
            if ($userAgent -like $pattern) {
                $userAgentAllowed = $true
                break
            }
        }
        if (-not $userAgentAllowed) {
            return @{ Allowed = $false; Reason = "User-Agent not allowed" }
        }
    }
    
    return @{ Allowed = $true; Reason = "" }
}

# Enhanced CORS handling
function Set-CorsHeaders {
    param($Response, $Origin)
    
    # Determine allowed origin
    $allowedOrigin = "*"
    if ($Origin) {
        foreach ($allowed in $script:Config.AllowedOrigins) {
            if ($Origin -like $allowed) {
                $allowedOrigin = $Origin
                break
            }
        }
        
        # If no match found, check if it's localhost or a secure origin
        if ($allowedOrigin -eq "*" -and ($Origin -like "http://localhost*" -or $Origin -like "https://*")) {
            $allowedOrigin = $Origin
        }
    }
    
    # Set CORS headers
    $Response.Headers.Add("Access-Control-Allow-Origin", $allowedOrigin)
    $Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    $Response.Headers.Add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-API-Key")
    $Response.Headers.Add("Access-Control-Max-Age", "86400")
    $Response.Headers.Add("Access-Control-Allow-Credentials", "false")
    
    # Security headers
    $Response.Headers.Add("X-Content-Type-Options", "nosniff")
    $Response.Headers.Add("X-Frame-Options", "DENY")
    $Response.Headers.Add("X-XSS-Protection", "1; mode=block")
    $Response.Headers.Add("Referrer-Policy", "strict-origin-when-cross-origin")
    $Response.Headers.Add("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
}

# JSON response helper
function Send-JsonResponse {
    param($Response, $Data, $StatusCode = 200)
    
    $Response.StatusCode = $StatusCode
    $Response.ContentType = "application/json; charset=utf-8"
    
    $jsonData = $Data | ConvertTo-Json -Depth 10 -Compress
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($jsonData)
    $Response.ContentLength64 = $buffer.Length
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $Response.OutputStream.Close()
}

# Error response helper
function Send-ErrorResponse {
    param($Response, $Message, $StatusCode = 500)
    
    $errorData = @{
        error = $Message
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    Send-JsonResponse -Response $Response -Data $errorData -StatusCode $StatusCode
}

# Chat API endpoint
function Invoke-ChatApi {
    param($Request, $Response)
    
    try {
        # Read request body
        $reader = New-Object System.IO.StreamReader($Request.InputStream)
        $requestBody = $reader.ReadToEnd()
        $reader.Close()
        
        $requestData = $requestBody | ConvertFrom-Json
        
        # Validate required fields
        if (-not $requestData.messages) {
            Send-ErrorResponse -Response $Response -Message "Missing 'messages' field" -StatusCode 400
            return
        }
        
        # Prepare OpenAI API request
        $openaiUrl = "https://api.openai.com/v1/chat/completions"
        $apiKey = $script:Config.ApiKeys["OPENAI_API_KEY"]
        
        if (-not $apiKey) {
            Send-ErrorResponse -Response $Response -Message "OpenAI API key not configured" -StatusCode 500
            return
        }
        
        $headers = @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        }
        
        $body = @{
            model = $requestData.model ?? "gpt-4"
            messages = $requestData.messages
            temperature = $requestData.temperature ?? 0.7
            max_tokens = $requestData.max_tokens ?? 2000
        } | ConvertTo-Json -Depth 10
        
        # Call OpenAI API
        $result = Invoke-RestMethod -Uri $openaiUrl -Method POST -Headers $headers -Body $body
        
        # Return response
        Send-JsonResponse -Response $Response -Data $result
        
    } catch {
        Write-Host "Error in Chat API: $($_.Exception.Message)" -ForegroundColor Red
        Send-ErrorResponse -Response $Response -Message $_.Exception.Message
    }
}

# MCP Tools endpoint
function Invoke-McpTools {
    param($Request, $Response)
    
    try {
        # Get available MCP tools from the Node.js server
        $mcpUrl = "http://localhost:3000/tools"
        
        try {
            $tools = Invoke-RestMethod -Uri $mcpUrl -Method GET -TimeoutSec 5
            Send-JsonResponse -Response $Response -Data $tools
        } catch {
            # Fallback to static tool list if MCP server is not available
            $fallbackTools = @{
                tools = @(
                    @{
                        name = "extract_hatena_articles"
                        description = "Extract articles from Hatena blog archives"
                        parameters = @{
                            blog_url = "string"
                            max_pages = "number"
                        }
                    },
                    @{
                        name = "search_article_content"
                        description = "Search through extracted article content"
                        parameters = @{
                            query = "string"
                            limit = "number"
                        }
                    },
                    @{
                        name = "retrieve_related_articles"
                        description = "Get semantically related articles using RAG"
                        parameters = @{
                            query = "string"
                            limit = "number"
                        }
                    }
                )
            }
            Send-JsonResponse -Response $Response -Data $fallbackTools
        }
        
    } catch {
        Write-Host "Error in MCP Tools: $($_.Exception.Message)" -ForegroundColor Red
        Send-ErrorResponse -Response $Response -Message $_.Exception.Message
    }
}

# Agent status endpoint
function Get-AgentStatus {
    param($Request, $Response)
    
    try {
        $status = @{
            agents = @{
                article_extractor = @{ status = "available"; last_run = $null }
                retrieval_agent = @{ status = "available"; last_run = $null }
                image_generator = @{ status = "available"; last_run = $null }
                affiliate_manager = @{ status = "available"; last_run = $null }
                knowledge_network = @{ status = "available"; last_run = $null }
                personalization_agent = @{ status = "available"; last_run = $null }
                link_checker = @{ status = "available"; last_run = $null }
                repost_manager = @{ status = "available"; last_run = $null }
            }
            mcp_server = @{ 
                status = if (Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet) { "running" } else { "stopped" }
            }
            system = @{
                uptime = (Get-Date) - (Get-Process -Id $PID).StartTime
                memory_usage = [Math]::Round((Get-Process -Id $PID).WorkingSet64 / 1MB, 2)
            }
        }
        
        Send-JsonResponse -Response $Response -Data $status
        
    } catch {
        Write-Host "Error getting agent status: $($_.Exception.Message)" -ForegroundColor Red
        Send-ErrorResponse -Response $Response -Message $_.Exception.Message
    }
}

# Run agent endpoint
function Invoke-Agent {
    param($Request, $Response)
    
    try {
        # Extract agent name from URL
        $urlParts = $Request.Url.AbsolutePath.Split('/')
        $agentName = $urlParts[-1]
        
        # Read request body
        $reader = New-Object System.IO.StreamReader($Request.InputStream)
        $requestBody = $reader.ReadToEnd()
        $reader.Close()
        
        $requestData = if ($requestBody) { $requestBody | ConvertFrom-Json } else { @{} }
        
        # Execute Python agent
        $pythonScript = "python src/agents/$agentName.py"
        
        if ($requestData.args) {
            $args = $requestData.args -join " "
            $pythonScript += " $args"
        }
        
        Write-Host "Executing: $pythonScript" -ForegroundColor Green
        
        $result = Invoke-Expression $pythonScript 2>&1
        
        $response = @{
            agent = $agentName
            output = $result
            timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        }
        
        Send-JsonResponse -Response $Response -Data $response
        
    } catch {
        Write-Host "Error running agent: $($_.Exception.Message)" -ForegroundColor Red
        Send-ErrorResponse -Response $Response -Message $_.Exception.Message
    }
}

# Main request handler
function Handle-Request {
    param($Request, $Response)
    
    $origin = $Request.Headers["Origin"]
    $clientIP = $Request.RemoteEndPoint.Address.ToString()
    $userAgent = $Request.Headers["User-Agent"]
    
    # Security checks
    $securityResult = Test-SecurityConstraints -Request $Request
    if (-not $securityResult.Allowed) {
        Write-Host "Security violation from $clientIP`: $($securityResult.Reason)" -ForegroundColor Red
        Set-CorsHeaders -Response $Response -Origin $origin
        Send-ErrorResponse -Response $Response -Message $securityResult.Reason -StatusCode 429
        return
    }
    
    Set-CorsHeaders -Response $Response -Origin $origin
    
    # Handle preflight requests
    if ($Request.HttpMethod -eq "OPTIONS") {
        $Response.StatusCode = 200
        $Response.Close()
        return
    }
    
    $path = $Request.Url.AbsolutePath
    $method = $Request.HttpMethod
    
    Write-Host "$method $path from $clientIP" -ForegroundColor Cyan
    
    try {
        switch -Regex ($path) {
            "^/api/chat$" {
                if ($method -eq "POST") {
                    Invoke-ChatApi -Request $Request -Response $Response
                } else {
                    Send-ErrorResponse -Response $Response -Message "Method not allowed" -StatusCode 405
                }
            }
            "^/api/mcp/tools$" {
                if ($method -eq "GET") {
                    Invoke-McpTools -Request $Request -Response $Response
                } else {
                    Send-ErrorResponse -Response $Response -Message "Method not allowed" -StatusCode 405
                }
            }
            "^/api/status$" {
                if ($method -eq "GET") {
                    Get-AgentStatus -Request $Request -Response $Response
                } else {
                    Send-ErrorResponse -Response $Response -Message "Method not allowed" -StatusCode 405
                }
            }
            "^/api/agents/\w+$" {
                if ($method -eq "POST") {
                    Invoke-Agent -Request $Request -Response $Response
                } else {
                    Send-ErrorResponse -Response $Response -Message "Method not allowed" -StatusCode 405
                }
            }
            default {
                Send-ErrorResponse -Response $Response -Message "Not found" -StatusCode 404
            }
        }
    } catch {
        Write-Host "Unhandled error: $($_.Exception.Message)" -ForegroundColor Red
        Send-ErrorResponse -Response $Response -Message "Internal server error"
    }
}

# Start server
function Start-ApiServer {
    # Load environment variables
    Load-Environment
    
    # Create HTTP listener
    $listener = New-Object System.Net.HttpListener
    $prefix = "http://$($script:Config.Host):$($script:Config.Port)/"
    $listener.Prefixes.Add($prefix)
    
    try {
        $listener.Start()
        Write-Host "PowerShell API Server started at $prefix" -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        
        # Handle requests
        while ($listener.IsListening) {
            try {
                $context = $listener.GetContext()
                $request = $context.Request
                $response = $context.Response
                
                Handle-Request -Request $request -Response $response
                
            } catch [System.Management.Automation.PipelineStoppedException] {
                break
            } catch {
                Write-Host "Error handling request: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        if ($listener.IsListening) {
            $listener.Stop()
        }
        Write-Host "Server stopped" -ForegroundColor Yellow
    }
}

# Start the server
Start-ApiServer