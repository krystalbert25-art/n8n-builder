#!/usr/bin/env node
/**
 * Post to LinkedIn using Puppeteer
 * Bypasses API restrictions by automating browser
 * Usage: node post_to_linkedin.js <content>
 * Example: node post_to_linkedin.js 'Just published a new article about AI!'
 */

const puppeteer = require('puppeteer');
require('dotenv').config();

const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function loginLinkedIn(page) {
  console.log('[Login] Navigating to LinkedIn...');
  await page.goto('https://www.linkedin.com/', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  // Check if already logged in
  const isLoggedIn = await page.$('[aria-label="Start a post"]') !== null;
  if (isLoggedIn) {
    console.log('[Login] Already logged in');
    return true;
  }

  console.log('[Login] Starting authentication...');
  
  // Navigate to login
  await page.goto('https://www.linkedin.com/login', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  // Email input
  console.log('[Login] Entering email...');
  await delay(500);
  
  const emailInput = await page.$('input[id="username"]');
  if (!emailInput) {
    throw new Error('Email input not found');
  }

  await emailInput.type(LINKEDIN_EMAIL, { delay: 50 });
  console.log('[Login] Email entered');

  // Password input
  console.log('[Login] Entering password...');
  const passwordInput = await page.$('input[id="password"]');
  if (!passwordInput) {
    throw new Error('Password input not found');
  }

  await passwordInput.type(LINKEDIN_PASSWORD, { delay: 50 });
  console.log('[Login] Password entered');

  // Sign in button
  await delay(500);
  const signInBtn = await page.$('button[type="submit"]');
  if (!signInBtn) {
    throw new Error('Sign in button not found');
  }

  await signInBtn.click();
  console.log('[Login] Clicked Sign In');

  // Wait for navigation
  try {
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 });
  } catch (e) {
    console.log('[Login] Navigation timeout...');
  }

  // Handle potential 2FA
  await delay(2000);
  const twoFAInput = await page.$('input[type="text"][maxlength="6"]');
  if (twoFAInput) {
    console.log('[Login] 2FA detected - waiting for manual entry (max 30 seconds)...');
    for (let i = 0; i < 30; i++) {
      const verifyBtn = await page.$('button:has-text("Verify")');
      if (verifyBtn) {
        console.log('[Login] 2FA verified');
        break;
      }
      await delay(1000);
    }
  }

  // Verify login
  await delay(2000);
  const feedPresent = await page.$('[aria-label="Start a post"]');
  if (feedPresent) {
    console.log('[Login] ✓ Successfully logged in');
    return true;
  } else {
    throw new Error('Login failed - Feed not found');
  }
}

async function postContent(page, content) {
  console.log(`[Post] Creating post: "${content.substring(0, 50)}..."`);

  // Click "Start a post" button
  const startPostBtn = await page.$('[aria-label="Start a post"]');
  if (!startPostBtn) {
    throw new Error('Start a post button not found');
  }

  await startPostBtn.click();
  await delay(1500);

  // Find text area in modal
  const textarea = await page.$('[role="textbox"][aria-label*="What"]') ||
                   await page.$('div[role="textbox"]');
  
  if (!textarea) {
    throw new Error('Text area not found');
  }

  // Type content
  await textarea.click();
  await delay(300);
  await textarea.type(content, { delay: 10 });
  console.log('[Post] Content entered');

  await delay(500);

  // Find post button
  const buttons = await page.$$('button');
  let posted = false;

  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText || el.textContent, btn);
    const ariaLabel = await page.evaluate(el => el.getAttribute('aria-label'), btn);

    if ((text && text.includes('Post')) || (ariaLabel && ariaLabel.includes('Post'))) {
      // Check if enabled
      const disabled = await page.evaluate(el => el.getAttribute('aria-disabled'), btn);
      if (disabled !== 'true') {
        await btn.click();
        posted = true;
        console.log('[Post] ✓ Posted');
        break;
      }
    }
  }

  if (!posted) {
    throw new Error('Post button not found or disabled');
  }

  // Wait for post to be published
  await delay(3000);
}

async function postLinkedIn(content, credentials) {
  if (!credentials.email || !credentials.password) {
    throw new Error('LinkedIn credentials missing (LINKEDIN_EMAIL, LINKEDIN_PASSWORD)');
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
    await loginLinkedIn(page);

    // Go to feed
    console.log('[Feed] Navigating to feed...');
    await page.goto('https://www.linkedin.com/feed/', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Post content
    await postContent(page, content);

    console.log('[Success] Post published!');
    return {
      success: true,
      content: content.substring(0, 100),
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('[Error]', error.message);
    return {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  } finally {
    await browser.close();
  }
}

// Main execution
async function main() {
  const content = process.argv[2];

  if (!content) {
    console.error('Error: No content provided');
    console.error('Usage: node post_to_linkedin.js "Your post content"');
    process.exit(1);
  }

  const result = await postLinkedIn(content, {
    email: LINKEDIN_EMAIL,
    password: LINKEDIN_PASSWORD
  });

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
