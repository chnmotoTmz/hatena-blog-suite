// Basic test script to verify MCP server functionality
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const serverPath = join(__dirname, 'dist', 'index.js');

console.log('Testing Hatena RAG MCP Server...');
console.log('Server path:', serverPath);

// Test server startup
const server = spawn('node', [serverPath], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Test initialization message
const initMessage = {
  jsonrpc: '2.0',
  id: 1,
  method: 'initialize',
  params: {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: {
      name: 'test-client',
      version: '1.0.0'
    }
  }
};

// Test tools list
const toolsMessage = {
  jsonrpc: '2.0',
  id: 2,
  method: 'tools/list'
};

let messageId = 0;

function sendMessage(message) {
  messageId++;
  const msg = JSON.stringify(message) + '\n';
  console.log('Sending:', msg.trim());
  server.stdin.write(msg);
}

server.stdout.on('data', (data) => {
  console.log('Server response:', data.toString());
});

server.stderr.on('data', (data) => {
  console.error('Server error:', data.toString());
});

server.on('close', (code) => {
  console.log(`Server process exited with code ${code}`);
});

// Send test messages
setTimeout(() => {
  sendMessage(initMessage);
}, 100);

setTimeout(() => {
  sendMessage(toolsMessage);
}, 500);

// Cleanup after 3 seconds
setTimeout(() => {
  server.kill();
}, 3000);