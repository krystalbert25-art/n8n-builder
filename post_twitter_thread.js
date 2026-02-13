const puppeteer = require('puppeteer');

// Usage: provide env vars TWITTER_EMAIL, TWITTER_PASSWORD, TWEET1, TWEET2, TWEET3
// Note: This is a basic script. If your account uses 2FA, Puppeteer needs session cookies or interactive handling.

(async () => {
  const email = process.env.TWITTER_EMAIL;
  const password = process.env.TWITTER_PASSWORD;
  const tweets = [process.env.TWEET1 || '', process.env.TWEET2 || '', process.env.TWEET3 || ''].filter(t => t);

  if (!email || !password || tweets.length === 0) {
    console.error(JSON.stringify({ success: false, error: 'Missing env vars (TWITTER_EMAIL/TWITTER_PASSWORD/TWEET1..3)' }));
    process.exit(2);
  }

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 800 });

    // Go to login
    await page.goto('https://twitter.com/i/flow/login', { waitUntil: 'networkidle2' });

    // Wait and fill email
    await page.waitForTimeout(1000);

    // The login flow may vary; try common selectors
    try {
      await page.waitForSelector('input[name="text"]', { timeout: 5000 });
      await page.type('input[name="text"]', email, { delay: 50 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    } catch (err) {
      // fallback to other selector
    }

    // Password field
    await page.waitForSelector('input[name="password"]', { timeout: 10000 });
    await page.type('input[name="password"]', password, { delay: 50 });
    await page.keyboard.press('Enter');

    // Wait for home page
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 });
    await page.waitForTimeout(2000);

    // Post first tweet
    let firstTweetId = null;
    for (let i = 0; i < tweets.length; i++) {
      const text = tweets[i];
      // Click tweet button or composer
      // New Twitter UI uses a "div[aria-label='Tweet text']" editor inside modal
      try {
        // Open composer
        await page.waitForTimeout(500);
        const composer = await page.$("div[aria-label='Tweet text']");
        if (!composer) {
          // Try to click Tweet button
          const shareBtn = await page.$x("//a[@href='/compose/tweet'] | //div[@role='button' and contains(., 'Tweet')]");
          if (shareBtn && shareBtn.length) await shareBtn[0].click();
          await page.waitForTimeout(1000);
        }

        const editable = await page.waitForSelector("div[aria-label='Tweet text']", { timeout: 5000 });
        await editable.focus();
        await page.keyboard.type(text, { delay: 20 });

        // Click Tweet button inside composer
        const tweetBtn = await page.$x("//div[@role='button' and .//span[text()='Tweet']]");
        if (tweetBtn && tweetBtn.length) {
          await tweetBtn[0].click();
        } else {
          // fallback: press Ctrl+Enter
          await page.keyboard.down('Control');
          await page.keyboard.press('Enter');
          await page.keyboard.up('Control');
        }

        // wait for the tweet to post
        await page.waitForTimeout(3000);

        // Get last tweet URL by visiting profile
        await page.goto(`https://twitter.com/${encodeURIComponent((await page.evaluate(() => window.__INITIAL_STATE__?.user?.screen_name) || ''))}`, { waitUntil: 'networkidle2' }).catch(()=>{});
        // Instead of profile scraping, we can get last tweet via timeline
        // Simpler: after posting, search for status URL in DOM
        // Wait a bit and then attempt to extract latest tweet id
        await page.waitForTimeout(2000);

      } catch (err) {
        console.error('posting error', err.toString());
        await browser.close();
        console.log(JSON.stringify({ success: false, error: err.toString() }));
        process.exit(3);
      }

      // For replies (threading) we rely on posting in sequence; Twitter usually threads if reply metadata set, but via UI we must open reply box and post
      if (i < tweets.length - 1) {
        // open reply on last tweet posted: navigate to profile and click reply on the first found tweet
        // This is fragile; for reliability, open the newly posted tweet by searching for 'aria-label' and click reply
        await page.waitForTimeout(1500);
        // Navigate to home and click first tweet to open detail
        await page.goto('https://twitter.com/home', { waitUntil: 'networkidle2' });
        await page.waitForTimeout(1500);

        // Try to find the first tweet in timeline and click reply
        try {
          const firstTimelineTweet = await page.$("article div[data-testid='tweet']");
          if (firstTimelineTweet) {
            // Click reply button within tweet
            const replyBtn = await firstTimelineTweet.$("div[data-testid='reply']");
            if (replyBtn) await replyBtn.click();
            await page.waitForTimeout(800);
            const replyEditor = await page.waitForSelector("div[aria-label='Tweet text']", { timeout: 5000 });
            await replyEditor.focus();
            await page.keyboard.type(tweets[i+1], { delay: 20 });
            const replyTweetBtn = await page.$x("//div[@role='button' and .//span[text()='Reply']]");
            if (replyTweetBtn && replyTweetBtn.length) {
              await replyTweetBtn[0].click();
              await page.waitForTimeout(2000);
            }
            i++; // we posted the next tweet as reply
          }
        } catch (err) {
          // If reply failed, continue posting as normal
        }
      }
    }

    // Return success
    await browser.close();
    console.log(JSON.stringify({ success: true, message: 'Tweets posted (UI method)' }));
    process.exit(0);
  } catch (err) {
    await browser.close();
    console.error(JSON.stringify({ success: false, error: err.toString() }));
    process.exit(4);
  }
})();
