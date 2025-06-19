#!/usr/bin/env python3
"""
Comprehensive chat troubleshooting script for PHRM
"""

import os
import sys
import requests
import json
import re
from datetime import datetime

def load_env_file():
    """Load environment variables from .env file"""
    env_path = '/home/em/code/wip/phrm/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded from .env file")
    else:
        print("❌ .env file not found")

def check_api_keys():
    """Check if AI API keys are configured"""
    print("🔑 Checking API Keys:")
    
    keys_to_check = {
        'HUGGINGFACE_ACCESS_TOKEN': 'HuggingFace',
        'GROQ_API_KEY': 'GROQ',
        'DEEPSEEK_API_KEY': 'DeepSeek'
    }
    
    configured_keys = 0
    for env_key, provider in keys_to_check.items():
        value = os.environ.get(env_key)
        if value and value.strip():
            print(f"   ✅ {provider}: {value[:15]}...")
            configured_keys += 1
        else:
            print(f"   ❌ {provider}: Not configured")
    
    return configured_keys > 0

def test_ai_providers():
    """Test each AI provider individually"""
    print("🤖 Testing AI Providers:")
    
    results = {}
    
    # Test HuggingFace
    hf_token = os.environ.get('HUGGINGFACE_ACCESS_TOKEN')
    if hf_token:
        try:
            url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            headers = {"Authorization": f"Bearer {hf_token}"}
            payload = {"inputs": "Hello, test message"}
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("   ✅ HuggingFace API: Working")
                results['huggingface'] = True
            else:
                print(f"   ❌ HuggingFace API: Failed ({response.status_code})")
                results['huggingface'] = False
        except Exception as e:
            print(f"   ❌ HuggingFace API: Error - {e}")
            results['huggingface'] = False
    else:
        print("   ⚠️  HuggingFace API: No token configured")
        results['huggingface'] = False
    
    # Test GROQ
    groq_key = os.environ.get('GROQ_API_KEY')
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}"}
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("   ✅ GROQ API: Working")
                results['groq'] = True
            else:
                print(f"   ❌ GROQ API: Failed ({response.status_code})")
                results['groq'] = False
        except Exception as e:
            print(f"   ❌ GROQ API: Error - {e}")
            results['groq'] = False
    else:
        print("   ⚠️  GROQ API: No key configured")
        results['groq'] = False
    
    # Test DeepSeek
    deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
    if deepseek_key:
        try:
            url = "https://api.deepseek.com/chat/completions"
            headers = {"Authorization": f"Bearer {deepseek_key}"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("   ✅ DeepSeek API: Working")
                results['deepseek'] = True
            else:
                print(f"   ❌ DeepSeek API: Failed ({response.status_code})")
                results['deepseek'] = False
        except Exception as e:
            print(f"   ❌ DeepSeek API: Error - {e}")
            results['deepseek'] = False
    else:
        print("   ⚠️  DeepSeek API: No key configured")
        results['deepseek'] = False
    
    return results

def test_chat_endpoint():
    """Test the chat endpoint of the application"""
    print("🌐 Testing PHRM Chat Endpoint:")
    
    try:
        # Test if server is running
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code != 200:
            print("   ❌ Server not responding")
            return False
    except:
        print("   ❌ Server not running on localhost:5000")
        return False
    
    # Login and test chat
    try:
        session = requests.Session()
        
        # Get login page
        login_response = session.get('http://localhost:5000/auth/login')
        if login_response.status_code != 200:
            print("   ❌ Cannot access login page")
            return False
        
        # Extract CSRF token
        csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', login_response.text)
        if not csrf_match:
            print("   ❌ No CSRF token found")
            return False
        
        csrf_token = csrf_match.group(1)
        
        # Login
        login_data = {
            'email': 'demo@example.com',
            'password': 'demo123',
            'csrf_token': csrf_token
        }
        
        login_result = session.post('http://localhost:5000/auth/login', data=login_data)
        if login_result.status_code != 302:
            print("   ❌ Login failed")
            return False
        
        print("   ✅ Successfully logged in")
        
        # Test chat endpoint
        chat_data = {
            'message': 'Hello, can you help me?',
            'mode': 'public'
        }
        
        chat_response = session.post('http://localhost:5000/ai/chat', json=chat_data)
        print(f"   Chat API status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            if result.get('response'):
                print("   ✅ Chat endpoint working - got response")
                return True
            else:
                print("   ❌ Chat endpoint returned empty response")
                print(f"   Response: {result}")
                return False
        else:
            print(f"   ❌ Chat endpoint failed: {chat_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing chat endpoint: {e}")
        return False

def check_missing_frontend():
    """Check if chat frontend files are missing"""
    print("📁 Checking Frontend Files:")
    
    js_files = [
        '/home/em/code/wip/phrm/app/static/js/main.js',
        '/home/em/code/wip/phrm/app/static/js/chat-manager.js',
        '/home/em/code/wip/phrm/app/static/js/optimized.min.js'
    ]
    
    missing_files = []
    for file_path in js_files:
        if os.path.exists(file_path):
            print(f"   ✅ {os.path.basename(file_path)}: Found")
        else:
            print(f"   ❌ {os.path.basename(file_path)}: Missing")
            missing_files.append(file_path)
    
    return missing_files

def create_minimal_chat_manager():
    """Create a minimal chat-manager.js file if missing"""
    chat_manager_path = '/home/em/code/wip/phrm/app/static/js/chat-manager.js'
    
    if not os.path.exists(chat_manager_path):
        print("🔧 Creating minimal chat-manager.js...")
        
        chat_manager_content = '''/**
 * Minimal Chat Manager for PHRM
 * Handles basic chat functionality
 */

export class ChatManager {
    constructor() {
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.init();
    }

    init() {
        if (!this.chatForm || !this.chatInput || !this.chatMessages) {
            console.log('Chat elements not found on this page');
            return;
        }

        this.setupEventListeners();
        console.log('Chat manager initialized');
    }

    setupEventListeners() {
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });
    }

    async handleSubmit() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        this.addMessage('user', message);
        this.chatInput.value = '';
        
        const loadingId = this.addMessage('assistant', 'Thinking...', true);

        try {
            const response = await fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    mode: 'public'
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.updateMessage(loadingId, data.response || 'No response received');
            } else {
                this.updateMessage(loadingId, 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.updateMessage(loadingId, 'Network error. Please check your connection.');
        }
    }

    addMessage(role, content, isLoading = false) {
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message ${role}-message`;
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>You</strong>
                    <small>${new Date().toLocaleTimeString()}</small>
                </div>
                <div class="message-content">${this.escapeHtml(content)}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>Health Assistant</strong>
                    <small>${new Date().toLocaleTimeString()}</small>
                </div>
                <div class="message-content">${isLoading ? content : this.formatResponse(content)}</div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageId;
    }

    updateMessage(messageId, content) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML = this.formatResponse(content);
            }
        }
    }

    formatResponse(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
            .replace(/\\n/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}
'''
        
        try:
            with open(chat_manager_path, 'w') as f:
                f.write(chat_manager_content)
            print("   ✅ Created chat-manager.js")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create chat-manager.js: {e}")
            return False
    else:
        print("   ✅ chat-manager.js already exists")
        return True

def main():
    print("🔍 PHRM Chat Troubleshooter")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load environment variables
    load_env_file()
    print()
    
    # Check API keys
    has_keys = check_api_keys()
    print()
    
    # Test AI providers if keys are available
    provider_results = {}
    if has_keys:
        provider_results = test_ai_providers()
        print()
    
    # Check frontend files
    missing_files = check_missing_frontend()
    print()
    
    # Create missing files
    if missing_files:
        if '/home/em/code/wip/phrm/app/static/js/chat-manager.js' in missing_files:
            create_minimal_chat_manager()
            print()
    
    # Test chat endpoint
    chat_working = test_chat_endpoint()
    print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 50)
    
    if chat_working:
        print("🎉 Chat is working!")
        print("   The chat endpoint is responding correctly.")
    elif has_keys and any(provider_results.values()):
        print("⚠️  Chat partially working:")
        print("   - AI providers are available")
        print("   - Check frontend JavaScript console for errors")
        print("   - Try refreshing the browser")
    elif has_keys:
        print("❌ Chat not working:")
        print("   - API keys configured but providers failing")
        print("   - Check API key validity and quotas")
    else:
        print("❌ Chat not working - No API keys configured")
        print("   Please configure at least one AI provider:")
        print("   1. Edit .env file")
        print("   2. Add HUGGINGFACE_ACCESS_TOKEN, GROQ_API_KEY, or DEEPSEEK_API_KEY")
        print("   3. Restart the application")
    
    print()
    print("💡 Quick fixes to try:")
    print("   1. Refresh your browser")
    print("   2. Check browser console (F12) for JavaScript errors")
    print("   3. Restart the PHRM application")
    print("   4. Clear browser cache")
    
    return chat_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
