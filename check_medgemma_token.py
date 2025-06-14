#!/usr/bin/env python3
"""
Quick script to validate and help fix Hugging Face token for MedGemma access
"""

import os

import requests

# HTTP status codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404


def check_token_validity():
    """Check if the current Hugging Face token is valid"""
    token = os.environ.get("HUGGINGFACE_ACCESS_TOKEN")

    if not token:
        print("❌ No HUGGINGFACE_ACCESS_TOKEN found in environment")
        print("💡 Add it to your .env file: HUGGINGFACE_ACCESS_TOKEN=hf_...")
        return False

    if not token.startswith("hf_"):
        print("⚠️  Token doesn't start with 'hf_' - this might be incorrect format")
        print(f"Current token: {token[:10]}...")

    print(f"🔑 Testing token: {token[:8]}...{token[-4:]}")

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://huggingface.co/api/whoami", headers=headers, timeout=10
        )

        if response.status_code == HTTP_OK:
            user_info = response.json()
            print("✅ Token is valid!")
            print(f"   User: {user_info.get('name', 'Unknown')}")
            print(f"   Type: {user_info.get('type', 'Unknown')}")
            return True
        elif response.status_code == HTTP_UNAUTHORIZED:
            print("❌ Token is invalid or expired")
            print("💡 Generate a new token at: https://huggingface.co/settings/tokens")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        print("💡 Check your internet connection")
        return False


def check_medgemma_access():
    """Check if the token has access to MedGemma models"""
    token = os.environ.get("HUGGINGFACE_ACCESS_TOKEN")
    if not token:
        return False

    print("\n🧬 Checking MedGemma model access...")

    models = ["google/medgemma-27b-text-it", "google/medgemma-4b-it"]

    headers = {"Authorization": f"Bearer {token}"}

    for model in models:
        try:
            # Check if we can access model info
            response = requests.get(
                f"https://huggingface.co/api/models/{model}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == HTTP_OK:
                model_info = response.json()
                is_gated = model_info.get("gated", False)
                print(f"✅ {model}: Accessible (gated: {is_gated})")

                # Try to access files to check if terms are accepted
                files_response = requests.get(
                    f"https://huggingface.co/api/models/{model}/tree/main",
                    headers=headers,
                    timeout=10,
                )

                if files_response.status_code == HTTP_OK:
                    print("   ✅ Terms of use accepted")
                elif files_response.status_code == HTTP_FORBIDDEN:
                    print("   ❌ Terms of use NOT accepted")
                    print(f"   💡 Visit: https://huggingface.co/{model}")
                else:
                    print(f"   ⚠️  Files access: {files_response.status_code}")

            elif response.status_code == HTTP_NOT_FOUND:
                print(f"❌ {model}: Not found or no access")
            else:
                print(f"⚠️  {model}: Response {response.status_code}")

        except requests.RequestException as e:
            print(f"❌ {model}: Network error - {e}")

    return True


def main():
    """Main validation function"""
    print("🔍 Hugging Face Token Validator for MedGemma")
    print("=" * 50)

    # Check token validity
    if not check_token_validity():
        print("\n📋 Next Steps:")
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Create a new token with 'Read' scope")
        print("3. Update your .env file: HUGGINGFACE_ACCESS_TOKEN=hf_your_new_token")
        print("4. Restart this script")
        return

    # Check MedGemma access
    check_medgemma_access()

    print("\n📋 Summary:")
    print("- If token is valid but MedGemma shows 'terms not accepted':")
    print("  Visit the model pages and accept the Health AI Developer Foundation terms")
    print("- If everything shows ✅, your MedGemma integration should work!")
    print("- Test with: python test_medgemma.py")


if __name__ == "__main__":
    main()
