# OAuth 1.0a Authorization Error - Troubleshooting Guide

**Error**: `OAuth Authorization Error - Request failed with status code 401`

**Cause**: Invalid or incorrect OAuth 1.0a credentials

**Solution**: Get fresh credentials from Twitter Developer Portal

---

## Step 1: Verify You're Getting the RIGHT Credentials

### ❌ Common Mistake #1: Getting Bearer Token Instead

If you copied a **Bearer Token** (starts with `AAAA...`), that's **WRONG**.

**Bearer Token Example** (❌ NOT for OAuth 1.0a):
```
AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75
```

**You need OAuth 1.0a credentials instead** (✅ for posting):
```
Consumer Key: xxxxxxxxxxxxxxxxxxxx
Consumer Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Access Token: xxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Access Token Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Step 2: Get Fresh Credentials from Twitter Developer Portal

### **Detailed Walkthrough**

**1. Go to Twitter Developer Portal**
- URL: https://developer.twitter.com/en/portal/dashboard
- Sign in with your Twitter account

**2. Select Your Application**
- You should see your app name
- Click on it

**3. Go to "Keys and Tokens" Tab**
- At the top of your app page
- You'll see several tabs: **Keys and Tokens** ← Click this
- (NOT "App Settings" or "Keys and tokens" - be careful with the exact name)

---

## Step 3: Copy Each Credential Carefully

### **Location 1: API Key & Secret**

You should see a section that says:
```
API Key
Consumer Key in OAuth 1.0a User Context
```

**Copy 1**: API Key (also called Consumer Key)
- Click the **"Copy"** button
- Looks like: `xxxxxxxxxxxxxxxxxxx` (about 25 characters)
- Paste into n8n as: **Consumer Key**

**Copy 2**: API Secret Key (also called Consumer Secret)
- Next to API Key
- Click **"Copy"** button
- Looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (about 50 characters)
- Paste into n8n as: **Consumer Secret**

⚠️ **IMPORTANT**: 
- Don't copy manually (use the Copy button)
- Don't add extra spaces
- These must be EXACT

---

### **Location 2: Access Token & Secret**

Below the API Key/Secret, look for:
```
Access Token & Secret
```

**If you see a "Generate" button:**
1. Click **"Generate"** button
2. It creates new Access Token and Secret
3. Copy them immediately (you can only see them once!)

**If you see the tokens already:**
1. Copy the **Access Token**
   - Looks like: `123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxx` (starts with numbers)
   - Paste into n8n as: **Access Token**

2. Copy the **Access Token Secret**
   - Looks very long: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Paste into n8n as: **Access Token Secret**

---

## Step 4: Verify You Have All 4 Credentials

Before putting into n8n, check you have:

- [ ] **Consumer Key** (starts with letters/numbers, ~25 chars)
  ```
  Example: xxxxxxxxxxxxxxxxxxx
  ```

- [ ] **Consumer Secret** (long string, ~50 chars)
  ```
  Example: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

- [ ] **Access Token** (starts with digits followed by dash, ~50 chars)
  ```
  Example: 123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

- [ ] **Access Token Secret** (long string, ~50 chars)
  ```
  Example: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

**All 4 are REQUIRED and DIFFERENT from each other**

---

## Step 5: Add to n8n Carefully

### **In n8n:**

1. Go to **Credentials** → Click **"+ New"**
2. Search for and select: **"Twitter OAuth 1.0a"**
   - (NOT "Twitter" or "Twitter API v2" - must be OAuth 1.0a)
3. Fill in EXACTLY:
   - **Consumer Key**: Paste from step 3
   - **Consumer Secret**: Paste from step 3
   - **Access Token**: Paste from step 3
   - **Access Token Secret**: Paste from step 3

4. Click **"Test"** button (if available)
   - Should say "Connection successful"
   - If not: credentials are wrong

5. Click **"Save"**
6. Give it a name: `Twitter OAuth 1.0a`

---

## Step 6: Troubleshooting 401 Error

### **Issue 1: Copy-Paste Error**

**Symptom**: Credentials look right but still get 401

**Fix**:
1. Delete the credential in n8n
2. Go back to Twitter Developer Portal
3. Use the **"Copy"** button next to each credential
4. Don't copy manually!
5. Paste immediately into n8n
6. Try again

### **Issue 2: Extra Spaces**

**Symptom**: Credentials have extra spaces or characters

**Fix**:
1. Check for spaces at beginning or end
2. Each credential should be clean text
3. Delete any accidental spaces
4. Try again

### **Issue 3: Wrong Credentials**

**Symptom**: You have Consumer Key but not Access Token

**Fix**:
1. Go to Twitter Dev Portal
2. Go to "Keys and Tokens" tab
3. Look for **"Authentication Tokens & Keys"** section
4. If you only see "Consumer Key" and "Consumer Secret":
   - Scroll down more
   - Look for "Access Token & Secret"
   - Click **"Generate"** if not present
5. Copy both Access Token and Secret

### **Issue 4: App Not Approved**

**Symptom**: Can't find "Keys and Tokens" tab

**Fix**:
1. Your Twitter Developer account might not be approved yet
2. Check your email for Twitter approval
3. You should have received email like "Your Twitter developer account is approved"
4. If not: wait 24-48 hours for approval
5. Check spam folder

### **Issue 5: Using Wrong OAuth Type**

**Symptom**: You have "OAuth 2.0" credentials instead of "OAuth 1.0a"

**Fix**:
1. Twitter offers both OAuth 1.0a and OAuth 2.0
2. For posting tweets, you NEED **OAuth 1.0a**
3. Look specifically for:
   - **Consumer Key** and **Consumer Secret** (not Client ID)
   - **Access Token** and **Access Token Secret** (not Refresh Token)

---

## Visual Guide: Finding Credentials in Twitter Portal

```
Developer Portal
    ↓
Your Apps
    ↓
[Select Your App]
    ↓
[Keys and Tokens Tab] ← Click here
    ↓
┌─────────────────────────────────────┐
│ SECTION 1: API Keys                 │
│ ┌─────────────────────────────────┐ │
│ │ API Key          [Copy]         │ │ ← Consumer Key
│ │ API Key Secret   [Copy]         │ │ ← Consumer Secret
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ SECTION 2: Authentication Tokens    │
│ ┌─────────────────────────────────┐ │
│ │ Access Token     [Copy]         │ │ ← Access Token
│ │ Access Secret    [Copy]         │ │ ← Access Token Secret
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## Regenerate Credentials (If Stuck)

If something is wrong and you can't figure it out:

**Option 1: Regenerate Access Token**
1. Go to Twitter Dev Portal → Keys and Tokens
2. Find Access Token section
3. Click **"Regenerate"** button
4. Copy the NEW Access Token and Secret
5. Update n8n credential with new values

**Option 2: Create New App**
1. If your app is broken, create a new one
2. Go to Twitter Dev Portal → Apps
3. Click **"Create App"**
4. Name it: `content-automation-bot-v2`
5. Get fresh credentials
6. Use in n8n

---

## Verify Credentials Work (Before n8n)

### **Quick Test in OAuth Tool**

Use an online OAuth 1.0a tool to verify your credentials:

1. Go to: https://oauth-playground.glitch.me/ (or similar)
2. Paste your credentials
3. Try to authorize
4. If it works: credentials are valid
5. If it fails: credentials are invalid

This helps confirm it's not an n8n issue.

---

## Final Checklist Before Testing

- [ ] Logged into Twitter Developer Portal
- [ ] Went to **Keys and Tokens** tab (exactly this name)
- [ ] Have all 4 credentials visible on screen
- [ ] Copied each using the **"Copy"** button (not manual copy)
- [ ] Deleted previous failed credential in n8n
- [ ] Created NEW credential in n8n with correct type: **"Twitter OAuth 1.0a"**
- [ ] Pasted credentials EXACTLY as copied
- [ ] Saved the credential
- [ ] Clicked **"Test"** in n8n (should say "Connection successful")

---

## If Still Getting 401 Error

If you've followed all steps and still get 401:

**The most common cause:**
- Using **OAuth 2.0** credentials instead of **OAuth 1.0a**
- Using **Bearer Token** instead of Consumer Key + Secret
- Credentials belong to **different app** than the one with API access

**Try this:**
1. Delete the credential in n8n
2. Go to Twitter Dev Portal
3. Check your app type
4. Make sure it's set to **"Elevated"** or has **full access**
5. Get fresh credentials
6. Try again

Or provide me with:
- Which exact credentials you're using (don't share actual values - just say "Consumer Key from APIs section" etc.)
- What error message you see
- Which n8n credential type you selected

---

## Quick Summary

| What is it | Where to find | What to paste in n8n |
|-----------|---------------|---------------------|
| Consumer Key | Twitter Portal → Keys tab → API Key | Consumer Key field |
| Consumer Secret | Twitter Portal → Keys tab → API Secret | Consumer Secret field |
| Access Token | Twitter Portal → Keys tab → Access Token | Access Token field |
| Access Token Secret | Twitter Portal → Keys tab → Access Secret | Access Token Secret field |

**ALL 4 ARE REQUIRED AND FROM THE SAME APP**

---

Start from **Step 2** and get fresh credentials. That usually fixes the 401 error!

Let me know which step you get stuck on, or share what credentials you're seeing in the Twitter Portal, and I can help point you to the right ones.
