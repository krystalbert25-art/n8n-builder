# Automated LinkedIn & Twitter Content Creator - Detailed Architecture Plan

**Project Overview**: Fully automated daily content creation system that scrapes trending topics, uses RAG to enhance content with personal expertise, generates high-quality posts via Gemini AI, and auto-posts to LinkedIn and Twitter.

**Tech Stack**: n8n + Pinecone + Google Gemini + APIs
**Cost Estimate**: $5-15/month (primarily Gemini API usage)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY TRIGGER (8 AM UTC)                     │
└────────────────┬────────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │   DATA COLLECTION PHASE │
    └────────────┬────────────┘
         │       │       │       │
    ┌────▼─┐ ┌──▼──┐ ┌─▼───┐ ┌─▼────┐
    │Reddit│ │Twitter│ │News│ │RSS   │
    │Topics│ │Trends │ │API │ │Feeds │
    └────┬─┘ └──┬──┘ └──┬──┘ └──┬───┘
         │      │       │       │
    ┌────▼──────▼───────▼───────▼────┐
    │  AGGREGATE & RANK TOPICS        │
    │  (Keep top 5 trending)          │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │    RAG RETRIEVAL SYSTEM        │
    │ (Pinecone + Gemini Embeddings)│
    │ - Query knowledge base         │
    │ - Get relevant context         │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │   CONTENT GENERATION PHASE    │
    │   (Google Gemini 1.5 Flash)   │
    │ - LinkedIn posts (1 main)     │
    │ - Twitter threads (3-5 tweets)│
    └────┬──────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │    OPTIMAL TIME SCHEDULING    │
    │ LinkedIn: 8 AM, 1 PM, 5 PM    │
    │ Twitter: 9 AM, 2 PM, 7 PM     │
    └────┬──────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │    AUTO-POSTING PHASE         │
    │ - LinkedIn API / Unofficial   │
    │ - Twitter API v2              │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │    LOGGING & MONITORING       │
    │ - Database storage            │
    │ - Error notifications         │
    │ - Engagement tracking         │
    └──────────────────────────────┘
```

---

## Detailed Node-by-Node Workflow Architecture

### **PHASE 1: DATA COLLECTION & TOPIC AGGREGATION**

#### Workflow 1: Daily Trigger & Data Scraping

**Node 1: Schedule Trigger**
- Type: `Cron` node
- Config: Every day at 8 AM UTC
- Output: Timestamp, trigger signal

**Node 2: Parallel Data Collection (Branching)**
Execute in parallel:

**Branch 2A: Twitter Trending Topics**
- Type: `HTTP Request` node
- Method: `GET`
- URL: `https://api.twitter.com/2/trends/by/woeid` (or custom scrape)
- Auth: Bearer Token (Twitter API v2)
- Headers: Authorization header
- Query: Filter for AI/Automation industry trends
- Output: Array of trending tweets/topics

**Branch 2B: Reddit Trending Topics**
- Type: `HTTP Request` OR `Cheerio` (web scraping)
- Target: Subreddits: r/MachineLearning, r/automation, r/Entrepreneur, r/ChatGPT
- Method: Scrape top posts (title + upvotes)
- Filter: Posts with 100+ upvotes in last 24h
- Output: Array of trending Reddit posts

**Branch 2C: Industry News & Blogs**
- Type: `HTTP Request` + `Cheerio` OR RSS Feed reader
- Sources: 
  - TechCrunch (RSS)
  - Medium AI topics (RSS)
  - Product Hunt (RSS/Scrape)
  - Hacker News (Scrape)
- Filter: AI, Automation, AI Agents keywords
- Output: Array of news articles

**Branch 2D: LinkedIn Feed (Optional)**
- Type: `Cheerio` (web scraping) - Official API is restricted
- Alternative: Use `LinkedIn RSS` feeds if available
- Filter: Trending posts in AI/Automation space
- Output: Array of LinkedIn trending content

**Node 3: Merge & Aggregate**
- Type: `Merge` node
- Combine all branches into single array
- Remove duplicates using content hash
- Output: Combined array of ~20-30 trending items

**Node 4: Rank Topics & Select Top 5**
- Type: `Code` node (JavaScript)
```javascript
// Score topics by:
// 1. Source credibility (Twitter=3, Reddit=2, News=4, LinkedIn=3)
// 2. Engagement metrics (upvotes, shares, retweets)
// 3. Relevance to AI/Automation keywords
// Return top 5 scored items

const topics = $input.all().map(item => {
  let score = 0;
  score += item.source === 'news' ? 4 : (item.source === 'twitter' ? 3 : 2);
  score += (item.engagement || 0) / 100;
  return { ...item, score };
});

return topics.sort((a,b) => b.score - a.score).slice(0, 5);
```
- Output: Top 5 trending topics with relevance scores

---

### **PHASE 2: RAG SYSTEM - KNOWLEDGE BASE RETRIEVAL**

#### Workflow 2: Vector Search & Context Retrieval

**Node 5: Initialize Pinecone Connection**
- Type: `HTTP Request` node OR Pinecone Integration (custom)
- Config:
  - Index name: `linkedin-knowledge-base`
  - Dimension: 768 (Gemini embeddings)
  - Metric: Cosine similarity
  - API Key: Stored in environment variable

**Node 6: Generate Query Embeddings**
- Type: `HTTP Request` node (to Gemini Embeddings API)
- For each trending topic from Node 4:
  - Current topic (passed as input)
  - Call: `https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent`
  - Model: `models/embedding-001` (text-embedding-3-small equivalent)
  - Input: Topic title + description
  - Output: 768-dimensional vector

**Node 7: Query Pinecone Knowledge Base**
- Type: `HTTP Request` node (Pinecone API)
- Method: `POST` to `/query` endpoint
- Payload:
  ```json
  {
    "vector": [embedding_from_node_6],
    "topK": 5,
    "includeMetadata": true,
    "namespace": "content"
  }
  ```
- Output: Top 5 most relevant past articles/expertise from your knowledge base

**Node 8: Prepare RAG Context**
- Type: `Code` node (JavaScript)
```javascript
// Combine topic with retrieved knowledge
const topic = $input.first().topicData;
const ragResults = $input.last().ragMatches;

return {
  topic: topic,
  relatedExpertise: ragResults.map(r => r.metadata),
  contextMerge: `Topic: ${topic.title}\n\nRelated Expertise:\n${
    ragResults.map(r => r.metadata.content).join('\n\n')
  }`
};
```
- Output: Combined context ready for AI generation

---

### **PHASE 3: CONTENT GENERATION**

#### Workflow 3: AI-Powered Content Creation

**Node 9: Generate LinkedIn Post**
- Type: `HTTP Request` node (Google Gemini API)
- Model: `gemini-1.5-flash` (cheaper than Pro)
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent`
- Prompt Template:
```
You are a professional LinkedIn content creator specializing in AI and Automation.

TRENDING TOPIC: {topic.title}
TOPIC SUMMARY: {topic.description}

YOUR EXPERTISE:
{ragContext}

Create a professional LinkedIn post (300-400 characters) that:
1. Hooks the reader in the first line
2. Provides actionable insight or unique perspective
3. Includes 3-4 relevant hashtags (#AI #Automation, etc.)
4. Calls to action (question, link, share)
5. Is engaging and thought-provoking

Format: Plain text, optimized for LinkedIn algorithm
```
- Parameters:
  - temperature: 0.7 (balanced creativity)
  - maxOutputTokens: 500
- Output: LinkedIn post text

**Node 10: Generate LinkedIn Carousel (Optional)**
- Type: `HTTP Request` node (Gemini API)
- Prompt: Extend Node 9 to create 5-slide structure:
```
Create 5 LinkedIn carousel slide texts based on the main post.
Each slide: 150-200 characters
Format: JSON array with slides
Include visual direction hints (e.g., "Visual: chart showing X")
```
- Output: Array of 5 carousel slides (JSON)

**Node 11: Generate Twitter Thread**
- Type: `HTTP Request` node (Gemini API)
- Prompt Template:
```
You are a Twitter content expert for AI/Automation topics.

TOPIC: {topic.title}
CONTEXT: {ragContext}

Create a Twitter thread (3-5 tweets) that:
1. First tweet: Hook with bold statement (280 chars max)
2. Tweets 2-4: Educational/insight content (each 280 chars)
3. Final tweet: Call to action + hashtags (280 chars)

Format: JSON array with "tweet1", "tweet2", etc. keys
Keep within 280 character limit per tweet
Use thread numbering (1/ 2/ 3/, etc.)
Include 2-3 relevant hashtags in final tweet only
```
- Output: JSON object with tweet_1, tweet_2, tweet_3, etc.

**Node 12: Validate Generated Content**
- Type: `Code` node (JavaScript)
```javascript
// Validate all generated content
const linkedin = $input.first().linkedinPost;
const twitter = $input.last().twitterThread;

// Checks
const checks = {
  linkedinLength: linkedin.length <= 3000, // LinkedIn limit
  twitterTweets: Object.values(twitter).length >= 3,
  tweetLengths: Object.values(twitter).every(t => t.length <= 280),
  hashtags: linkedin.includes('#'),
  hasContent: linkedin.length > 50 && Object.values(twitter)[0].length > 0
};

if (!Object.values(checks).every(c => c)) {
  throw new Error(`Validation failed: ${JSON.stringify(checks)}`);
}

return {
  validated: true,
  linkedin: linkedin,
  twitter: twitter,
  generatedAt: new Date().toISOString()
};
```
- Output: Validated content object

---

### **PHASE 4: SCHEDULING & POSTING**

#### Workflow 4A: LinkedIn Auto-Posting

**Node 13: Schedule for LinkedIn**
- Type: `Code` node
- Logic: Determine optimal LinkedIn posting time
```javascript
// LinkedIn optimal engagement: 8 AM, 1 PM, 5 PM UTC
const now = new Date();
const postTimes = ['08:00', '13:00', '17:00'];
const nextPostTime = postTimes.find(time => {
  const [h, m] = time.split(':');
  const scheduled = new Date();
  scheduled.setHours(parseInt(h), parseInt(m), 0, 0);
  return scheduled > now;
}) || '08:00'; // Tomorrow at 8 AM if all past

const scheduleTime = new Date();
const [h, m] = nextPostTime.split(':');
scheduleTime.setHours(parseInt(h), parseInt(m), 0, 0);
if (scheduleTime <= now) {
  scheduleTime.setDate(scheduleTime.getDate() + 1);
}

return {
  scheduledTime: scheduleTime.toISOString(),
  content: $input.first().content
};
```
- Output: Scheduled timestamp + content

**Node 14: Post to LinkedIn (API/Integration)**
- Type: `LinkedIn` integration OR `HTTP Request`
- Method: OAuth 2.0 with LinkedIn credentials

**Option A: LinkedIn Official API** (Preferred)
- Endpoint: `https://api.linkedin.com/v2/ugcPosts`
- Requires: LinkedIn Developer App + credentials
- Payload:
```json
{
  "author": "urn:li:person:{USER_ID}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "{generated_post_text}"
      },
      "shareMediaCategory": "ARTICLE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

**Option B: Unofficial Method** (Backup if API limited)
- Browser automation using `Puppeteer` or `Playwright` node
- More reliable for personal profiles

**Node 15: LinkedIn Post Confirmation**
- Type: `Code` node
- Validate response status code (200-201)
- Extract post ID for tracking
- Output: Post metadata (ID, timestamp, URL)

---

#### Workflow 4B: Twitter Auto-Posting

**Node 16: Schedule for Twitter**
- Type: `Code` node
- Logic: Determine optimal Twitter posting times (slightly different)
```javascript
// Twitter optimal engagement: 9 AM, 2 PM, 7 PM UTC
const postTimes = ['09:00', '14:00', '19:00'];
// Similar logic to Node 13
```
- Output: Scheduled timestamps for each tweet

**Node 17: Post Thread to Twitter**
- Type: `Twitter API v2` node OR `HTTP Request`
- Auth: Bearer Token (Twitter API v2)
- Endpoints:
  - First tweet: `POST /2/tweets`
  - Reply tweets: `POST /2/tweets` (with reply_settings)
  
**Implementation**:
```javascript
// Post tweet 1
const tweet1Response = await POST_REQUEST(
  'https://api.twitter.com/2/tweets',
  { text: tweets.tweet_1 },
  { headers: { Authorization: `Bearer ${API_KEY}` } }
);

// Post tweet 2 as reply to tweet 1
const tweet2Response = await POST_REQUEST(
  'https://api.twitter.com/2/tweets',
  {
    text: tweets.tweet_2,
    reply: { in_reply_to_tweet_id: tweet1Response.data.id }
  },
  { headers: { Authorization: `Bearer ${API_KEY}` } }
);

// Continue for tweets 3-5...
```
- Output: Array of tweet IDs and URLs

**Node 18: Twitter Post Confirmation**
- Type: `Code` node
- Validate all tweets posted successfully
- Collect all tweet URLs for database logging
- Output: Confirmed tweet thread metadata

---

### **PHASE 5: LOGGING & MONITORING**

#### Workflow 5: Database Storage & Error Handling

**Node 19: Store Posting History**
- Type: `Database` node (PostgreSQL, MySQL, or Supabase)
- Table: `content_posts`
- Schema:
```sql
CREATE TABLE content_posts (
  id UUID PRIMARY KEY,
  created_at TIMESTAMP,
  trending_topic VARCHAR(500),
  linkedin_post_id VARCHAR(100),
  linkedin_url VARCHAR(500),
  twitter_thread_ids JSON,
  twitter_urls JSON,
  content_text TEXT,
  engagement_score FLOAT DEFAULT 0,
  status VARCHAR(50) DEFAULT 'posted'
);
```
- Insert: All metadata from Nodes 15 & 18
- Output: Stored record ID

**Node 20: Error Handling & Notifications**
- Type: `Error Handler` node
- Triggers on any failure in workflow
- Actions:
  - Send email notification with error details
  - Type: `Send Email` node
  - Recipients: Your email
  - Subject: `[ALERT] Content Generation Failed`
  - Body: Includes error message, stack trace, recommended action
  
- Type: `Slack` node (optional)
  - Send error to Slack #automation channel
  - Include timestamp, error details, which step failed

**Node 21: Success Notification**
- Type: `Slack` OR `Email` node
- Trigger: On successful posting
- Message template:
```
✅ Daily Content Posted Successfully!
📅 Date: {date}
📌 Trending Topic: {topic}
📱 LinkedIn: [View Post] ({linkedin_url})
🐦 Twitter: [View Thread] ({twitter_url})
📊 Engagement Target: {engagement_target}
```

**Node 22: Weekly Analytics & Engagement Tracking**
- Type: `Cron` trigger (Weekly, Sundays at 10 AM)
- Tasks:
  1. Query LinkedIn Insights API for post metrics
  2. Query Twitter Insights API for engagement
  3. Calculate aggregated metrics (likes, shares, replies)
  4. Store in analytics table
  5. Generate weekly summary report

---

## COMPLETE WORKFLOW STRUCTURE (Simplified View)

```
1. MAIN WORKFLOW: "Daily Content Creation"
   ├── Schedule Trigger (Daily 8 AM)
   ├── Parallel Data Collection
   │   ├── Twitter Trends Scraper
   │   ├── Reddit Scraper
   │   ├── News API Scraper
   │   └── LinkedIn Feed Scraper
   ├── Aggregate & Rank Topics
   ├── Vector Embedding & RAG Query
   ├── Validate RAG Results
   ├── Generate LinkedIn Content
   ├── Generate Twitter Content
   ├── Validate Generated Content
   ├── Split into Two Parallel Posting Workflows
   │   ├── POSTING WORKFLOW A: LinkedIn
   │   │   ├── Schedule for Optimal Time
   │   │   ├── Post via API
   │   │   └── Confirm + Log
   │   └── POSTING WORKFLOW B: Twitter
   │       ├── Schedule for Optimal Time
   │       ├── Post Thread via API
   │       └── Confirm + Log
   ├── Store Posting History
   ├── Send Success Notification
   └── Error Handling (on any failure)

2. ANALYTICS WORKFLOW: "Weekly Analytics"
   ├── Schedule Trigger (Weekly)
   ├── Fetch LinkedIn Insights
   ├── Fetch Twitter Insights
   ├── Calculate Metrics
   ├── Store Analytics
   └── Generate Report Email
```

---

## IMPLEMENTATION SEQUENCE (Step-by-Step)

### **Week 1: Foundation & Setup**

**Day 1-2: API Credentials & Accounts**
- [ ] Create Twitter API v2 developer account
- [ ] Create Google Cloud project, enable Gemini API
- [ ] Set up Pinecone account (free tier)
- [ ] Prepare LinkedIn credentials (API or automation)
- [ ] Create database (PostgreSQL, MySQL, or Supabase)

**Day 3-4: Build Phase 1 (Data Collection)**
- [ ] Create Cron trigger node
- [ ] Build Twitter scraper node
- [ ] Build Reddit scraper node
- [ ] Build News/RSS scraper node
- [ ] Create aggregation & ranking node

**Day 5: Test Phase 1**
- [ ] Test each data source independently
- [ ] Verify data quality
- [ ] Test ranking algorithm
- [ ] Confirm output format

### **Week 2: RAG & Content Generation**

**Day 6-7: Prepare Knowledge Base**
- [ ] Collect your past articles/expertise in JSON format
- [ ] Generate embeddings for each article
- [ ] Upload embeddings to Pinecone
- [ ] Test retrieval with sample queries

**Day 8-10: Build Phase 2 & 3**
- [ ] Create Gemini embedding node
- [ ] Create Pinecone query node
- [ ] Build LinkedIn content generation node
- [ ] Build Twitter content generation node
- [ ] Create validation node

**Day 11: Test Phase 2 & 3**
- [ ] Test RAG retrieval accuracy
- [ ] Test content generation quality
- [ ] Iterate on prompts for better output
- [ ] Verify content meets guidelines

### **Week 3: Posting & Monitoring**

**Day 12-13: Build Phase 4 (Posting)**
- [ ] Implement LinkedIn posting (API or automation)
- [ ] Implement Twitter thread posting
- [ ] Build scheduling logic
- [ ] Create confirmation nodes

**Day 14: Build Phase 5 (Logging)**
- [ ] Create database schema & connection
- [ ] Build data storage node
- [ ] Implement error handling
- [ ] Set up notifications (Slack/Email)

**Day 15: Full Integration Test**
- [ ] Run complete workflow end-to-end
- [ ] Verify all nodes work together
- [ ] Check data flows correctly
- [ ] Test error scenarios
- [ ] Confirm posting to both platforms

### **Week 4: Optimization & Launch**

**Day 16-17: Refinement**
- [ ] Optimize node configurations
- [ ] Improve content quality with prompt tuning
- [ ] Add caching for API calls to reduce cost
- [ ] Test scheduling under different conditions

**Day 18: Monitoring Setup**
- [ ] Deploy analytics workflow
- [ ] Set up alerts for failures
- [ ] Create dashboard for engagement tracking
- [ ] Document entire workflow

**Day 19-20: Launch & Monitor**
- [ ] Let workflow run for 2-3 days in production
- [ ] Monitor for any issues
- [ ] Collect initial engagement metrics
- [ ] Make final adjustments based on real data

---

## COST BREAKDOWN (Monthly Estimate)

| Service | Usage | Cost |
|---------|-------|------|
| **Google Gemini API** | ~90 LLM calls @ 500 tokens avg (~45k tokens/month) | ~$0.70 |
| **Gemini Embeddings** | ~90 queries @ 100 tokens (~9k tokens/month) | ~$0.15 |
| **Twitter API v2** | Included in free tier | Free |
| **LinkedIn API** | Included in free tier | Free |
| **Pinecone** | Free tier (1 index, 100k vectors) | Free* |
| **Database** | Supabase free tier OR self-hosted | Free* |
| **n8n Cloud** | Self-hosted option | Free* |
| **Reddit API** | Free tier | Free |
| **News APIs** | NewsAPI free tier (~100 requests/day) | Free |
| **Email/Slack Notifications** | Included in tools | Free |
| **Total** | | **$0.85-1.50/month** |

\*Can upgrade if needed. Pinecone free tier = 100k vectors enough for ~5 years of knowledge base at personal use.

---

## OPTIMIZATION TIPS FOR COST REDUCTION

1. **Batch API Calls**: Group multiple trending topics into single API call
2. **Cache Embeddings**: Don't re-embed topics if already cached
3. **Reuse RAG Results**: In unlikely event of topic repetition
4. **Use 1.5 Flash**: Cheaper than Gemini Pro, 80% similar quality
5. **Self-host n8n**: Move from cloud to Docker on your own server
6. **Limit Posting Frequency**: Start with 1 post/day, not 3

---

## SECURITY & BEST PRACTICES

1. **Credentials Management**
   - Store all API keys in n8n environment variables
   - Never hardcode secrets in workflows
   - Use OAuth 2.0 where available

2. **Rate Limiting**
   - Add delays between API calls (1-2 second buffer)
   - Implement exponential backoff for failures
   - Monitor API usage to stay within free tiers

3. **Content Quality**
   - Always review generated content before first post
   - Add manual approval node if desired
   - Set confidence threshold for AI-generated content

4. **Error Recovery**
   - Implement retry logic with exponential backoff
   - Store failed posts in database for manual retry
   - Alert immediately on critical failures

5. **Data Privacy**
   - Keep knowledge base items private
   - Don't log sensitive information
   - Review stored engagement data periodically

---

## NEXT STEPS

1. **Which platform would you like to start with?** (LinkedIn or Twitter)
2. **Do you have Gemini API key ready?** (Free Google Cloud credits available)
3. **Should we add manual approval before posting?** (Recommended for v1)
4. **Do you have a knowledge base of past articles?** (Needed for RAG)
5. **Preferred n8n installation?** (Cloud vs. Self-hosted)

Once you provide context, I'll build the exact workflow configuration in n8n.
