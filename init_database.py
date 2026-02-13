#!/usr/bin/env python3
"""
Initialize SQLite database for content automation logging
Zero-cost alternative to PostgreSQL/Supabase
"""

import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = "content_automation.db"

def init_database(db_path=DATABASE_PATH):
    """Create all necessary tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"[Init] Creating tables in: {db_path}")
    
    # Posts table - tracks all generated and posted content
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_posted TIMESTAMP,
        platform TEXT NOT NULL,  -- 'twitter' or 'linkedin'
        content TEXT NOT NULL,
        topic TEXT,
        source TEXT,  -- where the topic came from
        status TEXT DEFAULT 'draft',  -- 'draft', 'posted', 'failed', 'scheduled'
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        engagement_likes INTEGER DEFAULT 0,
        engagement_shares INTEGER DEFAULT 0,
        engagement_comments INTEGER DEFAULT 0,
        engagement_retweets INTEGER DEFAULT 0,
        external_id TEXT UNIQUE,  -- Twitter/LinkedIn post ID
        notes TEXT
    )
    ''')
    
    # Trending topics table - for analytics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trending_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        topic_title TEXT NOT NULL,
        topic_summary TEXT,
        source TEXT NOT NULL,  -- 'twitter', 'reddit', 'hackernews', 'news'
        engagement_score REAL,
        url TEXT,
        relevant_context TEXT,
        used_for_content INTEGER DEFAULT 0,  -- 1 if content was generated
        content_id INTEGER,
        FOREIGN KEY (content_id) REFERENCES posts(id)
    )
    ''')
    
    # Execution logs - workflow execution tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workflow_name TEXT,
        workflow_id TEXT,
        execution_id TEXT UNIQUE,
        status TEXT,  -- 'success', 'error', 'warning', 'partial'
        duration_seconds REAL,
        message TEXT,
        topics_collected INTEGER,
        content_generated INTEGER,
        content_posted INTEGER,
        errors_count INTEGER DEFAULT 0,
        metadata TEXT  -- JSON: {node_results, errors, stats}
    )
    ''')
    
    # Knowledge base stats - for RAG system
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT,  -- 'manual', 'imported', 'scraped'
        content_text TEXT NOT NULL,
        metadata TEXT,  -- JSON: {url, title, category, relevance_score}
        embedding_generated INTEGER DEFAULT 0,
        embeddings_file TEXT,
        usage_count INTEGER DEFAULT 0
    )
    ''')
    
    # API rate limit tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_rate_limits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_name TEXT UNIQUE,  -- 'twitter', 'reddit', 'hackernews'
        last_request TIMESTAMP,
        requests_today INTEGER DEFAULT 0,
        requests_limit INTEGER,
        reset_time TIMESTAMP,
        status TEXT DEFAULT 'ok'  -- 'ok', 'approaching_limit', 'rate_limited'
    )
    ''')
    
    # Error recovery log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS error_recovery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        error_type TEXT,
        error_message TEXT,
        node_name TEXT,
        recovery_action TEXT,
        recovery_successful INTEGER DEFAULT 0,
        notes TEXT
    )
    ''')
    
    # Performance metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metric_name TEXT,  -- 'generation_time', 'posting_time', 'api_latency'
        value REAL,
        unit TEXT,  -- 'seconds', 'ms', 'count'
        node_name TEXT,
        metadata TEXT
    )
    ''')
    
    conn.commit()
    
    # Create indices for faster queries
    print("[Init] Creating indices...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date_created)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics_source ON trending_topics(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_status ON execution_logs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_date ON execution_logs(timestamp)')
    
    conn.commit()
    conn.close()
    
    print(f"[Success] Database initialized with {7} tables and indices")

def insert_test_data(db_path=DATABASE_PATH):
    """Insert sample data for testing"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("[Test] Inserting sample data...")
    
    # Sample trend
    cursor.execute('''
    INSERT INTO trending_topics (topic_title, topic_summary, source, engagement_score, url)
    VALUES (?, ?, ?, ?, ?)
    ''', [
        'AI-Powered Automation',
        'Latest trends in AI and automation',
        'twitter',
        85.5,
        'https://twitter.com/search?q=ai'
    ])
    
    # Sample post
    cursor.execute('''
    INSERT INTO posts (platform, content, topic, status)
    VALUES (?, ?, ?, ?)
    ''', [
        'twitter',
        'Just automated my first workflow with n8n! #AI #Automation',
        'AI-Powered Automation',
        'draft'
    ])
    
    conn.commit()
    conn.close()
    
    print("[Test] Sample data inserted")

def get_stats(db_path=DATABASE_PATH):
    """Get database statistics"""
    if not os.path.exists(db_path):
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM posts')
    post_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM posts WHERE status = "posted"')
    posted_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trending_topics')
    topic_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM execution_logs')
    log_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    kb_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_posts": post_count,
        "posted_posts": posted_count,
        "draft_posts": post_count - posted_count,
        "trending_topics_tracked": topic_count,
        "execution_logs": log_count,
        "knowledge_base_items": kb_count
    }

def query_recent_posts(db_path=DATABASE_PATH, limit=5):
    """Get recent posts"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, platform, content, status, date_created
    FROM posts
    ORDER BY date_created DESC
    LIMIT ?
    ''', [limit])
    
    cols = [desc[0] for desc in cursor.description]
    results = [dict(zip(cols, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results

# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2 or sys.argv[1] == "init":
        init_database()
    elif sys.argv[1] == "test":
        init_database()
        insert_test_data()
    elif sys.argv[1] == "stats":
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    elif sys.argv[1] == "recent":
        posts = query_recent_posts()
        print(json.dumps(posts, indent=2, default=str))
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Usage: python init_database.py [init|test|stats|recent]")
