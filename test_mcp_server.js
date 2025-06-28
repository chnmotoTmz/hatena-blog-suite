#!/usr/bin/env node
/**
 * MCP Server Test Suite
 */

const UnifiedMCPServer = require('./mcp/unified-server.js');
const assert = require('assert');

class MCPServerTester {
  constructor() {
    this.server = new UnifiedMCPServer();
    this.testResults = [];
  }

  async runTest(name, testFn) {
    try {
      console.log(`🗺 Testing: ${name}`);
      await testFn();
      console.log(`✅ ${name}: PASSED`);
      this.testResults.push({ name, status: 'PASSED' });
    } catch (error) {
      console.log(`❌ ${name}: FAILED - ${error.message}`);
      this.testResults.push({ name, status: 'FAILED', error: error.message });
    }
  }

  async testExtractArticles() {
    // Mock request
    const mockRequest = {
      params: {
        name: 'extract_articles',
        arguments: {
          blog_id: 'test-blog',
          max_pages: 1,
          extract_content: false
        }
      }
    };

    // This would test actual extraction in real scenario
    // For now, just test structure
    assert(typeof this.server.extractArticles === 'function');
  }

  async testEnhanceArticles() {
    const sampleArticles = [
      {
        title: 'Test Article',
        content: 'Sample content with amazon.com link',
        url: 'https://test.com/entry/1'
      }
    ];

    const result = await this.server.enhanceArticles({
      articles: sampleArticles,
      options: { affiliate: true, amazon_tag: 'test-tag' }
    });

    assert(result.content);
    assert(result.content[0].text.includes('拡張完了'));
  }

  async testAnalyzePerformance() {
    const sampleArticles = [
      {
        title: 'Test Article 1',
        word_count: 100,
        categories: ['Tech']
      },
      {
        title: 'Test Article 2', 
        word_count: 200,
        categories: ['Tech', 'Programming']
      }
    ];

    const result = await this.server.analyzePerformance({ articles: sampleArticles });
    
    assert(result.content);
    const response = result.content[0].text;
    assert(response.includes('分析完了'));
    assert(response.includes('total_articles'));
  }

  async testGenerateRepostPlan() {
    const sampleArticles = [
      {
        title: 'High Score Article',
        word_count: 500,
        links: [{}, {}, {}], // 3 links
        categories: ['Tech', 'AI']
      },
      {
        title: 'Low Score Article',
        word_count: 100,
        links: [],
        categories: ['Misc']
      }
    ];

    const result = await this.server.generateRepostPlan({ 
      articles: sampleArticles, 
      weeks: 2 
    });
    
    assert(result.content);
    const response = result.content[0].text;
    assert(response.includes('リポスト計画生成完了'));
  }

  async testSearchArticles() {
    const sampleArticles = [
      {
        title: 'JavaScript Tutorial',
        content: 'Learn JavaScript programming',
        url: 'https://test.com/js'
      },
      {
        title: 'Python Guide',
        content: 'Python programming basics',
        url: 'https://test.com/python'
      }
    ];

    const result = await this.server.searchArticles({
      query: 'JavaScript',
      articles: sampleArticles
    });
    
    assert(result.content);
    const response = result.content[0].text;
    assert(response.includes('検索結果'));
    assert(response.includes('JavaScript Tutorial'));
  }

  async testExportData() {
    const sampleArticles = [
      { title: 'Article 1', url: 'https://test.com/1', word_count: 100 },
      { title: 'Article 2', url: 'https://test.com/2', word_count: 200 }
    ];

    // Test JSON export
    const jsonResult = await this.server.exportData({
      articles: sampleArticles,
      format: 'json'
    });
    
    assert(jsonResult.content);
    assert(jsonResult.content[0].text.includes('エクスポート完了'));

    // Test CSV export
    const csvResult = await this.server.exportData({
      articles: sampleArticles,
      format: 'csv'
    });
    
    assert(csvResult.content);
    assert(csvResult.content[0].text.includes('Article 1'));
  }

  async testCacheSystem() {
    // Test that cache is working
    const args = { blog_id: 'test-cache', max_pages: 1 };
    
    // First call - should cache
    this.server.cache.set('test_key', { cached: true });
    
    // Verify cache exists
    assert(this.server.cache.has('test_key'));
    
    const cached = this.server.cache.get('test_key');
    assert(cached.cached === true);
  }

  async runAllTests() {
    console.log('🗺 MCP Server Test Suite');
    console.log('='.repeat(50));

    await this.runTest('Extract Articles Structure', () => this.testExtractArticles());
    await this.runTest('Enhance Articles', () => this.testEnhanceArticles());
    await this.runTest('Analyze Performance', () => this.testAnalyzePerformance());
    await this.runTest('Generate Repost Plan', () => this.testGenerateRepostPlan());
    await this.runTest('Search Articles', () => this.testSearchArticles());
    await this.runTest('Export Data (JSON/CSV)', () => this.testExportData());
    await this.runTest('Cache System', () => this.testCacheSystem());

    // Summary
    console.log('\n📊 Test Results Summary');
    console.log('='.repeat(30));
    
    const passed = this.testResults.filter(r => r.status === 'PASSED').length;
    const failed = this.testResults.filter(r => r.status === 'FAILED').length;
    
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📊 Total: ${this.testResults.length}`);
    
    if (failed > 0) {
      console.log('\n❌ Failed Tests:');
      this.testResults
        .filter(r => r.status === 'FAILED')
        .forEach(r => console.log(`  - ${r.name}: ${r.error}`));
    } else {
      console.log('\n🎉 All tests PASSED!');
    }
    
    return failed === 0;
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new MCPServerTester();
  tester.runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('👥 Test suite crashed:', error);
    process.exit(1);
  });
}

module.exports = MCPServerTester;