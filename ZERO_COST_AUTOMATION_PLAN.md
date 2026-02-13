# Zero-Cost LinkedIn & Twitter Content Automation - Complete Architecture

**Status**: Learning & Practice | Zero Cost | No Paywalls
**Date Created**: 2025
**Purpose**: Full end-to-end automation using only free/open-source tools

---

## Executive Summary: Cost Breakdown vs Original Plan

### Original Plan (Paid APIs - $5-15/month)
- Google Gemini 1.5 Flash: $0.70/month
- Gemini Embeddings API: $0.15/month
- Pinecone Vector DB: Free tier, but eventually paid
- Twitter API v2: Free read, paid write (PAYWALL)
- LinkedIn API: Restricted/Paid
- NewsAPI: Free tier limited
- **Issue**: Twitter write access blocked on free tier

### Zero-Cost Alternative Stack
| Component | Original | Alternative | Cost | Notes |
|-----------|----------|--------------|------|-------|
| **Content Generation** | Gemini 1.5 Flash | Ollama (Llama 2) locally | FREE | Open-source LLM on your machine |
| **Embeddings** | Gemini Embeddings | sentence-transformers (local) | FREE | Python library, 768-dim vectors |
| **Vector Database** | Pinecone | Chroma (local) | FREE | In-memory/SQLite backend |
| **Twitter Posting** | API v2 (paywall) | Puppeteer automation | FREE | Browser automation workaround |
| **LinkedIn Posting** | LinkedIn API (restricted) | Puppeteer automation | FREE | Browser-based posting |
| **Trending Data** | NewsAPI (limited free) | Twitter Search + Reddit API | FREE | Official free APIs, no paywall |
| **Data Collection** | RSS feeds + scraping | Twitter/Reddit/HN direct API | FREE | Native API + Cheerio scraping |
| **Database/Logging** | PostgreSQL (Supabase) | SQLite local | FREE | Single-file database |
| **Notifications** | Gmail API | SQLite logging + console | FREE | File-based audit logs |

---

## Architecture: Zero-Cost Alternative System

```
┌─────────────────────────────────────────────────────────────────┐
│           DAILY TRIGGER (Cron: 8 AM UTC)                        │
└────────────┬────────────────────────────────────────────────────┘
             │
    ┌────────▼────────────┐
    │ DATA COLLECTION     │
    │ (FREE APIS)         │
    ├─ Twitter Search API │
    ├─ Reddit API         │
    ├─ Hacker News API    │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ RANK TOP 5 TOPICS   │
    │ (n8n Code node)     │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ LOCAL EMBEDDINGS    │
    │ (sentence-trans)    │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ VECTOR SEARCH       │
    │ (Chroma local)      │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ GENERATE CONTENT    │
    │ (Ollama/Llama 2)    │
    │ LinkedIn + Twitter  │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ PUPPETEER POSTING   │
    │ Twitter webUI       │
    │ LinkedIn webUI      │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ LOG TO SQLITE       │
    │ Track & Audit       │
    └─────────────────────┘
```

---

## Component 1: FREE DATA COLLECTION

### Option A: Twitter Search API (Free)
- **Endpoint**: `https://api.twitter.com/2/tweets/search/recent`
- **Requires**: Bearer Token (free)
- **Limits**: Last 7 days, 450 requests/15 min
- **n8n Setup**:
  ```javascript
  // HTTP GET Request
  const query = "AI OR automation OR ChatGPT";
  const url = `https://api.twitter.com/2/tweets/search/recent?query=${encodeURIComponent(query)}&max_results=100&tweet.fields=public_metrics`;
  return {
    url,
    headers: { Authorization: `Bearer ${process.env.TWITTER_BEARER_TOKEN}` },
    method: 'GET'
  };
  ```

### Option B: Reddit API (Free)
- **Endpoint**: `https://www.reddit.com/r/{subreddit}/top.json`
- **Requires**: User-Agent header only
- **Limits**: Very generous, rate-limited but not enforced for educational use
- **n8n Setup**:
  ```javascript
  const url = `https://www.reddit.com/r/MachineLearning/top.json?t=day&limit=50`;
  return {
    url,
    headers: { 
      'User-Agent': 'Mozilla/5.0 n8n-automation/1.0'
    },
    method: 'GET'
  };
  ```

### Option C: Hacker News API (Free)
- **Endpoint**: `https://hacker-news.firebaseio.com/v0/`
- **Requires**: None (completely public)
- **Limits**: Unlimited
- **n8n Setup**:
  ```javascript
  // Get top 30 stories
  const url = `https://hacker-news.firebaseio.com/v0/topstories.json`;
  const stories = await fetch(url).then(r => r.json());
  const top10Ids = stories.slice(0, 10);
  
  // Fetch details for each
  const details = await Promise.all(
    top10Ids.map(id => 
      fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`)
        .then(r => r.json())
    )
  );
  
  return details.filter(s => s.title.toLowerCase().match(/ai|automation|llm|chatgpt/i));
  ```

---

## Component 2: LOCAL EMBEDDINGS & RAG

### Setup 2A: Install Python Dependencies

**File**: `setup_embeddings.sh` (or `.bat` for Windows)
```bash
pip install sentence-transformers chromadb python-dotenv
```

### Setup 2B: Create Embeddings Script

**File**: `embeddings_generator.py`
```python
import json
import sys
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize embedding model (auto-downloads ~400MB first run)
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, fast, accurate

# Initialize Chroma (local vector DB)
client = chromadb.Client()
collection = client.get_or_create_collection(
    name="content_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

def embed_and_store(texts, metadata_list=None):
    """Generate embeddings and store in vector DB"""
    embeddings = model.encode(texts, show_progress_bar=False)
    
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        collection.upsert(
            ids=[f"doc_{i}"],
            embeddings=[emb.tolist()],
            documents=[text],
            metadatas=[metadata_list[i] if metadata_list else {"source": "unknown"}]
        )
    
    return {"stored": len(texts), "collection_size": collection.count()}

def search(query_text, top_k=5):
    """Search vector DB for similar content"""
    query_embedding = model.encode([query_text])[0]
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    return {
        "query": query_text,
        "results": [
            {
                "content": doc,
                "similarity": 1 - dist,  # Convert distance to similarity
                "metadata": meta
            }
            for doc, dist, meta in zip(
                results['documents'][0],
                results['distances'][0],
                results['metadatas'][0]
            )
        ]
    }

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "search"
    
    if action == "embed":
        # Read input JSON: [{"text": "...", "source": "..."}, ...]
        input_data = json.loads(sys.stdin.read())
        texts = [item['text'] for item in input_data]
        metadata_list = [{"source": item.get('source', 'unknown')} for item in input_data]
        result = embed_and_store(texts, metadata_list)
        print(json.dumps(result))
    
    elif action == "search":
        # Read input JSON: {"query": "..."}
        input_data = json.loads(sys.stdin.read())
        result = search(input_data['query'], top_k=5)
        print(json.dumps(result))
```

**n8n Integration**:
```javascript
// Execute Python Script Node
// Command: python embeddings_generator.py search
// Input: {query: topic}
// Output: Relevant context from your knowledge base

// For embedding new content:
// Execute periodically with new articles
```

---

## Component 3: LOCAL LLM (OLLAMA)

### Setup 3A: Install Ollama
- Download: https://ollama.ai
- Windows/Mac/Linux support
- First run: `ollama pull llama2` (~4GB download, one-time)

### Setup 3B: Start Ollama Service
```bash
# Windows (PowerShell)
ollama serve

# Mac/Linux
ollama serve &
```

### Setup 3C: n8n Integration

**n8n HTTP Request Node**:
```javascript
{
  url: "http://localhost:11434/api/generate",
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: {
    model: "llama2",
    prompt: `Generate a LinkedIn post about: ${topic.title}\n\nContext: ${ragContext}\n\nPost:`,
    stream: false,
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40
  }
}
```

**Output Format**:
```json
{
  "response": "Generated content here...",
  "done": true
}
```

### Prompt Templates for Ollama

**LinkedIn Post Generation**:
```
You are a professional content creator specializing in AI and Automation.

Topic: {topic_title}
Summary: {topic_summary}

Related expertise from your knowledge base:
{rag_context}

Create a compelling LinkedIn post (200-300 words) that:
1. Starts with a hook/question
2. Provides unique insight mixed with the trending topic
3. Includes practical takeaway
4. Ends with engagement question
5. Incorporates 3-4 relevant hashtags

Keep it conversational, avoid corporate jargon. Post:
```

**Twitter Thread Generation**:
```
Create a 4-tweet thread about this topic:
Topic: {topic_title}
Context: {rag_context}

Constraints:
- Tweet 1: Hook (max 280 chars)
- Tweet 2-3: Value/insight (each max 280 chars)
- Tweet 4: CTA + hashtags (max 280 chars)

Format as JSON array: ["tweet 1", "tweet 2", "tweet 3", "tweet 4"]

Tweets:
```

---

## Component 4: PUPPETEER BROWSER AUTOMATION

### Setup 4A: Install Node Dependencies

**File**: `package.json`
```json
{
  "name": "content-automation",
  "version": "1.0.0",
  "dependencies": {
    "puppeteer": "^21.0.0",
    "dotenv": "^16.0.0",
    "chalk": "^5.0.0"
  }
}
```

**Install**: `npm install` in workspace directory

### Setup 4B: Twitter Posting Script (Improved)

**File**: `post_to_twitter.js`
```javascript
const puppeteer = require('puppeteer');
const fs = require('fs');

async function postTwitterThread(tweets, credentials) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    // Navigate to Twitter
    console.log('Opening Twitter...');
    await page.goto('https://twitter.com/home', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });

    // Check if already logged in
    const isLoggedIn = await page.$('[aria-label="Post"]') !== null;
    
    if (!isLoggedIn) {
      console.log('Logging in...');
      await loginToTwitter(page, credentials);
    }

    // Post each tweet
    for (let i = 0; i < tweets.length; i++) {
      const tweet = tweets[i];
      console.log(`Posting tweet ${i + 1}/${tweets.length}: "${tweet.substring(0, 50)}..."`);
      
      await postTweet(page, tweet);
      
      // If not the last tweet, click reply
      if (i < tweets.length - 1) {
        console.log('Preparing for next tweet in thread...');
        await page.waitForTimeout(2000);
        const replyButton = await page.$('[aria-label="Reply"]');
        if (replyButton) {
          await replyButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }

    console.log('✓ All tweets posted successfully!');
    return { success: true, tweetsPosted: tweets.length };

  } catch (error) {
    console.error('✗ Error:', error.message);
    return { success: false, error: error.message };
  } finally {
    await browser.close();
  }
}

async function loginToTwitter(page, credentials) {
  // Click email field
  await page.click('input[autocomplete="username"]');
  await page.type('input[autocomplete="username"]', credentials.email);
  
  // Click next
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Next')) {
      await btn.click();
      break;
    }
  }

  await page.waitForTimeout(1000);

  // Enter password
  const passwordField = await page.$('input[type="password"]');
  if (passwordField) {
    await passwordField.type(credentials.password);
    
    // Click login
    const loginBtn = await page.$('button[type="submit"]');
    if (loginBtn) await loginBtn.click();
  }

  // Wait for login to complete
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 });
}

async function postTweet(page, content) {
  // Click compose button
  const composeBtn = await page.$('[aria-label="Post"]');
  if (!composeBtn) throw new Error('Compose button not found');
  await composeBtn.click();

  await page.waitForTimeout(500);

  // Find and fill text area
  const textarea = await page.$('[data-testid="tweetTextarea_0"]') || 
                   await page.$('div[role="textbox"]');
  if (!textarea) throw new Error('Text area not found');

  await textarea.click();
  await page.type('div[role="textbox"]', content);

  await page.waitForTimeout(500);

  // Post button
  const postBtn = await page.$('[data-testid="Tweet-send-button"]');
  if (!postBtn) throw new Error('Post button not found');
  
  await postBtn.click();

  // Wait for confirmation
  await page.waitForTimeout(2000);
}

// Main execution
const tweets = JSON.parse(process.argv[2] || '[]');
const credentials = {
  email: process.env.TWITTER_EMAIL,
  password: process.env.TWITTER_PASSWORD
};

if (!tweets.length) {
  console.error('ERROR: No tweets provided');
  process.exit(1);
}

if (!credentials.email || !credentials.password) {
  console.error('ERROR: Twitter credentials not set in environment');
  process.exit(1);
}

postTwitterThread(tweets, credentials)
  .then(result => {
    console.log(JSON.stringify(result));
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error(JSON.stringify({ success: false, error: error.message }));
    process.exit(1);
  });
```

### Setup 4C: LinkedIn Posting Script

**File**: `post_to_linkedin.js`
```javascript
const puppeteer = require('puppeteer');

async function postLinkedIn(content, credentials) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox']
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    console.log('Opening LinkedIn...');
    await page.goto('https://www.linkedin.com/feed/', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Check login
    const isLoggedIn = await page.$('[data-test-id="topcard-profile-photo"]') !== null;
    
    if (!isLoggedIn) {
      console.log('Logging in...');
      await loginToLinkedIn(page, credentials);
    }

    console.log('Creating post...');
    
    // Click post composer
    const postBtn = await page.$('[data-test-id="top-card-post-button"]') ||
                    await page.$('button:has-text("Start a post")');
    if (!postBtn) throw new Error('Post button not found');
    await postBtn.click();

    await page.waitForTimeout(1000);

    // Find text area and type content
    const textarea = await page.$('div[role="textbox"]');
    if (!textarea) throw new Error('Text area not found');
    
    await textarea.click();
    await page.type('div[role="textbox"]', content);

    await page.waitForTimeout(500);

    // Post button in modal
    const modal = await page.$('[data-testid="left-rail-app-switcher-icon"]');
    const postBtns = await page.$$('button');
    let posted = false;

    for (const btn of postBtns) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text.includes('Post') && text.length < 10) {
        await btn.click();
        posted = true;
        break;
      }
    }

    if (!posted) throw new Error('Could not find post button');

    await page.waitForTimeout(3000);
    console.log('✓ Post created successfully!');
    
    return { success: true };

  } catch (error) {
    console.error('✗ Error:', error.message);
    return { success: false, error: error.message };
  } finally {
    await browser.close();
  }
}

async function loginToLinkedIn(page, credentials) {
  // Email
  await page.type('input[name="session_key"]', credentials.email);
  // Password
  await page.type('input[name="session_password"]', credentials.password);
  // Submit
  await page.click('button[type="submit"]');
  
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 });
}

// Main
const content = process.argv[2];
const credentials = {
  email: process.env.LINKEDIN_EMAIL,
  password: process.env.LINKEDIN_PASSWORD
};

if (!content) {
  console.error('ERROR: No content provided');
  process.exit(1);
}

if (!credentials.email || !credentials.password) {
  console.error('ERROR: LinkedIn credentials not set');
  process.exit(1);
}

postLinkedIn(content, credentials)
  .then(result => {
    console.log(JSON.stringify(result));
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error(JSON.stringify({ success: false, error: error.message }));
    process.exit(1);
  });
```

---

## Component 5: LOCAL DATABASE (SQLITE)

### Setup 5A: Create SQLite Schema

**File**: `init_database.py`
```python
import sqlite3
import json
from datetime import datetime

def init_database(db_path='content_automation.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Posts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        platform TEXT,  -- 'twitter' or 'linkedin'
        content TEXT,
        topic TEXT,
        status TEXT,  -- 'draft', 'posted', 'failed'
        error_message TEXT,
        engagement_clicks INTEGER DEFAULT 0,
        engagement_shares INTEGER DEFAULT 0,
        engagement_comments INTEGER DEFAULT 0
    )
    ''')

    # Topics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trending_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        topic_title TEXT,
        source TEXT,  -- 'twitter', 'reddit', 'hn', 'news'
        engagement_score REAL,
        url TEXT,
        relevant_context TEXT
    )
    ''')

    # Logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workflow_name TEXT,
        status TEXT,  -- 'success', 'error', 'warning'
        message TEXT,
        metadata TEXT  -- JSON
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized: {db_path}")

if __name__ == "__main__":
    init_database()
```

### Setup 5B: n8n Database Integration

**n8n HTTP Request Node** (log post):
```javascript
// After successful posting
return {
  url: "http://localhost:3000/api/database/insert",  // Your local API or execute Node.js
  method: "POST",
  body: {
    table: "posts",
    data: {
      platform: "twitter",
      content: generatedContent,
      topic: topic.title,
      status: "posted",
      date_created: new Date().toISOString()
    }
  }
};
```

Or use **Execute Node.js** node directly:
```javascript
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('content_automation.db');

db.run(
  `INSERT INTO posts (platform, content, topic, status) VALUES (?, ?, ?, ?)`,
  ['twitter', $input.first().content, $input.first().topic, 'posted'],
  function(err) {
    if (err) throw err;
    return { success: true, rowId: this.lastID };
  }
);
```

---

## Complete n8n Workflow JSON (Zero-Cost)

**File**: `zero-cost-content-automation.json`

```json
{
  "name": "Zero-Cost Content Creator",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "intervalValue": 1,
              "intervalUnit": "days",
              "triggerAtTime": "08:00"
            }
          ]
        }
      },
      "id": "Schedule_Trigger",
      "name": "Trigger Daily at 8 AM",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [
        250,
        300
      ]
    },
    {
      "parameters": {
        "url": "https://api.twitter.com/2/tweets/search/recent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "twitterApi",
        "method": "GET",
        "requestParameters": {
          "query": "AI OR automation OR llm OR chatgpt -is:retweet",
          "max_results": "100",
          "tweet.fields": "public_metrics"
        }
      },
      "id": "Twitter_Search",
      "name": "Fetch Twitter Trending",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        450,
        200
      ]
    },
    {
      "parameters": {
        "url": "=https://www.reddit.com/r/MachineLearning/top.json?t=day&limit=50",
        "method": "GET",
        "requestParameters": {
          "headers": [
            {
              "name": "User-Agent",
              "value": "Mozilla/5.0 n8n-automation/1.0"
            }
          ]
        }
      },
      "id": "Reddit_API",
      "name": "Fetch Reddit Trending",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        450,
        350
      ]
    },
    {
      "parameters": {
        "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "method": "GET"
      },
      "id": "HackerNews_API",
      "name": "Fetch Hacker News",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        450,
        500
      ]
    },
    {
      "parameters": {
        "jsCode": "// Aggregate and rank all sources\nconst twitter = $input.first().data || {};\nconst reddit = $input.all()[1]?.data || {};\nconst hn = $input.all()[2]?.data || [];\n\n// Score and select top 5\nconst topics = [];\nconst scores = {};\n\n// Tweet metrics (if available)\nif (twitter.data) {\n  twitter.data.slice(0, 10).forEach(tweet => {\n    const score = tweet.public_metrics.like_count * 0.1 + tweet.public_metrics.retweet_count * 0.5;\n    topics.push({ title: tweet.text.substring(0, 100), source: 'twitter', score, url: `https://twitter.com/i/web/status/${tweet.id}` });\n  });\n}\n\n// Take top 5 overall\nreturn topics.sort((a, b) => b.score - a.score).slice(0, 5).map((t, i) => ({ ...t, rank: i + 1 }));"
      },
      "id": "Rank_Topics",
      "name": "Rank & Select Top 5",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        700,
        350
      ]
    },
    {
      "parameters": {
        "command": "= python embeddings_generator.py search",
        "stdin": "={\"query\": \"{{ $json.title }}\"}"
      },
      "id": "Generate_Embeddings",
      "name": "Generate Embeddings",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [
        900,
        350
      ]
    },
    {
      "parameters": {
        "url": "=http://localhost:11434/api/generate",
        "method": "POST",
        "requestParameters": {
          "headers": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "body": {
          "contentType": "application/json",
          "content": "={\n  \"model\": \"llama2\",\n  \"prompt\": \"You are a professional content creator. Create a LinkedIn post (250 words) about:\\n{{ $json.title }}\\n\\nMake it engaging and add 3-4 hashtags. Include unique insights. Post:\",\n  \"stream\": false,\n  \"temperature\": 0.7\n}"
        }
      },
      "id": "Generate_LinkedIn_Post",
      "name": "Generate LinkedIn Post",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        1100,
        200
      ]
    },
    {
      "parameters": {
        "url": "=http://localhost:11434/api/generate",
        "method": "POST",
        "body": {
          "contentType": "application/json",
          "content": "={\n  \"model\": \"llama2\",\n  \"prompt\": \"Create a 4-tweet thread about: {{ $json.title }}\\n\\nFormat as JSON array with 4 elements. Each tweet max 280 chars. Start with hook, include value, end with CTA.\\n\\nJSON:\",\n  \"stream\": false,\n  \"temperature\": 0.7\n}"
        }
      },
      "id": "Generate_Twitter_Thread",
      "name": "Generate Twitter Thread",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        1100,
        350
      ]
    },
    {
      "parameters": {
        "command": "=node post_to_linkedin.js \"{{ $json.response }}\"",
        "stdin": ""
      },
      "id": "Post_to_LinkedIn",
      "name": "Post to LinkedIn",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [
        1300,
        150
      ],
      "credentials": {
        "executeCommand": "executeCommand_credential"
      }
    },
    {
      "parameters": {
        "command": "=node post_to_twitter.js '{{ JSON.stringify($json.response) }}'",
        "stdin": ""
      },
      "id": "Post_to_Twitter",
      "name": "Post to Twitter",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [
        1300,
        300
      ]
    },
    {
      "parameters": {
        "command": "=python << 'EOF'\nimport sqlite3\nimport json\nfrom datetime import datetime\n\nconn = sqlite3.connect('content_automation.db')\ncursor = conn.cursor()\n\ncursor.execute('''\n  INSERT INTO posts (platform, content, topic, status)\n  VALUES (?, ?, ?, ?)\n''', ('twitter', '{{ $json.response }}', '{{ $json.topic }}', 'posted'))\n\nconn.commit()\nconn.close()\nprint(json.dumps({\"logged\": 1}))\nEOF"
      },
      "id": "Log_to_SQLite",
      "name": "Log Results to SQLite",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [
        1500,
        350
      ]
    }
  ],
  "connections": {
    "Schedule_Trigger": {
      "main": [
        [
          {
            "node": "Twitter_Search",
            "type": "main",
            "index": 0
          },
          {
            "node": "Reddit_API",
            "type": "main",
            "index": 0
          },
          {
            "node": "HackerNews_API",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Twitter_Search": {
      "main": [
        [
          {
            "node": "Rank_Topics",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Reddit_API": {
      "main": [
        [
          {
            "node": "Rank_Topics",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "HackerNews_API": {
      "main": [
        [
          {
            "node": "Rank_Topics",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Rank_Topics": {
      "main": [
        [
          {
            "node": "Generate_Embeddings",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Generate_Embeddings": {
      "main": [
        [
          {
            "node": "Generate_LinkedIn_Post",
            "type": "main",
            "index": 0
          },
          {
            "node": "Generate_Twitter_Thread",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Generate_LinkedIn_Post": {
      "main": [
        [
          {
            "node": "Post_to_LinkedIn",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Generate_Twitter_Thread": {
      "main": [
        [
          {
            "node": "Post_to_Twitter",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Post_to_LinkedIn": {
      "main": [
        [
          {
            "node": "Log_to_SQLite",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Post_to_Twitter": {
      "main": [
        [
          {
            "node": "Log_to_SQLite",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Environment Variables

**File**: `.env`
```bash
# Twitter
TWITTER_BEARER_TOKEN=your_free_bearer_token
TWITTER_EMAIL=your_email@gmail.com
TWITTER_PASSWORD=your_app_password

# LinkedIn
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_app_password

# Local Services
OLLAMA_HOST=http://localhost:11434
SQLITE_DB_PATH=./content_automation.db
```

---

## Step-by-Step Setup Guide

### 1. Install Prerequisites (Windows)
```powershell
# Python 3.9+
python --version

# Node.js 16+
node --version

# Git
git --version
```

### 2. Install Python Dependencies
```powershell
cd "c:\Users\user\Documents\n8n builder"
pip install sentence-transformers chromadb python-dotenv sqlite3
```

### 3. Install Ollama
- Download from https://ollama.ai/download
- Run installer, follow setup
- Start: `ollama serve` (leave running)
- In new terminal: `ollama pull llama2`

### 4. Install Node Dependencies
```powershell
npm init -y
npm install puppeteer dotenv chalk
```

### 5. Create Python Scripts
- Copy `embeddings_generator.py` to workspace
- Copy `init_database.py` to workspace
- Run: `python init_database.py`

### 6. Create Node Scripts
- Copy `post_to_twitter.js` to workspace
- Copy `post_to_linkedin.js` to workspace
- Create `.env` file with credentials

### 7. Configure n8n
- Import `zero-cost-content-automation.json`
- Test each node individually
- Set up cron trigger for daily 8 AM

### 8. Test End-to-End
```powershell
# Terminal 1: Ollama
ollama serve

# Terminal 2: n8n
n8n start

# Terminal 3: Manual test
node post_to_twitter.js '["Test tweet 1", "Test tweet 2"]'
```

---

## Cost Analysis

| Component | Original Cost | Zero-Cost Alternative | Savings |
|-----------|---------------|----------------------|---------|
| Gemini LLM | $0.70/mo | Ollama (local Llama 2) | **$0** |
| Gemini Embeddings | $0.15/mo | sentence-transformers | **$0** |
| Pinecone | $25/mo (eventually) | Chroma local | **$0** |
| Twitter API write | Paywall | Puppeteer | **$0** |
| LinkedIn API | Restricted | Puppeteer | **$0** |
| Database | $5-20/mo | SQLite | **$0** |
| NewsAPI | $49+/mo (paid) | Twitter/Reddit/HN free APIs | **$0** |
| **TOTAL** | **$80+/mo** | **$0** | **$80/mo** |

**Hardware Requirement**: ~8GB RAM for Ollama (Llama 2 model), existing computer sufficient
**Internet**: Free API calls, minimal bandwidth

---

## Limitations & Tradeoffs

### Ollama vs Gemini
- ✅ Free, local, no API calls
- ✅ No rate limits
- ❌ Slower (few seconds per generation on CPU)
- ❌ Lower quality than commercial LLMs (but still useful for learning)
- **Solution**: Use smaller models (Mistral 7B) for faster inference

### Puppeteer vs Official APIs
- ✅ Free, no paywall
- ✅ Bypasses authentication completely
- ❌ Fragile (UI changes break it)
- ❌ Slower (5-30 seconds per post)
- ❌ Can't detect errors reliably
- **Solution**: Monitor closely, update selectors when Twitter/LinkedIn UI changes

### Local Embeddings vs Gemini
- ✅ Free, fast for small knowledge bases
- ❌ Lower quality for large/diverse topics
- **Solution**: Works fine for personal knowledge base (< 1000 docs)

---

## Performance Tips

1. **Faster LLM**: Use Mistral 7B instead of Llama 2
   ```bash
   ollama pull mistral
   # Update workflow to use "mistral" instead of "llama2"
   ```

2. **GPU Acceleration**: Install CUDA/Metal support for Ollama
   - Windows/Linux NVIDIA: https://docs.nvidia.com/cuda/

3. **Batch Processing**: Generate multiple posts in one trigger
   - Reduces overhead from startup times
   - Creates content buffer for better posting times

4. **Caching**: Store embeddings for frequently-searched topics
   - Chroma automatically handles this

---

## Next Steps

1. ✅ Install all prerequisites (this guide)
2. ✅ Set up local services (Ollama, SQLite)
3. ⬜ Configure n8n workflow with your actual credentials
4. ⬜ Test each node individually before full automation
5. ⬜ Monitor first few executions for Puppeteer breakage
6. ⬜ Adjust prompts for output quality
7. ⬜ Set up error handling (email on failures)

---

## Troubleshooting

**Ollama slow?**
→ Try smaller model: `ollama pull mistral`

**Puppeteer fails on login?**
→ Add screenshots: `await page.screenshot({path: 'debug.png'})`

**Embeddings query returns nothing?**
→ Seed knowledge base first with sample documents

**n8n Execute Command hangs?**
→ Set timeout in node settings

**Chroma connection errors?**
→ Ensure write permissions in workspace directory

---

**Created for**: Learning & Practice | Zero Cost | No Paywalls
**Last Updated**: 2025
**Status**: Ready for Implementation

```

