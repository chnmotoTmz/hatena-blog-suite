# 🎌 Hatena Multi-Blog System - Deployment Guide

## 📋 Implementation Summary

### ✅ Completed Features

1. **Multi-Blog Support**
   - `multi_blog_manager.py` - Handles multiple blog configurations
   - Support for 3 blogs: lifehack_blog, mountain_blog, tech_blog
   - Individual API key management per blog

2. **Fixed Authentication**
   - Proper WSSE header generation
   - Content-Type headers fixed
   - Timeout handling added

3. **Article Migration System**
   - Copy/move articles between blogs
   - Automatic migration notes
   - Batch migration support
   - Category preservation

4. **Enhanced Agent Interface**
   - `enhanced_hatena_agent.py` - Main interface
   - Search functionality
   - Migration candidate detection
   - Error handling and logging

## 🔧 Configuration Setup

### Environment Variables (.env)
```bash
# Primary API keys for multi-blog support
HATENA_BLOG_ATOMPUB_KEY_1=your_primary_key
HATENA_BLOG_ATOMPUB_KEY_2=your_secondary_key

# Legacy compatibility
HATENA_ID=motochan1969
BLOG_DOMAIN=arafo40tozan.hatenadiary.jp
```

### Blog Configuration
The system is pre-configured for:

1. **lifehack_blog**
   - Domain: motochan1969.hatenadiary.jp
   - Description: ライフハックブログ
   - API Key: HATENA_BLOG_ATOMPUB_KEY_1

2. **mountain_blog** 
   - Domain: arafo40tozan.hatenadiary.jp
   - Description: 登山ブログ
   - API Key: HATENA_BLOG_ATOMPUB_KEY_2

3. **tech_blog**
   - Domain: motochan1969.hatenablog.com
   - Description: 技術ブログ
   - API Key: HATENA_BLOG_ATOMPUB_KEY_1

## 🚀 Quick Start

### 1. Basic Usage
```python
from enhanced_hatena_agent import EnhancedHatenaAgent

agent = EnhancedHatenaAgent()

# List all configured blogs
blogs = agent.list_blogs()

# Test authentication
auth_status = agent.test_blog_authentication()

# Get articles from a blog
articles = agent.get_articles('lifehack_blog', limit=10)
```

### 2. Article Migration
```python
# Search for outdoor articles in lifehack_blog
candidates = agent.get_migration_candidates('lifehack_blog')

# Migrate specific article
result = agent.migrate_article(
    source_blog='lifehack_blog',
    target_blog='mountain_blog', 
    article_id='article_id_here',
    copy_mode=True  # Safe copy, keeps original
)
```

### 3. Batch Operations
```python
# Migrate multiple articles
article_ids = ['id1', 'id2', 'id3']
batch_result = agent.batch_migrate_articles(
    source_blog='lifehack_blog',
    target_blog='mountain_blog',
    article_ids=article_ids,
    copy_mode=True
)
```

## 🔍 Troubleshooting Authentication Issues

### Common Error Solutions

#### 404 Not Found
- **Cause**: Incorrect blog domain in configuration
- **Solution**: Verify blog domain matches exactly
- **Check**: Blog exists and is accessible

#### 401 Unauthorized  
- **Cause**: Invalid API key or incorrect WSSE generation
- **Solution**: 
  1. Verify API key in Hatena Blog settings
  2. Check environment variable names
  3. Ensure WSSE timestamp is correct

#### Fix Verification
```python
# Test individual blog authentication
agent = EnhancedHatenaAgent()
result = agent.test_blog_authentication('mountain_blog')
print(result)
```

## 📊 Migration Workflow

### Step 1: Identify Articles
```python
# Find articles about outdoor activities
candidates = agent.get_migration_candidates('lifehack_blog')

# Search by title keywords
outdoor_articles = agent.search_articles_by_title('lifehack_blog', '登山')
```

### Step 2: Review and Migrate
```python
# Migrate with review (as draft)
for article in outdoor_articles['articles']:
    result = agent.migrate_article(
        source_blog='lifehack_blog',
        target_blog='mountain_blog',
        article_id=article['id'],
        copy_mode=True  # Safe copy
    )
    if result['status'] == 'success':
        print(f"✅ Migrated: {article['title']}")
    else:
        print(f"❌ Failed: {result['message']}")
```

### Step 3: Verify Migration
- All migrated articles are posted as **drafts**
- Review content in target blog dashboard
- Publish manually after verification
- Original articles remain in source blog (copy_mode=True)

## 🎯 Next Steps for Full Deployment

### 1. Windows Environment Setup
Since you mentioned the clean version is at `C:\Users\motoc\hatena-agent\hatena-mcp-server-clean`:

1. Copy these new files to Windows environment:
   - `multi_blog_manager.py`
   - `enhanced_hatena_agent.py` 
   - `.env` (with real API keys)
   - `test_multi_blog.py`

2. Install dependencies:
   ```bash
   pip install python-dotenv requests
   ```

3. Test authentication:
   ```bash
   python test_multi_blog.py
   ```

### 2. API Key Verification
Ensure you have valid API keys from:
- Hatena Blog → Settings → AtomPub
- Copy the API key for each blog domain

### 3. Migration Process
1. Start with `copy_mode=True` for safety
2. Test with 1-2 articles first
3. Review migrated content
4. Scale up to batch migration

## 🔧 Integration with Existing Tools

The new multi-blog system is compatible with:
- Existing `hatena_agent.py` (legacy mode)
- MCP server integration
- Article enhancement tools
- Image generation systems

## 📞 Support

If you encounter issues:
1. Check authentication with `test_blog_authentication()`
2. Verify blog domains and API keys
3. Review logs for specific error messages
4. Test with simple article retrieval first

---
**Status**: ✅ Ready for deployment and testing
**Priority**: Test authentication → Migrate test articles → Full migration