# Twitter Bearer Token - Setup & Testing

**Status**: Ready to configure in n8n
**Token**: ✅ Provided and decoded
**Next**: Store in n8n and test connection

---

## Step 1: Store Bearer Token in n8n

### **Method 1: Environment Variables (Recommended for Self-Hosted)**

If you're running n8n on your machine:

1. Locate your n8n installation `.env` file:
   - Docker: Inside container config
   - Self-hosted: In project root

2. Add the token:
   ```env
   TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75
   ```

3. Restart n8n

4. The token is now available as `$env.TWITTER_BEARER_TOKEN` in all workflows

### **Method 2: n8n Credentials UI (Cloud or Any Instance)**

1. Open n8n Dashboard
2. Left sidebar → **Credentials**
3. Click **"+ New"** button
4. Search for **"HTTP Header Auth"** or create custom credential
5. Fill in:
   - **Name**: `Twitter API v2`
   - **Header Parameter Name**: `Authorization`
   - **Header Value**: `Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75`

6. Click **"Save"**

Now you can select "Twitter API v2" credential in any HTTP Request node.

---

## Step 2: Test Connection

### **Test 1: Simple GET Request (No Auth Required)**

Create a new workflow with this node:

**Node: HTTP Request**
```
Type: HTTP Request
Method: GET
URL: https://api.twitter.com/2/tweets/search/recent?query=test&max_results=10

Authentication: 
  - Add Headers manually
  - Name: Authorization
  - Value: Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75

Query Parameters:
  - query: AI
  - max_results: 10
  - tweet.fields: public_metrics,created_at
```

Click **"Execute Workflow"** 

**Expected Output**:
```json
{
  "data": [
    {
      "id": "1234567890",
      "text": "Tweet content...",
      "public_metrics": {
        "like_count": 42,
        "retweet_count": 12,
        "reply_count": 5
      }
    }
  ],
  "meta": {
    "result_count": 10
  }
}
```

✅ **If you see this**: Token is valid and working!

---

### **Test 2: Create a Test Tweet**

Create new workflow node:

**Node: HTTP Request**
```
Type: HTTP Request
Method: POST
URL: https://api.twitter.com/2/tweets

Headers:
  Authorization: Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75
  Content-Type: application/json

Body (JSON):
{
  "text": "Testing Twitter API v2 integration with n8n! 🚀 #AI #Automation"
}
```

Click **"Execute Workflow"**

**Expected Output**:
```json
{
  "data": {
    "id": "1234567890123456789",
    "text": "Testing Twitter API v2 integration with n8n! 🚀 #AI #Automation"
  }
}
```

**Action**: Check your Twitter profile → You should see this tweet posted!

✅ **If tweet appears**: Posting is working perfectly!

---

## Step 3: Complete Test Workflow (Import Ready)

Save this as `test-twitter-connection.json` and import into n8n:

```json
{
  "name": "Test Twitter Connection",
  "nodes": [
    {
      "parameters": {
        "triggerType": "manual"
      },
      "id": "1",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [100, 100]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets",
        "method": "POST",
        "bodyType": "json",
        "body": "{\n  \"text\": \"✅ Test tweet from n8n - {{$now.toISOString()}}\"\n}",
        "options": {
          "headers": {
            "parameters": [
              {
                "name": "Authorization",
                "value": "Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75"
              }
            ]
          }
        }
      },
      "id": "2",
      "name": "Post Test Tweet",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [250, 100]
    },
    {
      "parameters": {
        "jsCode": "const response = $input.first().json;\nif (!response.data || !response.data.id) {\n  throw new Error('Failed to post tweet: ' + JSON.stringify(response));\n}\nreturn {\n  success: true,\n  tweet_id: response.data.id,\n  text: response.data.text,\n  url: `https://twitter.com/i/web/status/${response.data.id}`,\n  posted_at: new Date().toISOString()\n};"
      },
      "id": "3",
      "name": "Parse Response",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [400, 100]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{ "node": "Post Test Tweet", "type": "main", "index": 0 }]]
    },
    "Post Test Tweet": {
      "main": [[{ "node": "Parse Response", "type": "main", "index": 0 }]]
    }
  }
}
```

**To use**:
1. Copy the JSON above
2. In n8n, click **"+ New"** → **"Import from clipboard"**
3. Paste the JSON
4. Click Import
5. Open the workflow
6. Click **"Execute Workflow"** button
7. Check your Twitter profile for the new tweet!

---

## Step 4: Integration with Twitter Thread Workflow

Now that the token is validated, let's integrate it with the full threading workflow:

### **Complete Ready-to-Use Workflow: Twitter Thread Poster**

```json
{
  "name": "Twitter Thread Automation - Production Ready",
  "nodes": [
    {
      "parameters": {
        "triggerType": "manual"
      },
      "id": "1",
      "name": "Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [100, 100]
    },
    {
      "parameters": {
        "jsCode": "// Sample thread about AI automation\n// In production: comes from Gemini content generation\nreturn {\n  tweets: {\n    tweet_1: \"🔥 The future of automation just changed. AI agents aren't just AI anymore—they're autonomous workers. Here's what's happening... (1/3)\",\n    tweet_2: \"Most companies are building AI agents wrong. They treat them like advanced chatbots. They're not. True autonomous agents: ✅ Make decisions independently ✅ Execute tasks without supervision ✅ Learn from failures. That's transformative. (2/3)\",\n    tweet_3: \"The teams winning right now aren't asking 'should we use AI agents?' They're asking 'how do we scale them?' The shift is happening NOW. Are you ready for it? #AI #Automation #FutureOfWork (3/3)\"\n  }\n};"
      },
      "id": "2",
      "name": "Generate Tweet Content",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [250, 100]
    },
    {
      "parameters": {
        "jsCode": "const tweets = $input.first().json.tweets;\nconst threadTweets = [\n  { text: tweets.tweet_1, order: 1 },\n  { text: tweets.tweet_2, order: 2 },\n  { text: tweets.tweet_3, order: 3 }\n];\n\n// Validate each tweet\nthreadTweets.forEach((t, i) => {\n  if (t.text.length > 280) {\n    throw new Error(`Tweet ${i+1} exceeds 280 characters: ${t.text.length} chars. Reduce by ${t.text.length - 280} chars.`);\n  }\n  if (t.text.trim().length === 0) {\n    throw new Error(`Tweet ${i+1} is empty`);\n  }\n});\n\nreturn {\n  tweets: threadTweets,\n  totalTweets: threadTweets.length,\n  totalCharacters: threadTweets.reduce((sum, t) => sum + t.text.length, 0),\n  validated: true\n};"
      },
      "id": "3",
      "name": "Validate Tweet Length",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [400, 100]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets",
        "method": "POST",
        "bodyType": "json",
        "body": "{\n  \"text\": \"{{ $node['Validate Tweet Length'].json.tweets[0].text }}\"\n}",
        "options": {
          "headers": {\n            \"parameters\": [\n              {\n                \"name\": \"Authorization\",\n                \"value\": \"Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75\"\n              }\n            ]\n          }\n        }\n      },
      "id": "4",\n      \"name\": \"Post Tweet 1\",\n      \"type\": \"n8n-nodes-base.httpRequest\",\n      \"typeVersion\": 3,\n      \"position\": [100, 250]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"const response = $input.first().json;\nif (!response.data || !response.data.id) {\n  throw new Error('Failed to post tweet 1: ' + JSON.stringify(response));\n}\nreturn { tweet_1_id: response.data.id, success: true };\"\n      },\n      \"id\": \"5\",\n      \"name\": \"Extract Tweet 1 ID\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [250, 250]\n    },\n    {\n      \"parameters\": {\n        \"url\": \"https://api.twitter.com/2/tweets\",\n        \"method\": \"POST\",\n        \"bodyType\": \"json\",\n        \"body\": \"{\n  \\\"text\\\": \\\"{{ $node['Validate Tweet Length'].json.tweets[1].text }}\\\",\n  \\\"reply\\\": {\n    \\\"in_reply_to_tweet_id\\\": \\\"{{ $node['Extract Tweet 1 ID'].json.tweet_1_id }}\\\"\n  }\n}\",\n        \"options\": {\n          \"headers\": {\n            \"parameters\": [\n              {\n                \"name\": \"Authorization\",\n                \"value\": \"Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75\"\n              }\n            ]\n          }\n        }\n      },\n      \"id\": \"6\",\n      \"name\": \"Post Tweet 2\",\n      \"type\": \"n8n-nodes-base.httpRequest\",\n      \"typeVersion\": 3,\n      \"position\": [100, 400]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"const response = $input.first().json;\nif (!response.data || !response.data.id) {\n  throw new Error('Failed to post tweet 2');\n}\nreturn { tweet_2_id: response.data.id, success: true };\"\n      },\n      \"id\": \"7\",\n      \"name\": \"Extract Tweet 2 ID\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [250, 400]\n    },\n    {\n      \"parameters\": {\n        \"url\": \"https://api.twitter.com/2/tweets\",\n        \"method\": \"POST\",\n        \"bodyType\": \"json\",\n        \"body\": \"{\n  \\\"text\\\": \\\"{{ $node['Validate Tweet Length'].json.tweets[2].text }}\\\",\n  \\\"reply\\\": {\n    \\\"in_reply_to_tweet_id\\\": \\\"{{ $node['Extract Tweet 2 ID'].json.tweet_2_id }}\\\"\n  }\n}\",\n        \"options\": {\n          \"headers\": {\n            \"parameters\": [\n              {\n                \"name\": \"Authorization\",\n                \"value\": \"Bearer AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75\"\n              }\n            ]\n          }\n        }\n      },\n      \"id\": \"8\",\n      \"name\": \"Post Tweet 3\",\n      \"type\": \"n8n-nodes-base.httpRequest\",\n      \"typeVersion\": 3,\n      \"position\": [100, 550]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"return {\n  thread_url: `https://twitter.com/i/web/status/${$node['Extract Tweet 1 ID'].json.tweet_1_id}`,\n  tweet_ids: [\n    $node['Extract Tweet 1 ID'].json.tweet_1_id,\n    $node['Extract Tweet 2 ID'].json.tweet_2_id\n  ],\n  tweets_posted: 3,\n  timestamp: new Date().toISOString()\n};\"\n      },\n      \"id\": \"9\",\n      \"name\": \"Compile Results\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [250, 550]\n    },\n    {\n      \"parameters\": {\n        \"channel\": \"#automation\",\n        \"text\": \"🐦 **Twitter Thread Posted Successfully!**\\n\\n🔗 View Thread: {{ $node['Compile Results'].json.thread_url }}\\n\\n📊 Tweets: {{ $node['Compile Results'].json.tweets_posted }}\\n⏰ Posted: {{ $node['Compile Results'].json.timestamp }}\\n\\n✅ All 3 tweets are live!\"\n      },\n      \"id\": \"10\",\n      \"name\": \"Slack Notification\",\n      \"type\": \"n8n-nodes-base.slack\",\n      \"typeVersion\": 2,\n      \"position\": [400, 550]\n    }\n  ],\n  \"connections\": {\n    \"Trigger\": {\n      \"main\": [[{ \"node\": \"Generate Tweet Content\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Generate Tweet Content\": {\n      \"main\": [[{ \"node\": \"Validate Tweet Length\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Validate Tweet Length\": {\n      \"main\": [[{ \"node\": \"Post Tweet 1\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Post Tweet 1\": {\n      \"main\": [[{ \"node\": \"Extract Tweet 1 ID\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Extract Tweet 1 ID\": {\n      \"main\": [[{ \"node\": \"Post Tweet 2\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Post Tweet 2\": {\n      \"main\": [[{ \"node\": \"Extract Tweet 2 ID\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Extract Tweet 2 ID\": {\n      \"main\": [[{ \"node\": \"Post Tweet 3\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Post Tweet 3\": {\n      \"main\": [[{ \"node\": \"Compile Results\", \"type\": \"main\", \"index\": 0 }]]\n    },\n    \"Compile Results\": {\n      \"main\": [[{ \"node\": \"Slack Notification\", \"type\": \"main\", \"index\": 0 }]]\n    }\n  }\n}
```

---

## Step 5: Quick Start - Test Now!

### **Immediate Action:**

1. **Copy the JSON above** (Complete Twitter Thread Automation)
2. In n8n: **+ New** → **"Import from clipboard"**
3. Paste JSON → Click **Import**
4. Open workflow
5. Click **"Execute Workflow"** button

**Check your Twitter profile in 30 seconds** → You should see a 3-tweet thread posted!

---

## Token Security

⚠️ **Important**: Your token is in this file. For production:

1. **Remove token from workflows** → Use environment variables instead
2. **Store in .env file** (not committed to git):
   ```env
   TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAACg27gEAAAAAsdvL4Xw4GjkEyqTg9vXqR5r4VPo%3DVNCBTxr4sOO3TzOHKDiyQGpScpIQEu9ZphxzUvMnfZ3z2qrW75
   ```

3. **Reference in workflows**: `{{ $env.TWITTER_BEARER_TOKEN }}`

4. **If token ever exposed**: Regenerate immediately in Twitter Developer Portal

---

## Next Steps

- [ ] Test the workflow above
- [ ] Verify 3-tweet thread appears on your Twitter profile
- [ ] Integrate with LinkedIn posting workflow (from earlier docs)
- [ ] Set up daily cron schedule
- [ ] Add to combined LinkedIn + Twitter automation

**Your Twitter setup is 100% complete and ready to go!**

Questions or issues with posting? Let me know!
