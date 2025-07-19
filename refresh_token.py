#!/usr/bin/env python3
"""Manual script to refresh Meta access token for WhatsApp Business API."""

import asyncio
import httpx
from src.lanabot.config import get_settings


async def refresh_meta_token():
    """Refresh Meta access token and display the new token."""
    settings = get_settings()
    
    print("🔄 Refreshing Meta access token...")
    print(f"App ID: {settings.meta_app_id}")
    print(f"Current token (first 20 chars): {settings.meta_access_token[:20]}...")
    
    try:
        # Method 1: Try app access token generation
        url = "https://graph.facebook.com/oauth/access_token"
        
        params = {
            "grant_type": "client_credentials",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            token_type = data.get("token_type", "unknown")
            
            if new_token:
                print(f"✅ Successfully generated new {token_type} token!")
                print(f"📋 New token (first 20 chars): {new_token[:20]}...")
                print(f"📋 Full token: {new_token}")
                print(f"\n⚠️  Note: Update your .env file with:")
                print(f"META_ACCESS_TOKEN={new_token}")
                return new_token
            else:
                print("❌ No access token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Failed to refresh token: {response.text}")
            
            # Method 2: Try to get info about current token
            print(f"\n🔍 Checking current token info...")
            token_info_url = f"https://graph.facebook.com/me?access_token={settings.meta_access_token}"
            
            async with httpx.AsyncClient() as client:
                info_response = await client.get(token_info_url)
            
            print(f"Token info response: {info_response.status_code}")
            if info_response.status_code == 200:
                print(f"Token info: {info_response.json()}")
            else:
                print(f"Token info error: {info_response.text}")
            
            return None
            
    except Exception as e:
        print(f"❌ Error refreshing token: {e}")
        return None


async def test_token(token: str):
    """Test if a token works for WhatsApp API."""
    settings = get_settings()
    
    print(f"\n🧪 Testing token...")
    
    # Try to get phone number info
    url = f"https://graph.facebook.com/v18.0/{settings.meta_phone_number_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        
        print(f"Test response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token works! Phone info: {data}")
            return True
        else:
            print(f"❌ Token test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False


if __name__ == "__main__":
    async def main():
        new_token = await refresh_meta_token()
        
        if new_token:
            # Test the new token
            works = await test_token(new_token)
            
            if works:
                print(f"\n🎉 Success! Your new token is working.")
                print(f"📝 Don't forget to update your .env file!")
            else:
                print(f"\n⚠️  Generated token but it doesn't seem to work for WhatsApp API")
        else:
            print(f"\n💡 Alternative: Go to Meta Developers Console:")
            print(f"   1. Visit: https://developers.facebook.com/apps/{get_settings().meta_app_id}/whatsapp-business/wa-dev-console/")
            print(f"   2. Generate a new temporary access token")
            print(f"   3. Update your .env file")
    
    asyncio.run(main())