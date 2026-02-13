# LinkedIn Content Automation Workflow - Complete Implementation Guide

**Status**: Ready for Implementation
**Target**: Automated daily LinkedIn posts from trending topics + RAG + Gemini AI

---

## Table of Contents
1. [Prerequisites & Setup](#prerequisites--setup)
2. [Workflow Architecture](#workflow-architecture)
3. [Node Configuration Details](#node-configuration-details)
4. [Complete Workflow JSON](#complete-workflow-json)
5. [Testing & Deployment](#testing--deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Setup

### ✅ Required Accounts & Credentials

**1. Google Gemini API**
- [ ] Go to [Google Cloud Console](https://console.cloud.google.com)
- [ ] Create new project: "LinkedIn Content Creator"
- [ ] Enable APIs:
  - Generative AI API
  - Text Embeddings API
- [ ] Create API Key (not OAuth)
- [ ] **Save**: `GEMINI_API_KEY` in n8n credentials

**2. Twitter API v2** (for trending data)
- [ ] Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- [ ] Create App in Free tier
- [ ] Generate Bearer Token (not OAuth for this task)
- [ ] **Save**: `TWITTER_BEARER_TOKEN` in n8n

**3. LinkedIn Credentials**
- [ ] **Option A**: Using LinkedIn Official API
  - Apply for LinkedIn Developers Program access
  - Creates OAuth credentials
  - **Save**: LinkedIn OAuth credentials
  
- [ ] **Option B**: Browser Automation (Recommended for personal profiles)
  - Just need LinkedIn username & password (stored securely in n8n)
  - Use Puppeteer node in n8n

**4. Pinecone Vector Database**
- [ ] Go to [Pinecone](https://pinecone.io/)
- [ ] Sign up (free tier)
- [ ] Create index: `linkedin-knowledge-base`
  - Dimension: 768
  - Metric: cosine
- [ ] **Save**: `PINECONE_API_KEY` and `PINECONE_HOST` in n8n

**5. News API (for trending articles)**
- [ ] Go to [NewsAPI.org](https://newsapi.org)
- [ ] Get free API key
- [ ] **Save**: `NEWSAPI_KEY` in n8n

**6. Database** (Optional but recommended)
- [ ] Supabase (PostgreSQL, free tier)
  - Sign up at [Supabase](https://supabase.com)
  - Create `content_posts` table (schema below)
- [ ] **Save**: Database connection string in n8n

**7. n8n Instance**
- [ ] Option A: n8n Cloud (free tier, 100 tasks/month)
- [ ] Option B: Self-hosted Docker on your machine (unlimited)
- [ ] Recommended: Self-hosted for this project

---

## Workflow Architecture

### High-Level Flow

```
┌─────────────────────────────────────┐
│  1. CRON TRIGGER (Daily 8 AM UTC)  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 2. PARALLEL DATA COLLECTION         │
│    ├─ Twitter Trends                │
│    ├─ Reddit Top Posts              │
│    ├─ News API Articles             │
│    └─ LinkedIn RSS (optional)       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 3. AGGREGATE & RANK TOPICS          │
│    (Keep top 1-3 trending)          │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 4. GENERATE EMBEDDINGS              │
│    (Query vector for RAG)           │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 5. PINECONE VECTOR SEARCH           │
│    (Retrieve your expertise)        │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 6. GENERATE LINKEDIN POST           │
│    (Gemini 1.5 Flash)               │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 7. VALIDATE CONTENT                 │
│    (Check quality, length, etc)     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 8. SCHEDULE OPTIMAL TIME            │
│    (LinkedIn peak: 8 AM, 1 PM, 5 PM)│
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 9. POST TO LINKEDIN                 │
│    (Official API or Automation)     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 10. LOG TO DATABASE                 │
│     (Store metadata & engagement)   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 11. SEND NOTIFICATION               │
│     (Slack or Email)                │
└─────────────────────────────────────┘
```

---

## Node Configuration Details

### **Phase 1: Trigger & Data Collection**

#### Node 1: Schedule Trigger
```
Type: Cron
Configuration:
  - Mode: Every day
  - Time: 08:00 (UTC)
  - Timezone: UTC
  
Output:
  {
    "timestamp": "2026-02-13T08:00:00Z",
    "executionDate": "2026-02-13"
  }
```

#### Node 2A: Twitter Trends (HTTP Request)
```
Type: HTTP Request
Method: GET
URL: https://api.twitter.com/2/tweets/search/recent?query=AI%20OR%20automation%20-is:retweet&max_results=100&tweet.fields=public_metrics&sort_order=recency

Headers:
  Authorization: Bearer {{ $env.TWITTER_BEARER_TOKEN }}

Query Parameters:
  query: (AI OR automation OR "machine learning") lang:en
  max_results: 100
  tweet.fields: created_at,public_metrics,author_id
  sort_order: recency

Options:
  - Timeout: 30s
  - Retry on: Network error
  - Return All: true

Output Processing:
  - Extracts tweets with engagement > 50 retweets
  - Returns: [{ text, engagement, url, created_at }, ...]
```

#### Node 2B: Reddit Trends (HTTP Request with Cheerio)
```
Type: HTTP Request + Code Node
Method: GET
URLs (in sequence or parallel):
  1. https://www.reddit.com/r/MachineLearning/top/?t=day.json
  2. https://www.reddit.com/r/ChatGPT/top/?t=day.json
  3. https://www.reddit.com/r/automation/top/?t=day.json
  4. https://www.reddit.com/r/Entrepreneur/hot.json

Headers:
  User-Agent: Mozilla/5.0 (LinkedIn Content Creator)

Output Processing Code:
  ```javascript
  const redditTopics = [];
  
  $input.all().forEach(response => {
    const data = JSON.parse(response.body);
    const children = data.data.children.slice(0, 10);
    
    children.forEach(post => {
      if (post.data.score > 50) {
        redditTopics.push({
          title: post.data.title,
          score: post.data.score,
          url: `https://reddit.com${post.data.permalink}`,
          source: 'reddit',
          engagement: post.data.upvote_ratio
        });
      }
    });
  });
  
  return redditTopics;
  ```
```

#### Node 2C: News API Articles (HTTP Request)
```
Type: HTTP Request
Method: GET
URL: https://newsapi.org/v2/everything

Query Parameters:
  q: AI AND (automation OR agent OR "machine learning")
  sortBy: publishedAt
  language: en
  pageSize: 20
  apiKey: {{ $env.NEWSAPI_KEY }}

Output Processing:
  - Extract articles published in last 24h
  - Returns: [{ title, description, url, source, publishedAt }, ...]
```

#### Node 2D: LinkedIn RSS (Skip for now - requires special setup)
```
Type: Skip or HTTP Request to RSS redirect
Alternative: Manually curate top 5 LinkedIn posts weekly
```

#### Node 3: Merge Results
```
Type: Merge Node
Mode: Combine
Configuration:
  - Combine all 3 data sources (Twitter, Reddit, News)
  - Remove duplicates by title similarity

Output:
  Array of 30-50 trending items with source info
```

#### Node 4: Rank & Select Top Topics
```
Type: Code Node
Language: JavaScript

Code:
  ```javascript
  const allItems = $input.all();
  
  // Scoring algorithm
  const scored = allItems.map(item => {
    let score = 0;
    
    // Source credibility
    const sourceScore = {
      'news': 4,
      'twitter': 3,
      'reddit': 2
    };
    score += sourceScore[item.source] || 2;
    
    // Engagement metrics
    score += (item.engagement || item.score || 0) / 100;
    
    // Relevance boosters
    if (item.title?.includes('AI') || item.title?.includes('automation')) score += 2;
    if (item.title?.includes('agent') || item.title?.includes('LLM')) score += 1.5;
    
    return { ...item, score };
  });
  
  // Sort and take top 3
  const topTopics = scored
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(t => ({
      title: t.title,
      description: t.description || t.text,
      source: t.source,
      url: t.url,
      score: Math.round(t.score * 100) / 100
    }));
  
  return topTopics;
  ```

Output:
  ```json
  [
    {
      "title": "AI Agents Transform Enterprise...",
      "description": "New research shows...",
      "source": "news",
      "score": 8.5
    },
    { ... },
    { ... }
  ]
  ```
```

---

### **Phase 2: RAG System**

#### Node 5: Generate Query Embedding
```
Type: HTTP Request
Method: POST
URL: https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent

Headers:
  Content-Type: application/json
  X-Goog-Api-Key: {{ $env.GEMINI_API_KEY }}

Body:
  ```json
  {
    "model": "models/embedding-001",
    "content": {
      "parts": [
        {
          "text": "{{ $node['Node4'].json.first().title }} {{ $node['Node4'].json.first().description }}"
        }
      ]
    }
  }
  ```

Output:
  ```json
  {
    "embedding": {
      "values": [0.023, -0.045, 0.089, ...] // 768 dimensions
    }
  }
  ```
```

#### Node 6: Query Pinecone Knowledge Base
```
Type: HTTP Request
Method: POST
URL: {{ $env.PINECONE_HOST }}/query

Headers:
  Api-Key: {{ $env.PINECONE_API_KEY }}
  Content-Type: application/json

Body:
  ```json
  {
    "vector": {{ $node['Node5'].json.embedding.values }},
    "topK": 5,
    "includeMetadata": true,
    "namespace": "content"
  }
  ```

Expected Output:
  ```json
  {
    "matches": [
      {
        "id": "article-123",
        "score": 0.95,
        "metadata": {
          "title": "Your Past Article...",
          "content": "Full article text..."
        }
      },
      { ... more matches ... }
    ]
  }
  ```

Note: First time setup - you need to upload your knowledge base:
- Collect past 10-20 articles/insights you've written
- Generate embeddings for each
- Upload to Pinecone with metadata
```

#### Node 7: Prepare RAG Context
```
Type: Code Node
Language: JavaScript

Code:
  ```javascript
  const topic = $node['Node4'].json[0]; // Top trending topic
  const ragMatches = $node['Node6'].json.matches || [];
  
  // Build context string
  const expertise = ragMatches
    .map((m, i) => `${i+1}. "${m.metadata.title}"\n${m.metadata.content.substring(0, 300)}...`)
    .join('\n\n');
  
  return {
    topic: topic,
    expertise: expertise,
    ragRelevance: ragMatches[0]?.score || 0,
    numberOfMatches: ragMatches.length
  };
  ```

Output:
  ```json
  {
    "topic": { "title": "...", "description": "..." },
    "expertise": "1. Article Title\nContent preview...\n\n2. ...",
    "ragRelevance": 0.94,
    "numberOfMatches": 5
  }
  ```
```

---

### **Phase 3: Content Generation**

#### Node 8: Generate LinkedIn Post
```
Type: HTTP Request
Method: POST
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent

Headers:
  Content-Type: application/json
  X-Goog-Api-Key: {{ $env.GEMINI_API_KEY }}

Body:
  ```json
  {
    "contents": [
      {
        "parts": [
          {
            "text": "You are a LinkedIn content expert specializing in AI, automation, and business innovation. Your tone is professional yet engaging, with clear insights and actionable takeaways.\n\nTRENDING TOPIC:\nTitle: {{ $node['Node7'].json.topic.title }}\nDescription: {{ $node['Node7'].json.topic.description }}\n\nYOUR RELEVANT EXPERTISE:\n{{ $node['Node7'].json.expertise }}\n\nCreate a compelling LinkedIn post (280-400 characters) that:\n\n1. Opens with a hook or bold statement that stops the scroll\n2. Shares a unique insight or perspective based on the trending topic + your expertise\n3. Includes 2-3 actionable takeaways or thought-provoking questions\n4. Ends with a clear CTA (ask question, invite discussion, link to resource)\n5. Uses 3-4 relevant hashtags (#AI #Automation #Innovation, etc.)\n6. Maintains professional tone while being conversational\n7. Is optimized for LinkedIn algorithm (specific keywords, values clarity)\n\nIMPORTANT: Keep it under 3000 characters. Format as plain text (no markdown). Include hashtags at the end.\n\nGenerate ONLY the post text. No explanation, no title, no additional commentary."
          }
        ]
      }
    ],
    "generationConfig": {
      "temperature": 0.7,
      "topK": 40,
      "topP": 0.95,
      "maxOutputTokens": 500
    }
  }
  ```

Expected Output:
  LinkedIn post text ready to post

Parsing Code (add Code node after):
  ```javascript
  const response = $input.first().json;
  const postText = response.candidates[0].content.parts[0].text;
  
  return {
    postContent: postText,
    length: postText.length,
    generatedAt: new Date().toISOString(),
    model: 'gemini-1.5-flash'
  };
  ```
```

#### Node 9: Validate Content Quality
```
Type: Code Node
Language: JavaScript

Code:
  ```javascript
  const post = $input.first().json.postContent;
  
  // Validation checks
  const validation = {
    hasContent: post && post.length > 50,
    withinLinkedInLimit: post.length <= 3000,
    hasHashtags: post.includes('#'),
    hasEngagement: post.match(/\?|\.\.\./) !== null, // Question or ellipsis
    minLength: post.length >= 100,
    hasValue: post.includes('insight') || post.includes('tips') || post.includes('why') || post.includes('how')
  };
  
  const isValid = Object.values(validation).every(v => v === true);
  
  if (!isValid) {
    throw new Error(`Content validation failed: ${JSON.stringify(validation)}`);
  }
  
  return {
    validated: true,
    content: post.trim(),
    checks: validation,
    readyToPost: true
  };
  ```
```

---

### **Phase 4: Scheduling & Posting**

#### Node 10: Schedule for Optimal Time
```
Type: Code Node
Language: JavaScript

Code:
  ```javascript
  // LinkedIn optimal engagement times: 8 AM, 1 PM, 5 PM UTC
  // For version 1.0: Just post at 8 AM same day (no scheduling)
  // v2.0: Implement scheduling for multiple times
  
  const now = new Date();
  const postTime = new Date();
  
  // Next optimal slot
  const optimalHours = [8, 13, 17]; // 8 AM, 1 PM, 5 PM UTC
  const nextHour = optimalHours.find(h => {
    const test = new Date();
    test.setUTCHours(h, 0, 0, 0);
    return test > now;
  });
  
  if (nextHour) {
    postTime.setUTCHours(nextHour, 0, 0, 0);
  } else {
    // If all past, schedule for 8 AM tomorrow
    postTime.setUTCHours(8, 0, 0, 0);
    postTime.setUTCDate(postTime.getUTCDate() + 1);
  }
  
  return {
    scheduledTime: postTime.toISOString(),
    hoursUntilPost: ((postTime - now) / 1000 / 3600).toFixed(1),
    content: $input.first().json.content
  };
  ```
```

#### Node 11A: Post to LinkedIn (Method 1 - Official API)
```
Type: HTTP Request
Method: POST
URL: https://api.linkedin.com/v2/ugcPosts

Headers:
  Authorization: Bearer {{ $node['credentials'].linkedin.accessToken }}
  Content-Type: application/json
  X-Restli-Protocol-Version: 2.0.0

Body:
  ```json
  {
    "author": "urn:li:person:{{ $node['credentials'].linkedin.userId }}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
      "com.linkedin.ugc.ShareContent": {
        "shareCommentary": {
          "text": "{{ $node['Node10'].json.content }}"
        },
        "shareMediaCategory": "NONE"
      }
    },
    "visibility": {
      "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
  }
  ```

Note: Requires LinkedIn Developer App credentials
Response: { "id": "urn:li:activity:1234567890" }
```

#### Node 11B: Post to LinkedIn (Method 2 - Puppeteer Automation)
```
Type: Execute Node / Puppeteer
Advantage: Works with personal profiles, no API application needed

Code:
  ```javascript
  const puppeteer = require('puppeteer');
  
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Login to LinkedIn
  await page.goto('https://www.linkedin.com/login');
  await page.type('input[name="session_key"]', process.env.LINKEDIN_EMAIL);
  await page.type('input[name="session_password"]', process.env.LINKEDIN_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  // Create post
  await page.goto('https://www.linkedin.com/feed/');
  await page.click('.share-box'); // Click share box
  await page.type('.ql-editor', $input.first().json.content);
  await page.click('button[aria-label="Post"]');
  
  await page.waitForNavigation();
  const postUrl = page.url();
  
  await browser.close();
  
  return {
    success: true,
    postUrl: postUrl,
    timestamp: new Date().toISOString()
  };
  ```

Recommendation: Use this for v1.0 (simpler, no API approvals needed)
```

#### Node 12: Confirm Post Success
```
Type: Code Node
Language: JavaScript

Code:
  ```javascript
  const response = $input.first().json;
  
  if (!response.success && !response.id && !response.postUrl) {
    throw new Error('LinkedIn posting failed: ' + JSON.stringify(response));
  }
  
  return {
    posted: true,
    postId: response.id || response.postUrl,
    timestamp: new Date().toISOString(),
    content: $node['Node10'].json.content,
    topic: $node['Node7'].json.topic.title
  };
  ```
```

---

### **Phase 5: Logging & Notifications**

#### Node 13: Store in Database (Supabase/PostgreSQL)
```
Type: PostgreSQL / Supabase Node
Table: public.content_posts

Schema (create before using):
  ```sql
  CREATE TABLE content_posts (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    posted_at TIMESTAMP,
    topic VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    linkedin_post_id VARCHAR(200),
    linkedin_url VARCHAR(500),
    post_length INT,
    engagement_score FLOAT DEFAULT 0,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'posted',
    rag_relevance FLOAT,
    model VARCHAR(50) DEFAULT 'gemini-1.5-flash'
  );
  
  CREATE INDEX idx_posted_at ON content_posts(posted_at);
  CREATE INDEX idx_status ON content_posts(status);
  ```

Insert Query:
  ```sql
  INSERT INTO content_posts 
  (topic, content, posted_at, linkedin_post_id, post_length, rag_relevance, status)
  VALUES 
  ($1, $2, $3, $4, $5, $6, 'posted')
  RETURNING id, created_at;
  ```

Parameters:
  $1 = $node['Node7'].json.topic.title
  $2 = $node['Node10'].json.content
  $3 = NOW()
  $4 = $node['Node12'].json.postId
  $5 = $node['Node10'].json.content.length
  $6 = $node['Node7'].json.ragRelevance
```

#### Node 14: Success Notification (Slack)
```
Type: Slack Node
Channel: #content-automation (or direct message)

Message Template:
  ```
  ✅ LinkedIn Post Published Successfully!
  
  📌 Topic: {{ $node['Node7'].json.topic.title }}
  📝 Post Length: {{ $node['Node10'].json.content.length }} characters
  🔗 Knowledge Base Relevance: {{ $node['Node7'].json.ragRelevance }}
  📅 Posted: {{ $node['Node12'].json.timestamp }}
  
  Content Preview:
  > {{ $node['Node10'].json.content.substring(0, 200) }}...
  
  Check engagement in > 2 hours
  ```
```

#### Node 15: Error Handling (Catch-All)
```
Type: Error Handler Node (attach to all previous nodes)

On Error:
1. Send Email Alert
   Type: Send Email Node
   To: your-email@gmail.com
   Subject: ⚠️ LinkedIn Content Creation Failed
   Body: Include error message, which node failed, time, steps to fix

2. Send Slack Alert
   #errors or #alerts channel
   Message: Error details + timestamp + recommended action

3. Update Database
   INSERT error log: { status: 'failed', error_message, failed_node }
```

---

## Complete Workflow JSON

Save this as `linkedin-content-automation.json` and import into n8n:

```json
{
  "name": "LinkedIn Daily Content Creator",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "type": "hours",
              "value": 24
            }
          ]
        },
        "timezone": "UTC",
        "triggerAtStartup": false
      },
      "id": "1",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [250, 100]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/v2/tweets/search/recent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "twitterOAuth2Api",
        "options": {
          "headers": {
            "parameters": [
              {
                "name": "Authorization",
                "value": "Bearer {{ $env.TWITTER_BEARER_TOKEN }}"
              }
            ]
          }
        },
        "qs": {
          "query": "(AI OR automation OR \"machine learning\") lang:en -is:retweet",
          "max_results": "100",
          "tweet.fields": "created_at,public_metrics,author_id",
          "sort_order": "recency"
        },
        "sendQuery": true
      },
      "id": "2",
      "name": "Get Twitter Trends",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [100, 200]
    },
    {
      "parameters": {
        "url": "https://newsapi.org/v2/everything",
        "qs": {
          "q": "AI AND (automation OR agent OR \"machine learning\")",
          "sortBy": "publishedAt",
          "language": "en",
          "pageSize": "20",
          "apiKey": "={{ $env.NEWSAPI_KEY }}"
        },
        "sendQuery": true
      },
      "id": "3",
      "name": "Get News Articles",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [100, 300]
    },
    {
      "parameters": {
        "mode": "combine"
      },
      "id": "4",
      "name": "Merge Data Sources",
      "type": "n8n-nodes-base.merge",
      "typeVersion": 2,
      "position": [250, 250]
    },
    {
      "parameters": {
        "jsCode": "const allItems = $input.all();\nconst scored = allItems.map(item => {\n  let score = 0;\n  const sourceScore = { 'news': 4, 'twitter': 3, 'reddit': 2 };\n  score += (sourceScore[item.source] || 2);\n  score += (item.engagement || item.score || 0) / 100;\n  if (item.title?.includes('AI')) score += 2;\n  return { ...item, score };\n});\nreturn scored.sort((a,b) => b.score - a.score).slice(0, 3);"
      },
      "id": "5",
      "name": "Rank Topics",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [400, 200]
    },
    {
      "parameters": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent",
        "method": "POST",
        "bodyType": "json",
        "body": "{\n  \"model\": \"models/embedding-001\",\n  \"content\": {\n    \"parts\": [{\n      \"text\": \"{{ $node['Rank Topics'].json[0].title }} {{ $node['Rank Topics'].json[0].description }}\"\n    }]\n  }\n}",
        "options": {
          "headers": {\n            \"parameters\": [\n              {\n                \"name\": \"X-Goog-Api-Key\",\n                \"value\": \"={{ $env.GEMINI_API_KEY }}\"\n              }\n            ]\n          }\n        }
      },
      "id": "6",
      "name": "Generate Embedding",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [550, 200]
    },
    {
      "parameters": {
        "url": "={{ $env.PINECONE_HOST }}/query",
        "method": "POST",
        "bodyType": "json",
        "body": "{\n  \"vector\": {{ $node['Generate Embedding'].json.embedding.values }},\n  \"topK\": 5,\n  \"includeMetadata\": true,\n  \"namespace\": \"content\"\n}",
        "options": {
          "headers": {\n            \"parameters\": [\n              {\n                \"name\": \"Api-Key\",\n                \"value\": \"={{ $env.PINECONE_API_KEY }}\"\n              }\n            ]\n          }\n        }
      },
      "id": "7",
      "name": "Query Pinecone RAG",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [700, 200]
    },
    {
      "parameters": {
        "jsCode": "const topic = $node['Rank Topics'].json[0];\nconst ragMatches = $node['Query Pinecone RAG'].json.matches || [];\nconst expertise = ragMatches\n  .map((m, i) => `${i+1}. \"${m.metadata.title}\"\\n${m.metadata.content.substring(0, 300)}...`)\n  .join('\\n\\n');\nreturn {\n  topic: topic,\n  expertise: expertise,\n  ragRelevance: ragMatches[0]?.score || 0\n};"
      },
      "id": "8",
      "name": "Prepare RAG Context",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [850, 200]
    },
    {
      "parameters": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "method": "POST",
        "bodyType": "json",
        "body": "{\n  \"contents\": [{\n    \"parts\": [{\n      \"text\": \"You are a LinkedIn content expert specializing in AI and automation. Create a compelling LinkedIn post (280-400 chars) based on:\\n\\nTOPIC: {{ $node['Prepare RAG Context'].json.topic.title }}\\n\\nEXPERTISE:\\n{{ $node['Prepare RAG Context'].json.expertise }}\\n\\nInclude hook, insight, 2-3 takeaways, CTA, and 3-4 hashtags. Keep under 3000 characters.\"\n    }]\n  }],\n  \"generationConfig\": {\n    \"temperature\": 0.7,\n    \"maxOutputTokens\": 500\n  }\n}",
        "options": {\n          \"headers\": {\n            \"parameters\": [\n              {\n                \"name\": \"X-Goog-Api-Key\",\n                \"value\": \"={{ $env.GEMINI_API_KEY }}\"\n              }\n            ]\n          }\n        }\n      },\n      \"id\": \"9\",\n      \"name\": \"Generate LinkedIn Post\",\n      \"type\": \"n8n-nodes-base.httpRequest\",\n      \"typeVersion\": 3,\n      \"position\": [400, 400]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"const response = $input.first().json;\\nconst postText = response.candidates[0].content.parts[0].text;\\nreturn {\\n  postContent: postText,\\n  length: postText.length,\\n  generatedAt: new Date().toISOString()\\n};\"\n      },\n      \"id\": \"10\",\n      \"name\": \"Parse Generated Content\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [550, 400]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"const post = $input.first().json.postContent;\\nconst validation = {\\n  hasContent: post && post.length > 50,\\n  withinLimit: post.length <= 3000,\\n  hasHashtags: post.includes('#'),\\n  hasEngagement: post.match(/\\\\?|\\\\.\\\\.\\\\./),\\n  minLength: post.length >= 100\\n};\\nif (!Object.values(validation).every(v => v)) {\\n  throw new Error(`Validation failed: ${JSON.stringify(validation)}`);\\n}\\nreturn { validated: true, content: post.trim() };\"\n      },\n      \"id\": \"11\",\n      \"name\": \"Validate Content\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [700, 400]\n    },\n    {\n      \"parameters\": {\n        \"jsCode\": \"const now = new Date();\\nconst postTime = new Date();\\nconst optimalHours = [8, 13, 17];\\nconst nextHour = optimalHours.find(h => {\\n  const test = new Date();\\n  test.setUTCHours(h, 0, 0, 0);\\n  return test > now;\\n});\\nif (nextHour) {\\n  postTime.setUTCHours(nextHour, 0, 0, 0);\\n} else {\\n  postTime.setUTCHours(8, 0, 0, 0);\\n  postTime.setUTCDate(postTime.getUTCDate() + 1);\\n}\\nreturn {\\n  scheduledTime: postTime.toISOString(),\\n  content: $input.first().json.content\\n};\"\n      },\n      \"id\": \"12\",\n      \"name\": \"Schedule Posting Time\",\n      \"type\": \"n8n-nodes-base.code\",\n      \"typeVersion\": 2,\n      \"position\": [850, 400]\n    },\n    {\n      \"parameters\": {\n        \"authentication\": \"oAuth2\",\n        \"nodeCredentialType\": \"supabaseApi\",\n        \"mode\": \"insert\",\n        \"table\": \"content_posts\",\n        \"columns\": \"topic,content,posted_at,post_length,rag_relevance,status\",\n        \"fieldsUi\": {\n          \"fieldValues\": [\n            { \"fieldName\": \"topic\", \"fieldValue\": \"={{ $node['Prepare RAG Context'].json.topic.title }}\" },\n            { \"fieldName\": \"content\", \"fieldValue\": \"={{ $node['Validate Content'].json.content }}\" },\n            { \"fieldName\": \"posted_at\", \"fieldValue\": \"={{ $node['Schedule Posting Time'].json.scheduledTime }}\" },\n            { \"fieldName\": \"post_length\", \"fieldValue\": \"={{ $node['Validate Content'].json.content.length }}\" },\n            { \"fieldName\": \"rag_relevance\", \"fieldValue\": \"={{ $node['Prepare RAG Context'].json.ragRelevance }}\" },\n            { \"fieldName\": \"status\", \"fieldValue\": \"posted\" }\n          ]\n        }\n      },\n      \"id\": \"13\",\n      \"name\": \"Store in Database\",\n      \"type\": \"n8n-nodes-base.supabase\",\n      \"typeVersion\": 1,\n      \"position\": [400, 550]\n    },\n    {\n      \"parameters\": {\n        \"channel\": \"#content-automation\",\n        \"messageType\": \"text\",\n        \"text\": \"✅ LinkedIn Post Published!\\n\\n📌 Topic: {{ $node['Prepare RAG Context'].json.topic.title }}\\n📝 Length: {{ $node['Validate Content'].json.content.length }} chars\\n🔗 RAG Relevance: {{ $node['Prepare RAG Context'].json.ragRelevance }}\\n\\nContent:\\n{{ $node['Validate Content'].json.content.substring(0, 200) }}...\"\n      },\n      \"id\": \"14\",\n      \"name\": \"Slack Notification\",\n      \"type\": \"n8n-nodes-base.slack\",\n      \"typeVersion\": 2,\n      \"position\": [550, 550]\n    }\n  ],\n  \"connections\": {\n    \"Schedule Trigger\": { \"main\": [[{ \"node\": \"Get Twitter Trends\", \"type\": \"main\", \"index\": 0 }, { \"node\": \"Get News Articles\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Get Twitter Trends\": { \"main\": [[{ \"node\": \"Merge Data Sources\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Get News Articles\": { \"main\": [[{ \"node\": \"Merge Data Sources\", \"type\": \"main\", \"index\": 1 }]] },\n    \"Merge Data Sources\": { \"main\": [[{ \"node\": \"Rank Topics\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Rank Topics\": { \"main\": [[{ \"node\": \"Generate Embedding\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Generate Embedding\": { \"main\": [[{ \"node\": \"Query Pinecone RAG\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Query Pinecone RAG\": { \"main\": [[{ \"node\": \"Prepare RAG Context\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Prepare RAG Context\": { \"main\": [[{ \"node\": \"Generate LinkedIn Post\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Generate LinkedIn Post\": { \"main\": [[{ \"node\": \"Parse Generated Content\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Parse Generated Content\": { \"main\": [[{ \"node\": \"Validate Content\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Validate Content\": { \"main\": [[{ \"node\": \"Schedule Posting Time\", \"type\": \"main\", \"index\": 0 }]] },\n    \"Schedule Posting Time\": { \"main\": [[{ \"node\": \"Store in Database\", \"type\": \"main\", \"index\": 0 }, { \"node\": \"Slack Notification\", \"type\": \"main\", \"index\": 0 }]] }\n  }\n}
```

---

## Testing & Deployment

### **Step 1: Set Up Credentials in n8n**

1. Go to n8n Dashboard → Credentials
2. Add new credentials for each service:
   - Google Gemini API: `GEMINI_API_KEY`
   - Twitter API v2: `TWITTER_BEARER_TOKEN`
   - Pinecone: `PINECONE_API_KEY`, `PINECONE_HOST`
   - NewsAPI: `NEWSAPI_KEY`
   - Supabase: Connection string
   - Slack: Bot token (if using Slack)

3. Set as environment variables in n8n `.env` file:
```
GEMINI_API_KEY=your_key_here
TWITTER_BEARER_TOKEN=your_token_here
PINECONE_API_KEY=your_key_here
PINECONE_HOST=https://your-index-xxxxx.pinecone.io
NEWSAPI_KEY=your_key_here
DATABASE_URL=postgresql://user:password@host/db
```

### **Step 2: Prepare Knowledge Base (Pinecone)**

1. Collect 10-20 of your best articles/insights as text files
2. Create a Python script to upload to Pinecone:

```python
import pinecone
from sentence_transformers import SentenceTransformer
import json

# Initialize
pinecone.init(api_key="YOUR_KEY", environment="us-west1-gcp")
index = pinecone.Index("linkedin-knowledge-base")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load your articles
articles = [
    {"id": "article-1", "title": "Your Article Title", "content": "Full article text..."},
    # ... more articles
]

# Generate embeddings and upload
for article in articles:
    embedding = model.encode(article['content']).tolist()
    index.upsert([(
        article['id'],
        embedding,
        {"title": article['title'], "content": article['content']}
    )])

print("Knowledge base uploaded successfully!")
```

### **Step 3: Create Database Table**

If using Supabase:
1. Go to SQL Editor
2. Run:
```sql
CREATE TABLE content_posts (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW(),
  posted_at TIMESTAMP,
  topic VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  linkedin_post_id VARCHAR(200),
  post_length INT,
  rag_relevance FLOAT,
  status VARCHAR(50) DEFAULT 'posted'
);
```

### **Step 4: Test Each Phase**

1. **Test Data Collection**: Run nodes 1-5, verify top 3 topics appear
2. **Test RAG**: Run nodes 6-8, verify expertise from knowledge base appears
3. **Test Content Generation**: Run node 9, verify LinkedIn post looks good
4. **Test Validation**: Run node 11, should pass without errors
5. **Test Full Workflow**: Enable scheduling and run once

### **Step 5: Deploy**

1. Activate the workflow (toggle "Active" to ON)
2. Set cron to run daily at 8 AM UTC
3. Monitor Slack/email for notifications
4. Check generated posts after 2-3 days of running
5. Adjust prompts if needed for better quality

---

## Troubleshooting

### **Issue: Gemini API returns 401 Unauthorized**
- Verify API key is correct in credentials
- Check API is enabled in Google Cloud Console
- Regenerate key if needed

### **Issue: Twitter API returns 403 Forbidden**
- Verify Bearer Token is current (may need refresh)
- Check API v2 endpoints are enabled
- Ensure account hasn't hit rate limits

### **Issue: Pinecone returns 0 matches**
- Your knowledge base may not be uploaded yet
- Check Pinecone index exists and has data
- Try with different topic to verify connection

### **Issue: Generated content is low quality**
- Adjust temperature in Gemini API (try 0.5-0.8)
- Improve system prompt with more specific guidelines
- Ensure knowledge base has relevant articles
- Try Gemini 1.5 Pro for better quality (higher cost)

### **Issue: LinkedIn posting fails**
- If using API: verify OAuth credentials and user ID
- If using Puppeteer: may need 2FA bypass, update password
- Consider switching to official API (more reliable)

### **Issue: Workflow times out**
- Split into multiple workflows (data collection → posting)
- Add timeout buffers between API calls
- Use "Continue on Error" for non-critical nodes

---

## Next Steps

1. ✅ Set up all API credentials
2. ✅ Upload knowledge base to Pinecone
3. ✅ Create database table
4. ✅ Import workflow JSON into n8n
5. ✅ Test Phase 1 (data collection)
6. ✅ Test Phase 2 (RAG retrieval)
7. ✅ Test Phase 3 (content generation)
8. ✅ Test full workflow end-to-end
9. ✅ Deploy and monitor for 3-5 days
10. ✅ Iterate on prompts and optimize

Ready to start implementation? Let me know what step you'd like help with!
