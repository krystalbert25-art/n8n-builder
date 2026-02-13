# Twitter API v2 Setup & Integration Guide

**Objective**: Set up Twitter API v2 credentials and integrate with n8n for automated Twitter thread posting

**Status**: Ready to implement
**Estimated Setup Time**: 20-30 minutes
**Cost**: Free (X Developer Program)

---

## Table of Contents
1. [Create Twitter Developer Account](#create-twitter-developer-account)
2. [Get API Credentials](#get-api-credentials)
3. [Understand API Limits & Endpoints](#understand-api-limits--endpoints)
4. [n8n Integration](#n8n-integration)
5. [Twitter Thread Posting Workflow](#twitter-thread-posting-workflow)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)

---

## Create Twitter Developer Account

### **Step 1: Register Developer Account**

1. Go to [Twitter Developer Portal](https://developer.twitter.com)
2. Click **"Sign Up"** (top right)
3. Sign in with your Twitter account (or create new one)
4. Fill out the form:
   - **Username**: Your Twitter handle
   - **Email**: Your email
   - **Phone**: Your phone number (Twitter verification)
   - **Country**: Select your country
5. Accept terms and click **"Next"**

### **Step 2: Create Developer Account Details**

Fill out the form with:
- **Account Name**: "Personal Content Automation" or similar
- **Use Case**: Select "Automation"
- **Use Case Details**: 
  ```
  I'm building an automated LinkedIn and Twitter content creator that:
  - Scrapes trending topics from Twitter and other sources
  - Uses AI (Gemini) to generate professional content
  - Auto-posts to Twitter using the official API
  - Tracks engagement metrics for personal branding
  ```
- **Are you planning to analyze Twitter data?**: No
- **Will your app use Tweet, Retweet, or Like functionality?**: Yes
- **Will your app display Tweets or aggregate data about Twitter in a feed or timeline?**: No
- **Will you make Tweet content or Twitter handles the centerpiece of your product or service?**: No

Click **"Next"** and finalize.

### **Step 3: Verify Email**

- Twitter sends verification email
- Click the link to confirm
- Account is now active

### **Step 4: Create Application**

1. Go to [Developer Portal Dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Click **"Create App"** button
3. Fill in:
   - **App Name**: `content-automation-bot` (or your preference)
   - **App ID**: Auto-generated
   - **Description**: "Automated content creator for Twitter and LinkedIn using AI"

4. Click **"Create"**

---

## Get API Credentials

### **Step 1: Generate Bearer Token**

1. In Developer Portal, select your app
2. Go to **"Keys and Tokens"** tab
3. Under **API Keys**:
   - You'll see **API Key** (also called Consumer Key)
   - You'll see **API Secret Key** (also called Consumer Secret)
   - **Save these securely** (we'll use for Bearer Token)

4. Scroll down to **Authentication Tokens & Keys**
5. Click **"Generate"** under **Bearer Token**
   - This generates a read/write token
   - **Copy the token immediately** (you can't view it again)
   - **Save**: `TWITTER_BEARER_TOKEN`

### **Step 2: Generate Access Tokens (Optional - for elevated access)**

For writing tweets, you may need:
1. Click **"Generate"** under **Access Token & Secret**
   - Generates `ACCESS_TOKEN` 
   - Generates `ACCESS_TOKEN_SECRET`
   - **Copy both immediately**
   - **Save**: `TWITTER_ACCESS_TOKEN` and `TWITTER_ACCESS_TOKEN_SECRET`

### **Step 3: Enable OAuth 1.0a + 2.0 (If needed)**

1. Go to **"App Settings"** tab
2. Scroll to **Authentication Settings**
3. Toggle **"OAuth 1.0a"** = ON
   - Set **Callback URLs**: `http://localhost:3000/callback` (for testing)
   - Set **Website URL**: Your website (or `http://localhost` for dev)
   - Set **Privacy Policy**: Link to your privacy policy
   - Set **Terms of Service**: Link to your ToS

4. Toggle **"OAuth 2.0"** = ON (recommended)
   - Set similar callback URLs
   - **Save**

### **Step 4: Store Credentials Securely**

Create a `.env` file in your n8n instance:
```env
TWITTER_BEARER_TOKEN=AAAA...YourTokenHere
TWITTER_API_KEY=abc123...
TWITTER_API_SECRET=xyz789...
TWITTER_ACCESS_TOKEN=optional...
TWITTER_ACCESS_TOKEN_SECRET=optional...
```

**IMPORTANT**: Never commit `.env` to git. Use n8n's credential system instead:
1. n8n Dashboard → **Credentials** (left sidebar)
2. Click **"+ New"**
3. Select **"Twitter" or "HTTP Header Auth"**
4. Paste your Bearer Token
5. Save as **"Twitter API v2"**

---

## Understand API Limits & Endpoints

### **Rate Limits (Free Tier)**

| Endpoint | Limit | Reset |
|----------|-------|-------|
| `/2/tweets` (Create) | 300 per 15 min | Every 15 minutes |
| `/2/tweets/search/recent` | 450 per 15 min | Every 15 minutes |
| `/2/tweets/:id` (Lookup) | 300 per 15 min | Every 15 min |
| `/2/tweets/search/all` | 10 per month | Monthly |

**For our use case**: We create 1 tweet every 24 hours (well within 300/15min limit).

### **Key Endpoints for This Project**

#### **1. Create Tweet**
```
POST /2/tweets
```
Payload:
```json
{
  "text": "Your tweet content here (280 chars max)"
}
```
Response:
```json
{
  "data": {
    "id": "1234567890",
    "text": "Your tweet content here"
  }
}
```

#### **2. Create Tweet Reply**
```
POST /2/tweets
```
Payload (for thread):
```json
{
  "text": "Reply tweet content",
  "reply": {
    "in_reply_to_tweet_id": "1234567890"
  }
}
```

#### **3. Search Recent Tweets**
```
GET /2/tweets/search/recent?query=...&max_results=100&tweet.fields=public_metrics
```

#### **4. Tweet Preview**
```
GET /2/tweets/1234567890?tweet.fields=public_metrics,created_at
```

---

## n8n Integration

### **Method 1: Using n8n Twitter Node (Recommended)**

1. In n8n, create new workflow
2. Add node → Search **"Twitter"**
3. Select **"Twitter"** node (official integration)
4. Click **"Create new credential"**
5. Select **"Twitter"** credential type
6. Paste your **Bearer Token**
7. Test connection

### **Method 2: Using HTTP Request Node (More Flexible)**

If the official node is outdated, use HTTP Request:

**For Posting Tweet:**
```
Type: HTTP Request
Method: POST
URL: https://api.twitter.com/2/tweets
Headers:
  Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}
  Content-Type: application/json

Body (JSON):
{
  "text": "{{ your_tweet_content }}"
}
```

**For Replying (Thread):**
```
Type: HTTP Request
Method: POST
URL: https://api.twitter.com/2/tweets
Headers:
  Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}
  Content-Type: application/json

Body (JSON):
{
  "text": "{{ reply_content }}",
  "reply": {
    "in_reply_to_tweet_id": "{{ previous_tweet_id }}"
  }
}
```

---

## Twitter Thread Posting Workflow

### **Complete Node Structure for Posting Threads**

**Example**: 3-tweet thread on a trending AI topic

#### **Node 1: Prepare Thread Content**
Type: Code Node
```javascript
// Input: 3 generated tweets from Gemini
const tweets = $input.first().json;

// Ensure proper format
const threadTweets = [
  {
    text: tweets.tweet_1,
    order: 1
  },
  {
    text: tweets.tweet_2,
    order: 2
  },
  {
    text: tweets.tweet_3,
    order: 3
  }
];

// Validate each tweet
threadTweets.forEach((t, i) => {
  if (t.text.length > 280) {
    throw new Error(`Tweet ${i+1} exceeds 280 characters: ${t.text.length} chars`);
  }
  if (!t.text.trim()) {
    throw new Error(`Tweet ${i+1} is empty`);
  }
});

return {
  tweets: threadTweets,
  threadCount: threadTweets.length,
  totalChars: threadTweets.reduce((sum, t) => sum + t.text.length, 0)
};
```

#### **Node 2: Post Tweet #1 (Thread Starter)**
Type: HTTP Request
```
POST https://api.twitter.com/2/tweets

Headers:
  Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}
  Content-Type: application/json

Body:
{
  "text": "{{ $node['Prepare Thread Content'].json.tweets[0].text }}"
}
```

Output stores `response.data.id` (tweet ID for replies)

#### **Node 3: Extract Tweet #1 ID**
Type: Code Node
```javascript
const response = $input.first().json;

if (!response.data || !response.data.id) {
  throw new Error('Failed to create tweet: ' + JSON.stringify(response));
}

return {
  tweet_1_id: response.data.id,
  tweet_1_text: response.data.text,
  tweet_1_url: `https://twitter.com/i/web/status/${response.data.id}`
};
```

#### **Node 4: Post Tweet #2 (Reply to #1)**
Type: HTTP Request
```
POST https://api.twitter.com/2/tweets

Headers:
  Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}
  Content-Type: application/json

Body:
{
  "text": "{{ $node['Prepare Thread Content'].json.tweets[1].text }}",
  "reply": {
    "in_reply_to_tweet_id": "{{ $node['Extract Tweet #1 ID'].json.tweet_1_id }}"
  }
}
```

#### **Node 5: Extract Tweet #2 ID**
Same pattern as Node 3, stores Tweet #2 ID

#### **Node 6: Post Tweet #3 (Reply to #2)**
Type: HTTP Request
```
POST https://api.twitter.com/2/tweets

Body:
{
  "text": "{{ $node['Prepare Thread Content'].json.tweets[2].text }}",
  "reply": {
    "in_reply_to_tweet_id": "{{ $node['Extract Tweet #2 ID'].json.tweet_2_id }}"
  }
}
```

#### **Node 7: Compile Thread Metadata**
Type: Code Node
```javascript
return {
  thread_complete: true,
  tweet_count: 3,
  first_tweet_id: $node['Extract Tweet #1 ID'].json.tweet_1_id,
  last_tweet_id: $node['Extract Tweet #3 ID'].json.tweet_3_id,
  thread_url: `https://twitter.com/i/web/status/${$node['Extract Tweet #1 ID'].json.tweet_1_id}`,
  posted_at: new Date().toISOString(),
  tweets: [
    $node['Extract Tweet #1 ID'].json.tweet_1_url,
    $node['Extract Tweet #2 ID'].json.tweet_2_url,
    $node['Extract Tweet #3 ID'].json.tweet_3_url
  ]
};
```

#### **Node 8: Store in Database**
Type: Supabase/PostgreSQL
```sql
INSERT INTO content_posts 
(topic, content, twitter_thread_ids, twitter_urls, posted_at, status)
VALUES 
($1, $2, $3, $4, $5, 'posted')
```

Parameters:
- $1: Topic
- $2: Combined tweet text
- $3: JSON array of tweet IDs
- $4: JSON array of URLs
- $5: NOW()

#### **Node 9: Send Slack Notification**
Type: Slack
```
Message:
🐦 Twitter Thread Posted Successfully!

📌 Topic: {{ topic }}
🧵 Thread: {{ $node['Compile Thread Metadata'].json.thread_url }}
📝 Tweets: {{ $node['Compile Thread Metadata'].json.tweet_count }}

Tweet 1: {{ $node['Compile Thread Metadata'].json.tweets[0] }}
Tweet 2: {{ $node['Compile Thread Metadata'].json.tweets[1] }}
Tweet 3: {{ $node['Compile Thread Metadata'].json.tweets[2] }}

⏩ Check engagement in 1 hour
```

---

## Testing & Validation

### **Test 1: Connection Test**

In n8n, create a test workflow:

```
1. HTTP Request node
   - Method: GET
   - URL: https://api.twitter.com/2/tweets/search/recent?query=test&max_results=10
   - Header: Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}
   
2. Run workflow
3. If you get results, connection is working ✅
```

### **Test 2: Create Single Tweet**

```
1. Code node:
   return { text: "Testing Twitter API v2 from n8n! #AI #Automation" };

2. HTTP Request:
   POST https://api.twitter.com/2/tweets
   Body: { "text": "{{ $node['Code'].json.text }}" }

3. If you get tweet ID back, posting works ✅
```

**Verify**: Go to your Twitter profile → should see the test tweet

### **Test 3: Create Thread**

```
1. Create 3 separate tweets
2. Use reply functionality
3. Verify they appear as thread on Twitter
4. Check thread looks correct
```

### **Test 4: Retrieve Tweet Data**

```
GET /2/tweets/{{ tweet_id }}?tweet.fields=public_metrics,created_at

Should return:
- like_count
- retweet_count
- reply_count
- created_at
```

---

## Twitter Thread Format Guide

### **Best Practices for Twitter Threads**

**1. First Tweet (Hook)**
- Should grab attention immediately
- 120-200 characters (leave room for engagement)
- Question, bold statement, or controversy
- Optional: Add relevant emoji

Example:
```
🔥 AI agents are about to change everything for automation.

Here's why... (1/)
```

**2. Middle Tweets (Value)**
- One insight per tweet
- Actionable advice or unique perspective
- Use line breaks for readability
- Reference data/stats when possible

Example:
```
Most teams are STILL building AI agents wrong.

They treat them like chatbots.

They're not.

Agents should:
✅ Make autonomous decisions
✅ Execute tasks without human input
✅ Learn from failures

(2/)
```

**3. Final Tweet (CTA)**
- Call-to-action (follow, reply, link)
- Key takeaway
- Invite engagement
- Add hashtags here

Example:
```
The future of work isn't AI vs humans.

It's humans + autonomous agents.

If you're not building with agents, you're falling behind.

What's your biggest AI challenge? 👇

#AI #Automation #FutureOfWork (3/)
```

### **Thread Generation Prompt (For Gemini)**

```
You are a Twitter expert creating viral threads on AI and automation.

Topic: {trending_topic}

Create a 3-tweet thread that:
1. First tweet: Bold statement/hook (max 280 chars, include 1/)
2. Second tweet: Valuable insight (max 280 chars, include 2/)
3. Third tweet: CTA + takeaway (max 280 chars, include 3/)

RULES:
- Each tweet must be under 280 characters
- Use line breaks for readability
- Only add hashtags on final tweet
- Be specific and actionable
- Avoid generic content

Format output as JSON:
{
  "tweet_1": "text",
  "tweet_2": "text", 
  "tweet_3": "text"
}
```

---

## Complete Workflow JSON (Twitter Integration)

Save as `twitter-thread-automation.json`:

```json
{
  "name": "Twitter Thread Automation",
  "nodes": [
    {
      "parameters": {
        "jsCode": "return {\n  tweets: {\n    tweet_1: \"🔥 AI agents are about to change everything for automation (1/)\",\n    tweet_2: \"Most teams are building agents wrong. They should be autonomous. (2/)\",\n    tweet_3: \"The future of work isn't AI vs humans. It's both together. #AI #Automation (3/)\"\n  }\n};"
      },
      "id": "1",
      "name": "Generate Tweet Content",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [100, 100]
    },
    {
      "parameters": {
        "jsCode": "const tweets = $input.first().json.tweets;\nconst threadTweets = [\n  { text: tweets.tweet_1, order: 1 },\n  { text: tweets.tweet_2, order: 2 },\n  { text: tweets.tweet_3, order: 3 }\n];\nthreadTweets.forEach((t, i) => {\n  if (t.text.length > 280) throw new Error(`Tweet ${i+1} too long: ${t.text.length} chars`);\n});\nreturn { tweets: threadTweets, count: 3 };"
      },
      "id": "2",
      "name": "Validate Tweets",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [250, 100]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets",
        "method": "POST",
        "bodyType": "json",
        "body": "{ \"text\": \"{{ $node['Validate Tweets'].json.tweets[0].text }}\" }",
        "options": {
          "headers": {
            "parameters": [
              {
                "name": "Authorization",
                "value": "Bearer {{ $env.TWITTER_BEARER_TOKEN }}"
              }
            ]
          }
        }
      },
      "id": "3",
      "name": "Post Tweet 1",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [100, 250]
    },
    {
      "parameters": {
        "jsCode": "const id = $input.first().json.data.id;\nif (!id) throw new Error('No tweet ID returned');\nreturn { tweet_1_id: id };"
      },
      "id": "4",
      "name": "Extract Tweet 1 ID",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [250, 250]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets",
        "method": "POST",
        "bodyType": "json",
        "body": "{ \"text\": \"{{ $node['Validate Tweets'].json.tweets[1].text }}\", \"reply\": { \"in_reply_to_tweet_id\": \"{{ $node['Extract Tweet 1 ID'].json.tweet_1_id }}\" } }",
        "options": {
          "headers": {
            "parameters": [
              {
                "name": "Authorization",
                "value": "Bearer {{ $env.TWITTER_BEARER_TOKEN }}"
              }
            ]
          }
        }
      },
      "id": "5",
      "name": "Post Tweet 2",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [100, 400]
    },
    {
      "parameters": {
        "jsCode": "const id = $input.first().json.data.id;\nif (!id) throw new Error('No tweet ID returned');\nreturn { tweet_2_id: id };"
      },
      "id": "6",
      "name": "Extract Tweet 2 ID",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [250, 400]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets",
        "method": "POST",
        "bodyType": "json",
        "body": "{ \"text\": \"{{ $node['Validate Tweets'].json.tweets[2].text }}\", \"reply\": { \"in_reply_to_tweet_id\": \"{{ $node['Extract Tweet 2 ID'].json.tweet_2_id }}\" } }",
        "options": {
          "headers": {
            "parameters": [
              {
                "name": "Authorization",
                "value": "Bearer {{ $env.TWITTER_BEARER_TOKEN }}"
              }
            ]
          }
        }
      },
      "id": "7",
      "name": "Post Tweet 3",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [100, 550]
    },
    {
      "parameters": {
        "jsCode": "return { thread_url: `https://twitter.com/i/web/status/${$node['Extract Tweet 1 ID'].json.tweet_1_id}`, tweets_posted: 3 };"
      },
      "id": "8",
      "name": "Compile Results",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [250, 550]
    },
    {
      "parameters": {
        "channel": "#automation",
        "text": "🐦 Twitter thread posted!\\n{{ $node['Compile Results'].json.thread_url }}"
      },
      "id": "9",
      "name": "Slack Notification",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2,
      "position": [400, 400]
    }
  ],
  "connections": {
    "Generate Tweet Content": { "main": [[{ "node": "Validate Tweets", "type": "main", "index": 0 }]] },
    "Validate Tweets": { "main": [[{ "node": "Post Tweet 1", "type": "main", "index": 0 }]] },
    "Post Tweet 1": { "main": [[{ "node": "Extract Tweet 1 ID", "type": "main", "index": 0 }]] },
    "Extract Tweet 1 ID": { "main": [[{ "node": "Post Tweet 2", "type": "main", "index": 0 }]] },
    "Post Tweet 2": { "main": [[{ "node": "Extract Tweet 2 ID", "type": "main", "index": 0 }]] },
    "Extract Tweet 2 ID": { "main": [[{ "node": "Post Tweet 3", "type": "main", "index": 0 }]] },
    "Post Tweet 3": { "main": [[{ "node": "Compile Results", "type": "main", "index": 0 }]] },
    "Compile Results": { "main": [[{ "node": "Slack Notification", "type": "main", "index": 0 }]] }
  }
}
```

---

## Troubleshooting

### **Issue: 401 Unauthorized**
**Cause**: Invalid or expired Bearer Token

**Fix**:
1. Go to Twitter Developer Portal
2. Regenerate Bearer Token
3. Update in n8n credentials
4. Test connection again

### **Issue: 403 Forbidden**
**Cause**: Account not approved for v2 API or insufficient permissions

**Fix**:
1. Check email for Twitter API approval
2. May need to wait 24-48 hours after registration
3. Try creating app under different name
4. Contact Twitter support if still blocked

### **Issue: Tweet exceeds 280 characters**
**Cause**: Content longer than limit

**Fix**:
1. Check validation code catches this
2. Reduce tweet length in generation prompt
3. Add character counter to validation code
4. Could use Twitter's threading to split content

### **Issue: Thread not appearing in correct order**
**Cause**: Tweets posting too fast, Twitter hasn't updated

**Fix**:
1. Add 1-2 second delay between tweets:
   ```javascript
   // In n8n Code node
   await new Promise(resolve => setTimeout(resolve, 2000));
   ```
2. Tweet IDs may take seconds to propagate
3. Wait 5 seconds before next reply

### **Issue: Rate limit exceeded**
**Cause**: Too many API calls in 15-minute window

**Fix**:
1. We're well under limit (1 tweet/day vs 300/15min)
2. If occurring: add retry with exponential backoff
3. Check if multiple workflows running simultaneously
4. Stagger workflow execution times

### **Issue: Character encoding issues**
**Cause**: Emojis or special characters breaking API

**Fix**:
1. Ensure JSON payload is UTF-8 encoded
2. Test with emoji in Tweet content
3. Some emojis count as multiple characters
4. Use simple formatting if issues persist

---

## Integration Checklist

- [ ] Create Twitter Developer Account
- [ ] Create Application
- [ ] Generate Bearer Token
- [ ] Store token in n8n credentials as `TWITTER_BEARER_TOKEN`
- [ ] Test connection with simple GET request
- [ ] Test creating single tweet
- [ ] Test creating thread (3 tweets)
- [ ] Verify tweets appear on profile
- [ ] Set up error handling
- [ ] Add Slack/email notifications
- [ ] Ready to integrate with main LinkedIn Content Creator workflow

---

## Next Steps

1. **Complete the setup above** (should take ~20 minutes)
2. **Test each API endpoint** in the workflow
3. **Verify tweets appear** on your Twitter profile
4. **Integrate with main workflow** (from LinkedIn implementation guide)
   - Add Twitter posting after content generation
   - Use same Gemini-generated content
   - Post both LinkedIn + Twitter simultaneously

---

## Final Integration: LinkedIn + Twitter Combined

Once both are set up, your complete workflow will be:

```
1. Trigger (Daily 8 AM)
   │
2. Data Collection (trending topics)
   │
3. RAG Retrieval (personal expertise)
   │
4. Content Generation (Gemini)
   │
5. BRANCH HERE
   ├─ LinkedIn Posting Workflow
   │  └─ Schedule + Post + Notify
   │
   └─ Twitter Posting Workflow
      └─ Generate thread + Post 3 tweets + Notify
```

Both workflows run in parallel, so your content reaches both platforms simultaneously every day!

Ready to implement?
