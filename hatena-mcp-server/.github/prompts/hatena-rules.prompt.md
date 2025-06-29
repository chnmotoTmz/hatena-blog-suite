# Hatena Blog Specific Rules

## API Handling

1. Always use rate limiting when making API calls
2. Include retry logic for failed requests
3. Cache API responses when appropriate
4. Use proper error handling for API-specific errors

## Blog Post Format

1. Always include proper metadata for posts
2. Format code blocks with appropriate syntax highlighting
3. Handle image uploads with proper alt text
4. Support both draft and published states

## Integration Rules

1. Proper error handling for Hatena API responses
2. Support for custom categories and tags
3. Handle UTF-8 encoding properly
4. Maintain proper timestamp handling between systems

## Testing

1. Mock all API calls in tests
2. Include test cases for both success and failure scenarios
3. Test Japanese character handling
4. Verify proper HTML escaping
