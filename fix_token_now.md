# 🚨 URGENT: Fix Expired Meta Access Token

## Current Issue
The Meta access token has expired. Error from logs:
```
"Error validating access token: Session has expired on Saturday, 19-Jul-25 07:00:00 PDT"
```

## Quick Fix (5 minutes)

### Option 1: Meta Developers Console (Recommended)
1. **Go to Meta Developers Console**:
   - Visit: https://developers.facebook.com/apps/1765967607656060/whatsapp-business/wa-dev-console/
   - Log in with your Facebook/Meta account

2. **Generate New Token**:
   - Look for "Temporary access token" section
   - Click "Generate Token" or "Get Token"
   - Copy the new token (starts with EAAA...)

3. **Update Environment**:
   ```bash
   # Edit your .env file
   nano .env
   
   # Replace the line:
   META_ACCESS_TOKEN=EAAZAGI1ZCwbnwBPIeZB...
   
   # With new token:
   META_ACCESS_TOKEN=EAAA_NEW_TOKEN_HERE
   ```

4. **Restart Application**:
   ```bash
   # Stop current process (Ctrl+C if running)
   # Then restart:
   uv run uvicorn src.lanabot.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Use Generated App Token (Temporary)
If the console method doesn't work, you can try the app token we generated:

```bash
# In your .env file, temporarily use:
META_ACCESS_TOKEN=1765967607656060|OUWbSZUmw3soEg4uQhUfx_jKY58
```

**Note**: This might have limited functionality but could work for basic messaging.

## Long-term Solution
The automatic token refresh we implemented will:
- Detect 401 errors automatically
- Attempt to refresh tokens
- Retry failed requests
- Log all token-related issues

## Test After Fix
Send a WhatsApp message to verify:
1. Send "hola" to your WhatsApp number
2. Check logs for successful message sending
3. Verify you receive the welcome message

## Current App Details
- App ID: 1765967607656060
- Phone Number ID: 698358536698465
- Current working phone number: 525548471763

## If Problems Persist
1. Check Meta App status in developers console
2. Verify WhatsApp Business API permissions
3. Ensure phone number is verified and approved
4. Check webhook URL configuration