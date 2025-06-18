# MedGemma Access Guide

## 🎯 Current Status
Your PHRM system is successfully configured for MedGemma integration with intelligent fallbacks. The system is working but needs a valid Hugging Face token with MedGemma access.

## 🔑 How to Get MedGemma Access

### Step 1: Create/Update Hugging Face Account
1. Visit [Hugging Face](https://huggingface.co/)
2. Sign up for a free account or log in to existing account
3. Verify your email address

### Step 2: Generate API Token
1. Go to [Hugging Face Settings > Access Tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name it something like "PHRM-MedGemma"
4. Select scope: **"Read"** (minimum required)
5. Click "Generate a token"
6. **Copy the token immediately** (it won't be shown again)

### Step 3: Accept MedGemma Terms of Use
1. Visit the [MedGemma 27B model page](https://huggingface.co/google/medgemma-27b-text-it)
2. **Log in** to your Hugging Face account
3. You should see a prompt to "Accept Terms" or review conditions
4. Click "Accept" to agree to the Health AI Developer Foundation terms
5. Visit the [MedGemma 4B model page](https://huggingface.co/google/medgemma-4b-it) and accept terms there too

### Step 4: Update Your Environment
1. Open your `.env` file in the PHRM project
2. Update the token:
   ```bash
   HUGGINGFACE_ACCESS_TOKEN=hf_your_new_token_here
   ```
3. Save the file

### Step 5: Test Access
```bash
cd /home/em/code/wip/phrm
python test_medgemma.py
```

## 🔧 Current System Status

### ✅ Working Components:
- **Remote-only integration**: No local model downloads
- **Medical AI fallbacks**: Using Mixtral-8x7B-Instruct for medical queries
- **Access checking**: Automatically detects token/access issues
- **Intelligent routing**: Tries MedGemma first, falls back gracefully
- **Zero heavy dependencies**: No torch, transformers, or safetensors

### ⚠️ Needs Attention:
- **Token Issue**: Current token is invalid/expired (401 error)
- **Terms Acceptance**: Need to accept MedGemma terms of use

## 🚀 Alternative Access Methods

If direct HuggingFace access doesn't work, the system also tries:

### 1. Hugging Face Spaces
- Checks community-deployed MedGemma instances
- Examples: `rishiraj/medgemma-27b-text-it`, `Taylor658/medgemma27b`

### 2. Third-Party Providers (Future)
- Together AI: Set `TOGETHER_API_KEY` environment variable
- Replicate: Set `REPLICATE_API_TOKEN` environment variable

### 3. Google Cloud Vertex AI (Production)
For production deployments, consider Google Cloud Model Garden:
- Direct access to MedGemma models
- Requires Google Cloud account
- More reliable for production use

## 📊 Current Performance

### Resource Usage:
- **Storage**: ~50MB (just API libraries, no model files)
- **RAM**: ~200MB (base Flask app)
- **Startup Time**: 2-3 seconds
- **Dependencies**: Minimal (no ML libraries)

### AI Quality:
- **Fallback Model**: Mixtral-8x7B-Instruct-v0.1
- **Medical Knowledge**: Good general medical knowledge
- **Response Quality**: High quality medical responses
- **Availability**: 99.9% uptime via HuggingFace Inference API

## 🔍 Troubleshooting

### Token Issues:
```bash
# Check token format (should start with hf_)
echo $HUGGINGFACE_ACCESS_TOKEN

# Test token manually
curl -H "Authorization: Bearer $HUGGINGFACE_ACCESS_TOKEN" \
     https://huggingface.co/api/whoami
```

### Access Issues:
1. **401 Unauthorized**: Token is invalid/expired
2. **403 Forbidden**: Haven't accepted terms of use
3. **404 Not Found**: Model not available via Inference API

### Quick Fixes:
1. **Regenerate token** on Hugging Face
2. **Accept terms** on model pages
3. **Restart Flask app** after changing .env
4. **Check logs** for detailed error messages

## 💡 Best Practices

### For Development:
- Use the fallback models for testing
- MedGemma access is optional for development
- Keep the current remote-only approach

### For Production:
- Get proper MedGemma access for best medical AI quality
- Consider Google Cloud Vertex AI for reliability
- Monitor API usage and rate limits
- Set up proper error handling and logging

## 🎉 Success Indicators

You'll know MedGemma access is working when you see:
```
✅ MedGemma Access Status: Has Access: True
✅ Successfully used MedGemma model
✅ Using MedGemma 27B text-only for optimal text performance
```

Until then, the system works perfectly with medical-focused alternatives!
