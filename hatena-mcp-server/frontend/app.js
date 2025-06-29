// Hatena Agent v2 - Cloud Dashboard JavaScript
// MCP対応 多重エージェント会話システム

class HatenaAgentDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8080/api';
        this.mcpTools = [];
        this.chatHistory = [];
        this.agents = [
            'article_extractor',
            'retrieval_agent', 
            'image_generator',
            'affiliate_manager',
            'knowledge_network',
            'personalization_agent',
            'link_checker',
            'repost_manager'
        ];
        
        this.init();
    }

    init() {
        this.addLog('ダッシュボード初期化中...');
        this.refreshAgentStatus();
        this.loadMcpTools();
        
        // 定期的な状態更新
        setInterval(() => this.refreshAgentStatus(), 30000);
        
        this.addLog('ダッシュボード準備完了');
    }

    async refreshAgentStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/status`);
            const status = await response.json();
            
            this.updateSystemStatus(status);
            this.updateAgentGrid(status.agents);
            
            document.getElementById('statusIndicator').style.background = '#27ae60';
            document.getElementById('apiStatus').textContent = '正常';
            
        } catch (error) {
            console.error('Status check failed:', error);
            document.getElementById('statusIndicator').style.background = '#e74c3c';
            document.getElementById('apiStatus').textContent = '接続エラー';
            this.addLog(`状態確認エラー: ${error.message}`);
        }
    }

    updateSystemStatus(status) {
        if (status.mcp_server) {
            document.getElementById('mcpStatus').textContent = 
                status.mcp_server.status === 'running' ? '実行中' : '停止中';
        }
        
        if (status.system) {
            const uptime = status.system.uptime;
            document.getElementById('uptime').textContent = 
                `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m`;
            document.getElementById('memoryUsage').textContent = 
                `${status.system.memory_usage} MB`;
        }
    }

    updateAgentGrid(agents) {
        const grid = document.getElementById('agentGrid');
        grid.innerHTML = '';
        
        Object.entries(agents).forEach(([name, info]) => {
            const card = document.createElement('div');
            card.className = `agent-card ${info.status}`;
            card.onclick = () => this.runAgent(name);
            
            const displayName = this.getAgentDisplayName(name);
            const icon = this.getAgentIcon(name);
            
            card.innerHTML = `
                <div style="font-size: 24px; margin-bottom: 10px;">
                    <i class="${icon}"></i>
                </div>
                <div style="font-weight: bold; margin-bottom: 5px;">${displayName}</div>
                <div style="font-size: 12px; opacity: 0.9;">${info.status}</div>
            `;
            
            grid.appendChild(card);
        });
    }

    getAgentDisplayName(name) {
        const names = {
            'article_extractor': '記事抽出',
            'retrieval_agent': 'RAG検索',
            'image_generator': '画像生成',
            'affiliate_manager': 'アフィリエイト',
            'knowledge_network': 'ナレッジマップ',
            'personalization_agent': 'パーソナライズ',
            'link_checker': 'リンクチェック',
            'repost_manager': '再投稿管理'
        };
        return names[name] || name;
    }

    getAgentIcon(name) {
        const icons = {
            'article_extractor': 'fas fa-newspaper',
            'retrieval_agent': 'fas fa-search',
            'image_generator': 'fas fa-image',
            'affiliate_manager': 'fas fa-shopping-cart',
            'knowledge_network': 'fas fa-project-diagram',
            'personalization_agent': 'fas fa-user-cog',
            'link_checker': 'fas fa-link',
            'repost_manager': 'fas fa-share-alt'
        };
        return icons[name] || 'fas fa-robot';
    }

    async runAgent(agentName) {
        try {
            this.addLog(`エージェント実行中: ${this.getAgentDisplayName(agentName)}`);
            
            const response = await fetch(`${this.apiBaseUrl}/agents/${agentName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    args: []
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.addLog(`エージェント完了: ${this.getAgentDisplayName(agentName)}`);
                this.addChatMessage('system', `${this.getAgentDisplayName(agentName)}が実行されました。`);
                
                if (result.output) {
                    this.addChatMessage('assistant', result.output);
                }
            } else {
                throw new Error(result.error || 'エージェント実行エラー');
            }
            
        } catch (error) {
            console.error('Agent execution failed:', error);
            this.addLog(`エージェントエラー: ${error.message}`);
            this.addChatMessage('system', `エラー: ${error.message}`);
        }
    }

    async loadMcpTools() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/mcp/tools`);
            const data = await response.json();
            
            this.mcpTools = data.tools || [];
            this.addLog(`MCPツール読み込み完了: ${this.mcpTools.length}個のツール`);
            
        } catch (error) {
            console.error('Failed to load MCP tools:', error);
            this.addLog(`MCPツール読み込みエラー: ${error.message}`);
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // ユーザーメッセージを追加
        this.addChatMessage('user', message);
        this.chatHistory.push({ role: 'user', content: message });
        
        input.value = '';
        this.setLoading(true);
        
        try {
            // MCP tools を含めたシステムプロンプト
            const systemMessage = {
                role: 'system',
                content: `あなたはHatena Agent v2のAIアシスタントです。以下のMCPツールを利用できます：
${this.mcpTools.map(tool => `- ${tool.name}: ${tool.description}`).join('\n')}

ユーザーのリクエストに応じて適切なツールを提案し、エージェントの実行をサポートしてください。`
            };
            
            const messages = [systemMessage, ...this.chatHistory];
            
            const response = await fetch(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'gpt-4',
                    messages: messages,
                    temperature: 0.7,
                    max_tokens: 2000
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.choices && result.choices[0]) {
                const assistantMessage = result.choices[0].message.content;
                this.addChatMessage('assistant', assistantMessage);
                this.chatHistory.push({ role: 'assistant', content: assistantMessage });
            } else {
                throw new Error(result.error || 'API応答エラー');
            }
            
        } catch (error) {
            console.error('Chat API failed:', error);
            this.addChatMessage('system', `エラー: ${error.message}`);
            this.addLog(`チャットエラー: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }

    addChatMessage(role, content) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        if (role === 'user') {
            messageDiv.innerHTML = `<strong>あなた:</strong> ${this.escapeHtml(content)}`;
        } else if (role === 'assistant') {
            messageDiv.innerHTML = `<strong>AI:</strong> ${this.formatMessage(content)}`;
        } else {
            messageDiv.innerHTML = `<strong>システム:</strong> ${this.escapeHtml(content)}`;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // 簡単なマークダウン形式の変換
        content = this.escapeHtml(content);
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        content = content.replace(/`(.*?)`/g, '<code>$1</code>');
        content = content.replace(/\n/g, '<br>');
        return content;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setLoading(loading) {
        const sendButton = document.getElementById('sendButton');
        const chatInput = document.getElementById('chatInput');
        
        sendButton.disabled = loading;
        chatInput.disabled = loading;
        
        if (loading) {
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 送信中...';
        } else {
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> 送信';
        }
    }

    addLog(message) {
        const logContent = document.getElementById('logContent');
        const timestamp = new Date().toLocaleTimeString('ja-JP');
        logContent.innerHTML += `[${timestamp}] ${message}<br>`;
        logContent.scrollTop = logContent.scrollHeight;
    }

    clearChat() {
        document.getElementById('chatMessages').innerHTML = '';
        this.chatHistory = [];
        this.addLog('チャット履歴をクリアしました');
    }

    exportChat() {
        const chatData = {
            timestamp: new Date().toISOString(),
            messages: this.chatHistory
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hatena-agent-chat-${Date.now()}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.addLog('チャット履歴をエクスポートしました');
    }

    showMcpTools() {
        if (this.mcpTools.length === 0) {
            alert('MCPツールが見つかりません。');
            return;
        }
        
        const toolsInfo = this.mcpTools.map(tool => 
            `• ${tool.name}: ${tool.description}`
        ).join('\n');
        
        alert(`利用可能なMCPツール:\n\n${toolsInfo}`);
    }

    toggleAllAgents() {
        // この機能は実装が複雑なため、現在は alertで代替
        alert('全エージェント制御機能は開発中です。個別のエージェントカードをクリックして実行してください。');
    }
}

// グローバル関数（HTMLから呼び出し用）
let dashboard;

function refreshAgentStatus() {
    dashboard.refreshAgentStatus();
}

function clearChat() {
    dashboard.clearChat();
}

function exportChat() {
    dashboard.exportChat();
}

function showMcpTools() {
    dashboard.showMcpTools();
}

function toggleAllAgents() {
    dashboard.toggleAllAgents();
}

function sendMessage() {
    dashboard.sendMessage();
}

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new HatenaAgentDashboard();
});