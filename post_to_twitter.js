#!/usr/bin/env node
/**
 * Post tweets to Twitter using Puppeteer
 * Bypasses API paywall by automating browser
 * Usage: node post_to_twitter.js <tweets_json>
 * Example: node post_to_twitter.js '["Tweet 1", "Tweet 2"]'
 */

const puppeteer = require('puppeteer');
require('dotenv').config();

const TWITTER_EMAIL = process.env.TWITTER_EMAIL;
const TWITTER_PASSWORD = process.env.TWITTER_PASSWORD;

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function loginToTwitter(page) {
  console.log('[Login] Navigating to Twitter...');
  await page.goto('https://twitter.com/home', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  // Check if already logged in
  const isLoggedIn = await page.$('[aria-label="Compose"]') !== null;
  if (isLoggedIn) {
    console.log('[Login] Already logged in');
    return true;
  }

  console.log('[Login] Starting authentication...');
  
  // Click login button or navigate to login
  try {
    await page.goto('https://twitter.com/i/flow/login', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
  } catch (e) {
    console.error('[Login] Error navigating to login page:', e.message);
  }

  // Email/username field
  console.log('[Login] Entering email/username...');
  await delay(1000);
  
  let emailInput = await page.$('input[autocomplete="username"]');
  if (!emailInput) {
    emailInput = await page.$('input[type="text"]');
  }
  
  if (emailInput) {
    await emailInput.type(TWITTER_EMAIL, { delay: 50 });
    console.log('[Login] Email entered');
  } else {
    throw new Error('Email input not found');
  }

  // Find and click Next button
  await delay(500);
  let buttons = await page.$$('button');
  let nextClicked = false;
  
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText || el.textContent, btn);
    if (text && text.toLowerCase().includes('next')) {
      await btn.click();
      nextClicked = true;
      console.log('[Login] Clicked Next');
      break;
    }
  }

  if (!nextClicked) {
    throw new Error('Next button not found');
  }

  await delay(1000);

  // Password field
  console.log('[Login] Entering password...');
  const passwordInput = await page.$('input[type="password"]');
  if (passwordInput) {
    await passwordInput.type(TWITTER_PASSWORD, { delay: 50 });
    console.log('[Login] Password entered');
  } else {
    throw new Error('Password input not found');
  }

  // Find and click login button
  await delay(500);
  buttons = await page.$$('button');
  let loginClicked = false;
  
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText || el.textContent, btn);
    if (text && (text.toLowerCase().includes('login') || text.toLowerCase().includes('sign in'))) {
      await btn.click();
      loginClicked = true;
      console.log('[Login] Clicked Login');
      break;
    }
  }

  if (!loginClicked) {
    // Try submitting the form
    const form = await page.$('form');
    if (form) {
      await form.evaluate(f => f.submit());
      console.log('[Login] Form submitted');
    }
  }

  // Wait for navigation
  try {
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 });
  } catch (e) {
    console.log('[Login] Navigation timeout - checking if logged in...');
  }

  // Verify login
  await delay(2000);
  const composeBtn = await page.$('[aria-label="Compose"]');
  if (composeBtn) {
    console.log('[Login] ✓ Successfully logged in');
    return true;
  } else {
    throw new Error('Login failed - Compose button not found');
  }
}

async function postTweet(page, content, isReply = false) {
  console.log(`[Tweet] Posting: "${content.substring(0, 50)}..."`);

  // Click compose button
  let composeBtn = await page.$('[aria-label="Compose"]');
  if (!composeBtn) {
    throw new Error('Compose button not found');
  }

  await composeBtn.click();
  await delay(1500);

  // Find text area
  let textarea = await page.$('[data-testid="tweetTextarea_0"]');
  if (!textarea) {
    // Try alternate selector
    const textboxes = await page.$$('[role="textbox"]');
    if (textboxes.length > 0) {
      textarea = textboxes[0];
    }
  }

  if (!textarea) {
    throw new Error('Text area not found');
  }

  // Type tweet
  await textarea.click();
  await delay(300);
  await page.keyboard.type(content, { delay: 10 });
  await delay(500);

  // Find and click post button
  const buttons = await page.$$('button');
  let posted = false;

  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText || el.textContent, btn);
    const ariaLabel = await page.evaluate(el => el.getAttribute('aria-label'), btn);
    
    if ((text && text.toLowerCase().includes('post')) || 
        (ariaLabel && ariaLabel.toLowerCase().includes('post'))) {
      // Verify button is enabled
      const disabled = await page.evaluate(el => el.getAttribute('aria-disabled'), btn);
      if (disabled !== 'true') {
        await btn.click();
        posted = true;
        console.log('[Tweet] ✓ Posted');
        break;
      }
    }
  }

  if (!posted) {
    throw new Error('Post button not found or disabled');
  }

  // Wait for tweet to be posted
  await delay(2000);
}

async function postTwitterThread(tweets, credentials) {
  if (!Array.isArray(tweets)) {
    tweets = [tweets];
  }

  if (!credentials.email || !credentials.password) {
    throw new Error('Twitter credentials missing (TWITTER_EMAIL, TWITTER_PASSWORD)');
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--single-process=false',
      '--disable-dev-shm-usage'
    ]
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    // Set user agent
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    );

    // Login
    await loginToTwitter(page);

    // Post tweets
    for (let i = 0; i < tweets.length; i++) {
      try {
        await postTweet(page, tweets[i], i > 0);
        
        // Delay between tweets in thread
        if (i < tweets.length - 1) {
          console.log(`[Thread] Waiting before next tweet...`);
          await delay(3000);
        }
      } catch (error) {
        console.error(`[Error] Tweet ${i + 1} failed:`, error.message);
        throw new Error(`Failed to post tweet ${i + 1}: ${error.message}`);
      }
    }

    console.log(`[Success] All ${tweets.length} tweets posted!`);
    return {
      success: true,
      tweetsPosted: tweets.length,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('[Error]', error.message);
    return {
      success: false,
      tweetsPosted: 0,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  } finally {
    await browser.close();
  }
}

// Main execution
async function main() {
  const tweetsArg = process.argv[2];

  if (!tweetsArg) {
    console.error('Error: No tweets provided');
    console.error('Usage: node post_to_twitter.js \'["Tweet 1", "Tweet 2"]\' ');
    process.exit(1);
  }

  let tweets;
  try {
    tweets = JSON.parse(tweetsArg);
  } catch (e) {
    console.error('Error: Invalid JSON');
    process.exit(1);
  }

  const result = await postTwitterThread(tweets, {
    email: TWITTER_EMAIL,
    password: TWITTER_PASSWORD
  });

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
