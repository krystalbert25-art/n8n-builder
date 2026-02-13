# Zero-Cost Content Automation - Complete Setup Guide

**Status**: Ready for Implementation
**Cost**: $0/month
**Time to Setup**: 45-60 minutes

---

## Table of Contents

1. [Prerequisites Check](#prerequisites-check)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)
6. [Running the Automation](#running-the-automation)

---

## Prerequisites Check

Before starting, verify you have:

- [ ] Windows 10/11 or Mac/Linux
- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Internet connection (for API calls)
- [ ] 8GB+ RAM (for Ollama Llama 2 model)
- [ ] ~10GB free disk space (for Ollama model + project files)
- [ ] Twitter/Gmail account (for posting)
- [ ] LinkedIn account (for posting)
- [ ] n8n installed and running locally

### Verify Prerequisites

**Windows PowerShell:**
```powershell
# Python
python --version

# Node.js
node --version
npm --version

# n8n (if installed)
npm list -g n8n
```

**Mac/Linux:**
```bash
python3 --version
node --version
npm --version
```

---

## Installation Steps

### Step 1: Set Up Project Directory

```powershell
# Navigate to n8n builder folder
cd "C:\Users\user\Documents\n8n builder"

# Verify you're in the right place
Get-ChildItem | Select-Object Name
# Should see: ZERO_COST_AUTOMATION_PLAN.md, embeddings_generator.py, init_database.py, etc.
```

### Step 2: Install Python Dependencies

```powershell
# Install required packages
pip install sentence-transformers chromadb python-dotenv

# Verify installation
pip list | findstr "sentence-transformers chromadb"
```

**Expected output:**
```
chromadb                  0.4.x
sentence-transformers    2.2.x
```

**Note**: First run will download ~400MB embedding model (one-time)

### Step 3: Install Node.js Dependencies

```powershell
# Create package.json
npm init -y

# Install Puppeteer and dependencies
npm install puppeteer dotenv chalk

# Verify installation
npm list
```

**Expected to see:**
```
├── puppeteer@21.x
├── dotenv@16.x
└── chalk@5.x
```

### Step 4: Install Ollama

#### On Windows:
1. Download from: https://ollama.ai/download/windows
2. Run the installer
3. Wait for installation to complete
4. Ollama will appear in system tray

#### On Mac:
```bash
curl https://ollama.ai/install.sh | sh
```

#### On Linux:
```bash
curl https://ollama.ai/install.sh | sh
ollama serve  # Start the service
```

### Step 5: Download Ollama Models

```powershell
# Start Ollama service (if not auto-running)
ollama serve

# In a new terminal, download model
ollama pull llama2

# Verify model loaded
ollama list

# Expected output:
# NAME      ID              SIZE     MODIFIED
# llama2    73bbeffe45c7    3.8 GB   2 minutes ago
```

**First-time download**: ~4GB (one-time), takes 5-10 minutes

### Step 6: Initialize Database

```powershell
python init_database.py init

# Verify database created
Get-Item content_automation.db

# Check with sample data
python init_database.py test
python init_database.py stats
```

**Expected output:**
```json
{
  "total_posts": 1,
  "posted_posts": 0,
  "draft_posts": 1,
  "trending_topics_tracked": 1,
  "execution_logs": 0,
  "knowledge_base_items": 0
}
```

### Step 7: Test Embeddings System

```powershell
# Test embedding search
$testQuery = @{
  "query" = "artificial intelligence and automation"
} | ConvertTo-Json

$testQuery | python embeddings_generator.py search

# Expected: {"query": "...", "results": []}  (empty because KB empty)
```

---

## Configuration

### Step 1: Create .env File

**File**: `.env` in `C:\Users\user\Documents\n8n builder\`

```bash
# Twitter Credentials (for Puppeteer automation)
TWITTER_EMAIL=your_twitter_email@gmail.com
TWITTER_PASSWORD=your_twitter_app_password

# LinkedIn Credentials (for Puppeteer automation)
LINKEDIN_EMAIL=your_linkedin_email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password

# Twitter API (Bearer Token for reading trends)
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Database Configuration
SQLITE_DB_PATH=./content_automation.db

# Optional: Reddit API
REDDIT_USER_AGENT=n8n-content-creator/1.0
```

### Step 2: Generate Twitter Credentials

**Get Twitter Bearer Token** (free):
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a Project (free tier)
3. Create an App
4. Generate a Bearer Token (Keys & Tokens section)
5. Copy and paste into `.env` as `TWITTER_BEARER_TOKEN`

**Get Twitter App Password** (for Puppeteer):
1. Log in to https://twitter.com
2. Settings → Security & Account Access → Password
3. Note: You'll need to authenticate with your phone number/email
4. Use regular Twitter password in `.env` as `TWITTER_PASSWORD`

### Step 3: Generate LinkedIn Credentials

**For LinkedIn Puppeteer Access:**
1. You'll use your regular LinkedIn email and password
2. LinkedIn may ask for 2FA - the script handles this by waiting
3. Add credentials to `.env` as `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`

### Step 4: Verify .env File

```powershell
# Windows: Verify file exists
Test-Path .env

# Check it's readable (don't print credentials!)
Get-Content .env | Measure-Object -Line

# Should show: Lines: 10+ (number of environment variables)
```

---

## Testing

### Test 1: Verify Ollama Model

```powershell
# Test Ollama is running
curl http://localhost:11434/api/tags

# Expected response: List of available models including llama2 and mistral

# Test model inference
$testPayload = @{
  model = "llama2"
  prompt = "What is AI? (answer in 1 sentence)"
  stream = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:11434/api/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body $testPayload | 
  Select-Object -ExpandProperty Content | ConvertFrom-Json

# Should return a generated response
```

### Test 2: Verify Embeddings

```powershell
# Test Python embeddings script
$test = @{
  query = "machine learning and AI trends"
} | ConvertTo-Json

$test | python embeddings_generator.py search | ConvertFrom-Json | ConvertTo-Json -Depth 3

# Expected:
# {
#   "query": "machine learning and AI trends",
#   "results": [],
#   "message": "Knowledge base is empty..."
# }
```

### Test 3: Test Database Logging

```powershell
python init_database.py stats

# Then manually check
python << 'EOF'
import sqlite3

conn = sqlite3.connect('content_automation.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM posts')
count = cursor.fetchone()[0]
conn.close()

print(f"Total posts in DB: {count}")
EOF
```

### Test 4: Test Twitter Posting (Manual)

```powershell
# Test Puppeteer connection to Twitter
# Create a test script
$tweets = @('This is a test tweet #automation') | ConvertTo-Json

node post_to_twitter.js $tweets

# Expected output:
# [Login] Navigating to Twitter...
# [Login] Starting authentication...
# ...
# [Success] All 1 tweets posted!
# {
#   "success": true,
#   "tweetsPosted": 1,
#   "timestamp": "2025-..."
# }
```

**Note**: First run may take 30+ seconds (opening browser, logging in)

### Test 5: Test LinkedIn Posting (Manual)

```powershell
node post_to_linkedin.js "Test LinkedIn post about automation and AI learning"

# Expected output:
# [Login] Navigating to LinkedIn...
# [Login] Starting authentication...
# ...
# [Success] Post published!
```

---

## Configuration for n8n

### Import n8n Workflow

1. **Open n8n**: Navigate to http://localhost:5678
2. **Create New Workflow**: Click "New"
3. **Import JSON**: Click Menu → Import from File
4. **Select**: `zero-cost-content-automation.json`
5. **Review Nodes**: Check all nodes are present

### Configure Credentials in n8n

#### Twitter Bearer Token
1. Go to Credentials → New → Twitter
2. Auth Type: "OAuth"
3. Paste Bearer Token
4. Save

#### Execute Command Node Credentials
1. Credentials → New → Execute Command
2. Remote Host: `localhost`
3. Port: `22` (or SSH port)
4. Or leave blank for local execution
5. Save

### Edit Workflow Nodes

**Node: "Schedule Trigger"**
- Trigger type: Cron
- Interval: Every 1 day at 08:00 AM
- Timezone: Your timezone

**Node: "Twitter Search"**
- Query: `AI OR automation OR llama OR chatgpt -is:retweet lang:en`
- Max Results: 100
- Tweet Fields: `public_metrics`

**Node: "Generate LinkedIn Post"**
- URL: `http://localhost:11434/api/generate`
- Method: POST
- Body:
```json
{
  "model": "llama2",
  "prompt": "Create a professional LinkedIn post (300 chars) about: {{ $json.title }}\nMake it engaging with insights and hashtags.\n\nPost:",
  "stream": false,
  "temperature": 0.7
}
```

**Nodes: "Post to Twitter" & "Post to LinkedIn"**
- Command: Use absolute paths
- `node "C:\Users\user\Documents\n8n builder\post_to_twitter.js" '{{ JSON.stringify($json.response) }}'`
- Environment: Pass with stdin

---

## Running the Automation

### Manual Start

```powershell
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start n8n
n8n start

# Terminal 3: Monitor logs
# Access http://localhost:5678

# Save and activate workflow
# Click "Execute Workflow" to test
```

### Scheduled Execution

1. In n8n, set Schedule Trigger to desired time (default: 8 AM daily)
2. Click "Activate"
3. Workflow will run automatically at scheduled time
4. Check logs: http://localhost:5678/workflow/logs

### Manual Execution (Testing)

1. Open workflow in n8n
2. Click "Execute Workflow" button
3. Monitor execution in bottom panel
4. Check SQLite logs:
```powershell
python init_database.py recent
```

---

## File Structure

After setup, your directory should look like:

```
n8n builder/
├── .env                                    # Environment variables
├── package.json                            # Node.js dependencies
├── content_automation.db                   # SQLite database (auto-created)
├── chroma_db/                              # Vector database (auto-created)
│   └── ...
├── ZERO_COST_AUTOMATION_PLAN.md           # This architecture guide
├── SETUP_GUIDE.md                         # This file
├── embeddings_generator.py                # Embeddings system
├── init_database.py                       # Database initialization
├── post_to_twitter.js                     # Twitter automation script
├── post_to_linkedin.js                    # LinkedIn automation script
├── zero-cost-content-automation.json      # n8n workflow
└── node_modules/                          # Node packages (auto-created)
    └── ...
```

---

## Troubleshooting

### Issue: "Ollama: Command not found"

**Solution:**
```powershell
# Ollama should be in PATH. Check:
$env:Path -split ';' | Select-String ollama

# If not found, add manually:
# Control Panel → System → Environment Variables → Edit PATH
# Add: C:\Users\[username]\AppData\Local\Programs\Ollama
```

### Issue: "Python module not found: sentence_transformers"

**Solution:**
```powershell
# Reinstall with specific version
pip install --upgrade sentence-transformers chromadb

# Or use specific Python:
python -m pip install sentence-transformers chromadb
```

### Issue: "Cannot find module 'puppeteer'"

**Solution:**
```powershell
npm install puppeteer
npm list puppeteer
```

### Issue: "Twitter login fails with Puppeteer"

**Possible Causes:**
1. Incorrect email/password in `.env`
2. 2FA enabled on account
3. Twitter security block on automated access

**Solution:**
```powershell
# Debug mode - keep browser visible
# Edit post_to_twitter.js line: headless: false

# Check for 2FA
# Manually log in first: https://twitter.com/login
# Complete any security challenges

# Lower security on Twitter account (temporary)
# Settings → Security & Account Access → Apps and sessions
```

### Issue: "LinkedIn login fails with Puppeteer"

**Most Common:**
LinkedIn frequently changes UI structure. Selectors may need updates.

**Solution:**
```powershell
# Edit post_to_linkedin.js to show browser
# Change: headless: true → headless: false

# Compare selectors with current LinkedIn UI
# Update selectors for new fields
```

### Issue: "Chroma database errors"

**Solution:**
```powershell
# Reset Chroma DB
Remove-Item -Recurse chroma_db/

# Recreate
python embeddings_generator.py stats
```

### Issue: "n8n workflow execution hangs"

**Solution:**
1. Check if Ollama is running: `ollama serve`
2. Check if scripts are executable: `node post_to_twitter.js`
3. Check environment variables in n8n
4. Set timeout on Execute Command nodes to 60000ms

### Issue: "Puppeteer browser times out"

**Solution:**
```powershell
# Update Puppeteer to latest
npm install puppeteer@latest

# Increase timeouts in scripts
# Change all: timeout: 30000 → timeout: 60000
```

---

## Performance Tuning

### For Faster Generation

**Use Mistral instead of Llama2:**
```powershell
ollama pull mistral
# Then update n8n workflow: "model": "mistral"
# ~3x faster inference
```

### For Lower Resource Usage

**Use smaller embedding model:**
Edit `embeddings_generator.py`:
```python
# Change from:
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim

# To:
model = SentenceTransformer('distiluse-base-multilingual-cased-v2')  # Smallest
```

### For Better Quality

**Use larger model (with GPU):**
```powershell
# Requires NVIDIA GPU with CUDA
ollama pull ollama:neural-chat-7b

# Or use 13B model if you have 16GB+ RAM
ollama pull llama2:13b
```

---

## Next Steps

1. ✅ Complete setup (this guide)
2. Seed knowledge base with your content
3. Configure posting times in n8n
4. Run first full workflow cycle
5. Monitor engagement metric (in SQLite)
6. Adjust prompts for better content
7. Optimize posting schedule

---

## Support & Monitoring

### Check Workflow Status

```powershell
# View recent executions
python init_database.py recent

# Full execution logs
python << 'EOF'
import sqlite3
import json

conn = sqlite3.connect('content_automation.db')
cursor = conn.cursor()

cursor.execute('''
  SELECT timestamp, status, message FROM execution_logs 
  ORDER BY timestamp DESC LIMIT 10
''')

for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]:8} | {row[2][:50]}")

conn.close()
EOF
```

### Monitor Posted Content

```powershell
python << 'EOF'
import sqlite3

conn = sqlite3.connect('content_automation.db')
cursor = conn.cursor()

cursor.execute('''
  SELECT platform, status, COUNT(*) FROM posts 
  GROUP BY platform, status
''')

for row in cursor.fetchall():
    print(f"{row[0]:10} | {row[1]:10} | {row[2]} posts")

conn.close()
EOF
```

---

## Backup & Recovery

```powershell
# Backup database
Copy-Item content_automation.db "content_automation.db.bak"

# Backup knowledge base
Copy-Item -Recurse chroma_db "chroma_db.bak"

# Restore if needed
Copy-Item "content_automation.db.bak" content_automation.db
```

---

**Setup Complete!** 🎉

Your zero-cost content automation system is ready to run. Start with Step "Running the Automation" above.

For questions or issues, check the Troubleshooting section or refer to the main architecture guide.

---

**Last Updated**: 2025
**Version**: 1.0
**Status**: Production Ready

