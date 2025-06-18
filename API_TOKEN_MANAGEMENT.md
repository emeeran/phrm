# API Token Management Guide

This document provides guidance on managing API tokens for the AI providers used in the PHRM system.

## Hugging Face Tokens

### Current Issue: MedGemma Quota Exhaustion

If you see the error: `MedGemma Inference API error: 402 - {"error":"You have exceeded your monthly included credits for Inference Providers."}`, the Hugging Face API quota has been exhausted.

### How to Fix

1. **Get a new Hugging Face token**:
   - Log in to [Hugging Face](https://huggingface.co)
   - Go to Settings > Access Tokens
   - Create a new token with "read" permissions
   - Copy the new token

2. **Update the .env.production file**:
   ```bash
   # Open the file
   nano .env.production

   # Update the token
   HUGGINGFACE_ACCESS_TOKEN=hf_your_new_token_here

   # Save the file
   ```

3. **Restart the application**:
   ```bash
   # Navigate to project directory
   cd /home/em/code/wip/phrm

   # Restart the application
   flask run
   # Or using your specific start command
   ```

4. **Long-term solution**:
   - Consider subscribing to Hugging Face PRO for higher monthly quotas
   - Implement a token rotation system with multiple accounts
   - Set up local inference for high-usage models

## Alternative AI Providers

The system is configured to fall back to these providers when MedGemma is unavailable:

1. **Groq**:
   - Edit `GROQ_API_KEY` in .env.production
   - Get new keys at [Groq Cloud](https://console.groq.com/)

2. **DeepSeek**:
   - Edit `DEEPSEEK_API_KEY` in .env.production
   - Get new keys at [DeepSeek AI](https://platform.deepseek.com/)

## Monitoring Token Usage

To monitor your API token usage:

1. **Hugging Face**: Visit the [Hugging Face Usage Dashboard](https://huggingface.co/settings/usage)
2. **Groq**: Check your usage at [Groq Console](https://console.groq.com/usage)
3. **DeepSeek**: Monitor through [DeepSeek Platform](https://platform.deepseek.com/usage)

## Contact

For urgent assistance with API tokens, contact the system administrator at admin@example.com.
