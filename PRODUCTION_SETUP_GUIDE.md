# Production Architecture Setup Guide
## LinkedIn & Twitter Automation with Pinecone + Gemini APIs + Twitter Puppeteer Workaround

This guide walks through setting up the **full production architecture** specified in `LINKEDIN_TWITTER_AUTOMATION_PLAN.md` with the required modifications:
- **Vector Database**: Pinecone (instead of Supabase)
- **Twitter Posting**: Puppeteer browser automation workaround for API paywall
- **Everything else**: Exactly as specified in the original plan

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY TRIGGER (8 AM UTC)                 │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┬──────────────┬──────────────┐
    ▼            ▼              ▼              ▼              ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐ ┌────────┐
│Twitter │ │Reddit  │ │ NewsAPI  │ │HackerNews  │ │Aggregate│
│Search  │ │API     │ │ API      │ │API         │ │Topics  │
└────────┘ └────────┘ └──────────┘ └────────────┘ └────────┘
    │            │              │              │              │
    └────────────┴──────────────┴──────────────┴──────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Rank & Score (JS)   │
                    │ Select Top 5 Topics │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼─────────────┐
                    │ Generate Embeddings   │
                    │ (Gemini API - 768D)   │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Query Pinecone Know-│
                    │ ledge Base (Top-K=5)│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Prepare RAG Context │
                    │(Topic + Expertise)  │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                              │
        ▼                                              ▼
    ┌────────────────────┐          ┌────────────────────────┐
    │Generate LinkedIn   │          │Generate Twitter Thread │
    │Post (Gemini)       │          │(Gemini - 3-5 tweets)   │
    │(300-400 chars)     │          │(280 chars/tweet max)   │
    └────────┬───────────┘          └──────────┬─────────────┘
             │                                  │
    ┌────────▼──────────────────────────────────▼────────────┐
    │         Validate All Content (JS Checks)               │
    │  - Length checks, hashtags, tweet char limits          │
    └────────┬──────────────────────────────────┬────────────┘
             │                                  │
    ┌────────▼──────────────┐      ┌───────────▼────────────┐
    │ Schedule LinkedIn     │      │ Schedule Twitter       │
    │ (8 AM/1 PM/5 PM)      │      │ (9 AM/2 PM/7 PM)      │
    └────────┬──────────────┘      └───────────┬────────────┘
             │                                  │
    ┌────────▼──────────────┐      ┌───────────▼────────────┐
    │Post to LinkedIn       │      │Post to Twitter         │
    │(Official API/OAuth)   │      │(Puppeteer Automation)  │
    └────────┬──────────────┘      └───────────┬────────────┘
             │                                  │
    ┌────────▼────────────────────────────────▼──────────────┐
    │     Store Posting History in Pinecone                 │
    │  (Vector + metadata for future reference learning)    │
    └────────┬────────────────────────────────┬──────────────┘
             │                                │
             └────────────────┬───────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Send Email Alert   │
                    │ (Success/Failure)  │
                    └────────────────────┘
```

---

## Prerequisites

### 1. API Keys and Credentials Required

| Service | Use Case | Cost | Setup |
|---------|----------|------|-------|
| **Google Gemini API** | LLM for content generation | $0.70/month | [Create API key](https://aistudio.google.com/) |
| **Pinecone** | Vector database (knowledge base) | Free tier: 1 index, 100K vectors | [Create account](https://www.pinecone.io/) |
| **Twitter API v2** | Data collection (trending) | Free | Existing Twitter account + API keys |
| **Reddit API** | Trending discussions | Free | Create app at reddit.com/prefs/apps |
| **NewsAPI** | Industry news | Free tier: 100/day | [Create key](https://newsapi.org/) |
| **LinkedIn OAuth** | Official posting API | Free | LinkedIn Developer app |
| **Puppeteer + Chrome** | Twitter posting workaround | Free | Local installation (included) |

### 2. System Requirements

- **Node.js** 16+ (for n8n and Puppeteer)
- **Python** 3.8+ (for Pinecone integration scripts)
- **Chrome/Chromium** browser (for Puppeteer)
- **n8n** (self-hosted or cloud)
- **4GB RAM minimum**, 2GB storage

---

## Step-by-Step Setup

### Phase 1: Create API Credentials

#### 1.1 Google Gemini API

```bash
# 1. Go to: https://aistudio.google.com/app/apikeys
# 2. Click "Create API Key"
# 3. Copy the key to .env file:

GEMINI_API_KEY=your_api_key_here
```

**Verify it works:**
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

#### 1.2 Pinecone Setup

```bash
# 1. Create free account: https://www.pinecone.io/
# 2. Create serverless index named "linkedin-knowledge-base"
#    - Dimension: 768 (for Gemini embeddings)
#    - Metric: cosine
#    - Cloud: AWS, Region: us-east-1
# 3. Get API key from console and add to .env:

PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=production
```

**Test Pinecone connection:**
```bash
python pinecone_integration.py
```

Expected output:
```
Initializing Pinecone index...
Index Status: {'name': 'linkedin-knowledge-base', 'dimension': 768, ...}
✅ Pinecone integration ready!
```

#### 1.3 Twitter API Keys

```bash
# 1. Go to: https://developer.twitter.com/en/portal/dashboard
# 2. Create/use existing Project and App
# 3. Generate API Keys v2 with "Read" access:

TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Get User ID (needed for Puppeteer posting):
TWITTER_USER_ID=your_numeric_user_id
TWITTER_EMAIL=your_twitter_email@gmail.com
TWITTER_PASSWORD=your_twitter_password  # Store securely!
```

#### 1.4 Reddit API Keys

```bash
# 1. Go to: https://www.reddit.com/prefs/apps
# 2. Create "script" app
# 3. Get credentials:

REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=MyContentBot/1.0 (User)
```

#### 1.5 NewsAPI Key

```bash
# 1. Go to: https://newsapi.org/register
# 2. Create account and get API key:

NEWSAPI_KEY=your_api_key_here
```

#### 1.6 LinkedIn OAuth Setup

```bash
# 1. Create app at: https://www.linkedin.com/developers/apps
# 2. Get credentials:

LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_REDIRECT_URI=http://localhost:3000/callback
LINKEDIN_ACCESS_TOKEN=oauth_token_obtained_from_login
LINKEDIN_USER_ID=urn:li:person:YOUR_NUMERIC_ID
```

### Phase 2: Environment Configuration

Create `.env` file in workspace root:

```bash
# === GEMINI APIs ===
GEMINI_API_KEY=your_gemini_api_key_here

# === PINECONE VECTOR DB ===
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=production

# === DATA COLLECTION APIs ===
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_USER_ID=YOUR_NUMERIC_TWITTER_ID
TWITTER_EMAIL=your_email@example.com
TWITTER_PASSWORD=your_password_encrypted

REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=MyBot/1.0

NEWSAPI_KEY=your_newsapi_key

# === LINKEDIN API ===
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_secret
LINKEDIN_ACCESS_TOKEN=your_oauth_token
LINKEDIN_USER_ID=urn:li:person:YOUR_NUMERIC_ID

# === NOTIFICATIONS ===
NOTIFICATION_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password

# === SCHEDULING ===
TIMEZONE=UTC
POST_SCHEDULE_LINKEDIN=08:00,13:00,17:00
POST_SCHEDULE_TWITTER=09:00,14:00,19:00
```

⚠️ **Important**: Never commit `.env` to version control. Add to `.gitignore`:
```
.env
.env.local
credentials/
```

### Phase 3: Set Up n8n Workflow

#### 3.1 Import Workflow

1. Open n8n
2. Click "Import" → "From File"
3. Load `linkedin-twitter-automation-production.json`
4. Click "Import"

#### 3.2 Configure Credentials in n8n

For each API connection in the workflow:

1. **Gemini API Nodes** (Nodes 6, 9, 11):
   - Click node → "Add credential"
   - Type: "HTTP Header Auth"
   - Header: `x-goog-api-key`
   - Header Value: `{{$env.GEMINI_API_KEY}}`

2. **Pinecone Nodes** (Nodes 5, 7, 19):
   - Click node → "Add credential"
   - Type: "Custom API"
   - URL: `https://api.pinecone.io/v1`
   - Header: `Api-Key: {{$env.PINECONE_API_KEY}}`

3. **Twitter API Node** (Node 2):
   - Click node → "Add credential" 
   - Type: "Twitter API"
   - Set Bearer Token: `{{$env.TWITTER_BEARER_TOKEN}}`

4. **LinkedIn API Node** (Node 14):
   - Click node → "Add credential"
   - Type: "LinkedIn OAuth2 API"
   - Client ID: `{{$env.LINKEDIN_CLIENT_ID}}`
   - Client Secret: `{{$env.LINKEDIN_CLIENT_SECRET}}`
   - Authenticate to get access token

5. **Email Notification Nodes** (Nodes 21, Error Handler):
   - Click node → "Add credential"
   - Type: "Gmail" 
   - App Password: `{{$env.GMAIL_APP_PASSWORD}}`

#### 3.3 Node-by-Node Configuration

| Node | Configuration | Parameters |
|------|---------------|------------|
| Schedule Trigger | Cron every day | 08:00 UTC |
| Twitter Trends | HTTP GET | `q=AI OR automation` |
| Reddit | HTTP GET | `/r/MachineLearning/top.json` |
| NewsAPI | HTTP GET | `query=AI OR ChatGPT` |
| HackerNews | HTTP GET | Top stories endpoint |
| Merge & Aggregate | JavaScript | Deduplicate sources |
| Rank Topics | JavaScript | Score & select top 5 |
| Generate Embeddings | Gemini API | 768-dimensional vectors |
| Query Pinecone | HTTP POST | top-K=5 retrieval |
| Prepare Context | JavaScript | Merge topic + expertise |
| Generate LinkedIn | Gemini 1.5 Flash | 300-400 character post |
| Generate Twitter | Gemini 1.5 Flash | 3-5 tweets × 280 chars |
| Validate Content | JavaScript | Checks & validation |
| Schedule LinkedIn | JavaScript | Optimal times logic |
| Schedule Twitter | JavaScript | Optimal times logic |
| Post LinkedIn | LinkedIn API | OAuth posting |
| Post Twitter | Execute Command | `node post_to_twitter.js` |
| Confirmations | JavaScript | Status tracking |
| Store History | Pinecone API | Vector embedding + metadata |
| Email Alerts | Gmail | Success/failure notifications |

### Phase 4: Twitter Puppeteer Workaround Setup

#### 4.1 Install Puppeteer

```bash
npm install puppeteer --save
npm install dotenv
```

#### 4.2 Verify Post Script

File: `post_to_twitter.js` (already created)

**Test to Twitter manually:**
```bash
node post_to_twitter.js '["1/ First tweet here", "2/ Reply tweet here"]'
```

Expected output:
```json
{
  "success": true,
  "tweetsPosted": 2,
  "tweetIds": ["1234567890", "1234567891"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 4.3 LinkedIn Puppeteer (Optional Backup)

Similarly, `post_to_linkedin.js` is available if official API fails.

### Phase 5: Pinecone Knowledge Base Initialization

#### 5.1 Seed with Initial Content

Create `seed_knowledge_base.py`:

```python
from pinecone_integration import PineconeIntegration
import json

# Initialize
pc = PineconeIntegration()

# Example knowledge items with embeddings
knowledge_items = [
    {
        "id": "expertise_001",
        "content": "RAG (Retrieval Augmented Generation) systems improve LLM accuracy by providing domain-specific context. They store embeddings of company documents, research papers, or historical data, then retrieve relevant pieces during generation.",
        "topic": "AI/ML",
        "source": "internal",
        "embedding_vector": [0.1, 0.2, 0.3] * 256  # Placeholder (generate real embeddings)
    },
    {
        "id": "expertise_002", 
        "content": "Automation workflows using n8n reduce manual work by 80%. Key use cases: data collection, API orchestration, scheduled posting, and error handling.",
        "topic": "automation",
        "source": "internal",
        "embedding_vector": [0.2, 0.3, 0.4] * 256
    }
]

# Seed knowledge base
result = pc.seed_knowledge_base(knowledge_items)
print(json.dumps(result, indent=2))
```

Run:
```bash
python seed_knowledge_base.py
```

### Phase 6: Test the Full Workflow

#### 6.1 Single Test Execution

1. Open n8n workflow
2. Click "Execute Workflow"
3. Monitor each node's output
4. Check for error messages

#### 6.2 Check Generated Content

After successful run, verify:
- ✅ LinkedIn post generated (300-400 chars)
- ✅ Twitter thread generated (3-5 tweets, 280 chars each)
- ✅ Posts posted to platforms
- ✅ History stored in Pinecone
- ✅ Email notification received

#### 6.3 Verify Pinecone Storage

```bash
python -c "
from pinecone_integration import PineconeIntegration
pc = PineconeIntegration()
stats = pc.get_index_stats()
print(f'Vectors in index: {stats.get(\"total_vector_count\", 0)}')
"
```

---

## Optimal Posting Times

### LinkedIn
- **08:00 UTC** - Wednesday mornings (highest engagement)
- **13:00 UTC** - Afternoon post
- **17:00 UTC** - Evening post

### Twitter
- **09:00 UTC** - Morning (East Coast business hours)
- **14:00 UTC** - Afternoon (peak US engagement)
- **19:00 UTC** - Evening (international users)

Adjust `POST_SCHEDULE_*` in `.env` to match your timezone.

---

## Cost Breakdown

| Service | Free/Tier | Monthly Cost | Notes |
|---------|-----------|--------------|-------|
| Gemini API | Usage-based | ~$0.70 | 1M embeddings @ $0.02/1K, 3M generation tokens @ $0.20/1M |
| Pinecone | Free tier | $0 | 100K vectors, 1 index (can scale to $35/month) |
| Twitter API | Premium tier | $100 | Free tier has read-only access, paid for write access |
| Reddit API | Free | $0 | None |
| NewsAPI | Free tier | $0 | 100 requests/day (can upgrade to $50/month) |
| LinkedIn API | Free | $0 | Rate limited but free for personal use |
| n8n | Self-hosted | $0 | Electricity cost only (~$5/month) |
| **TOTAL** | | **$100.70+** | Mostly Twitter API paywall |

**With Puppeteer workaround (no Twitter API upgrade needed):** ~$0.70/month

---

## Troubleshooting

### Common Issues

#### "Invalid Pinecone API Key"
```bash
# Verify key is set:
echo $PINECONE_API_KEY

# Check index name matches:
python -c "from pinecone_integration import PineconeIntegration; pc = PineconeIntegration(); print(pc.index_name)"
```

#### "Twitter Authentication Failed (401)"
```bash
# This is expected with free tier (read-only)
# Puppeteer workaround handles this automatically
# Verify Puppeteer script runs:
node post_to_twitter.js '["test tweet"]'
```

#### "Gemini API Returns Empty Response"
```bash
# Check API key has Gemini access enabled
# Verify in Google Cloud Console:
# - APIs & Services → Enabled APIs
# - Should see "Generative Language API" (enable if missing)
# - Check quota limits
```

#### "LinkedIn OAuth Token Expired"
```bash
# Re-authenticate:
# 1. Click LinkedIn node in n8n
# 2. Click "Re-authenticate"
# 3. Complete OAuth flow
# 4. New token auto-stored
```

---

## Maintenance & Monitoring

### Daily Checks
- Monitor n8n workflow logs for errors
- Check email alerts arrive 
- Spot-check LinkedIn/Twitter posts are correctly posted

### Weekly Tasks
- Review Pinecone vector count (should grow daily)
- Check API usage stays under free tier limits
- Validate post engagement metrics

### Monthly Tasks
- Refresh knowledge base with new expertise
- Analyze trending topics effectiveness
- Optimize prompts if content quality drops
- Rotate API keys (security best practice)

---

## Next Steps

1. **Immediate**: Set up all API keys (Section 1)
2. **Setup**: Configure environment (Section 2)
3. **Integration**: Import and configure n8n workflow (Section 3)
4. **Testing**: Run full test execution (Section 6)
5. **Deployment**: Enable daily schedule trigger in n8n
6. **Monitoring**: Set up logging/alerts in n8n

---

## References

- [n8n Documentation](https://docs.n8n.io/)
- [Pinecone Getting Started](https://docs.pinecone.io/guides/getting-started)
- [Google Gemini API](https://ai.google.dev/)
- [Twitter API v2 Docs](https://developer.twitter.com/en/docs/twitter-api)
- [Puppeteer Documentation](https://pptr.dev/)
- [LinkedIn Developer Docs](https://learn.microsoft.com/en-us/linkedin/shared/references/reference-v2-api-docs?context=linkedin%2Fcontext)

---

**Architecture Version**: 1.0 (Production)  
**Last Updated**: January 2024  
**Maintained By**: n8n Automation System
