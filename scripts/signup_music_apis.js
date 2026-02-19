#!/usr/bin/env node
/**
 * Automated signup for music database APIs using Playwright
 * Pauses at email verification steps for manual completion
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const EMAIL = 'sospecial07@hotmail.com';
const PASSWORD = 'SSKMUSICBABY';
const ENV_FILE = path.join(__dirname, '..', 'backend', '.env');

async function waitForUser(message) {
  console.log(`\n⏸️  ${message}`);
  console.log('   Press Enter when ready to continue...');
  return new Promise(resolve => {
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    rl.question('', () => {
      rl.close();
      resolve();
    });
  });
}

async function updateEnvFile(key, value) {
  let envContent = '';
  if (fs.existsSync(ENV_FILE)) {
    envContent = fs.readFileSync(ENV_FILE, 'utf-8');
  }
  
  // Remove existing key if present
  envContent = envContent.replace(new RegExp(`^${key}=.*$`, 'm'), '');
  
  // Add new key
  envContent += `\n${key}=${value}\n`;
  
  fs.writeFileSync(ENV_FILE, envContent);
  console.log(`✅ Added ${key} to .env file`);
}

async function signupAcoustID(page) {
  console.log('\n🎵 Signing up for AcoustID (MusicBrainz)...');
  console.log('   URL: https://acoustid.org/api-key');
  
  try {
    await page.goto('https://acoustid.org/api-key', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Look for email input
    const emailInput = await page.locator('input[type="email"], input[name*="email" i], input[id*="email" i]').first();
    if (await emailInput.count() > 0) {
      await emailInput.fill(EMAIL);
      console.log('   ✅ Filled email');
    }
    
    // Look for submit button
    const submitButton = await page.locator('button[type="submit"], input[type="submit"], button:has-text("Request"), button:has-text("Get"), button:has-text("Submit")').first();
    if (await submitButton.count() > 0) {
      await submitButton.click();
      console.log('   ✅ Clicked submit');
      await page.waitForTimeout(3000);
    }
    
    // Check for success message or API key display
    const pageContent = await page.content();
    if (pageContent.includes('API key') || pageContent.includes('api-key') || pageContent.includes('key')) {
      // Try to extract API key from page
      const keyMatch = pageContent.match(/([a-f0-9]{32,})/i);
      if (keyMatch) {
        const apiKey = keyMatch[1];
        await updateEnvFile('ACOUSTID_API_KEY', apiKey);
        console.log('   ✅ API key extracted and saved!');
        return apiKey;
      }
    }
    
    console.log('   ⏸️  Check your email for API key confirmation');
    await waitForUser('Have you received and clicked the email confirmation?');
    
    // After verification, try to get the key
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const content = await page.content();
    const keyMatch = content.match(/([a-f0-9]{32,})/i);
    if (keyMatch) {
      const apiKey = keyMatch[1];
      await updateEnvFile('ACOUSTID_API_KEY', apiKey);
      console.log('   ✅ API key extracted and saved!');
      return apiKey;
    }
    
    console.log('   ⚠️  Could not auto-extract API key. Please add manually to .env');
    await waitForUser('Please copy your API key from the page and we\'ll add it to .env');
    
    // User will paste it
    return null;
    
  } catch (error) {
    console.error('   ❌ Error:', error.message);
    return null;
  }
}

async function signupACRCloud(page) {
  console.log('\n🎵 Signing up for ACRCloud...');
  console.log('   URL: https://www.acrcloud.com');
  
  try {
    await page.goto('https://www.acrcloud.com', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Look for signup link
    const signupLink = await page.locator('a:has-text("Sign Up"), a:has-text("Signup"), a:has-text("Free Trial"), a:has-text("Register")').first();
    if (await signupLink.count() > 0) {
      await signupLink.click();
      await page.waitForTimeout(2000);
    }
    
    // Fill signup form
    const emailInput = await page.locator('input[type="email"], input[name*="email" i]').first();
    if (await emailInput.count() > 0) {
      await emailInput.fill(EMAIL);
      console.log('   ✅ Filled email');
    }
    
    const passwordInput = await page.locator('input[type="password"], input[name*="password" i]').first();
    if (await passwordInput.count() > 0) {
      await passwordInput.fill(PASSWORD);
      console.log('   ✅ Filled password');
    }
    
    // Look for additional fields
    const confirmPassword = await page.locator('input[name*="confirm" i], input[name*="repeat" i]').first();
    if (await confirmPassword.count() > 0) {
      await confirmPassword.fill(PASSWORD);
    }
    
    // Submit
    const submitButton = await page.locator('button[type="submit"], input[type="submit"], button:has-text("Sign Up"), button:has-text("Register")').first();
    if (await submitButton.count() > 0) {
      await submitButton.click();
      console.log('   ✅ Submitted form');
      await page.waitForTimeout(3000);
    }
    
    console.log('   ⏸️  Check your email for verification');
    await waitForUser('Have you verified your email?');
    
    // After verification, navigate to API keys page
    await page.goto('https://www.acrcloud.com/console/dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Look for API keys section
    const apiKeysLink = await page.locator('a:has-text("API"), a:has-text("Keys"), a:has-text("Credentials")').first();
    if (await apiKeysLink.count() > 0) {
      await apiKeysLink.click();
      await page.waitForTimeout(2000);
    }
    
    console.log('   ⏸️  Please copy Access Key and Access Secret from dashboard');
    await waitForUser('Ready to add API keys to .env?');
    
    return null;
    
  } catch (error) {
    console.error('   ❌ Error:', error.message);
    return null;
  }
}

async function signupAuddIO(page) {
  console.log('\n🎵 Signing up for Audd.io...');
  console.log('   URL: https://audd.io/');
  
  try {
    await page.goto('https://audd.io/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Look for signup
    const signupLink = await page.locator('a:has-text("Sign Up"), a:has-text("Get Started"), a:has-text("Register")').first();
    if (await signupLink.count() > 0) {
      await signupLink.click();
      await page.waitForTimeout(2000);
    }
    
    // Fill form
    const emailInput = await page.locator('input[type="email"], input[name*="email" i]').first();
    if (await emailInput.count() > 0) {
      await emailInput.fill(EMAIL);
      console.log('   ✅ Filled email');
    }
    
    const passwordInput = await page.locator('input[type="password"], input[name*="password" i]').first();
    if (await passwordInput.count() > 0) {
      await passwordInput.fill(PASSWORD);
      console.log('   ✅ Filled password');
    }
    
    // Submit
    const submitButton = await page.locator('button[type="submit"], input[type="submit"], button:has-text("Sign Up")').first();
    if (await submitButton.count() > 0) {
      await submitButton.click();
      console.log('   ✅ Submitted form');
      await page.waitForTimeout(3000);
    }
    
    console.log('   ⏸️  Check your email for verification');
    await waitForUser('Have you verified your email?');
    
    // Navigate to API page
    await page.goto('https://audd.io/dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log('   ⏸️  Please copy API Token from dashboard');
    await waitForUser('Ready to add API token to .env?');
    
    return null;
    
  } catch (error) {
    console.error('   ❌ Error:', error.message);
    return null;
  }
}

async function main() {
  console.log('\n🚀 Music Database API Signup Automation');
  console.log('========================================');
  console.log(`📧 Email: ${EMAIL}`);
  console.log('========================================\n');
  
  const browser = await chromium.launch({ 
    headless: false,  // Visible browser so you can verify
    slowMo: 500  // Slow down for visibility
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  try {
    // 1. AcoustID (most important)
    await signupAcoustID(page);
    
    // 2. ACRCloud (optional)
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    console.log('\n⏭️  Skip ACRCloud? (y/n)');
    const skipACR = await new Promise(resolve => {
      rl.question('', answer => {
        rl.close();
        resolve(answer.trim().toLowerCase() === 'y');
      });
    });
    
    if (!skipACR) {
      await signupACRCloud(page);
    }
    
    // 3. Audd.io (optional)
    const rl2 = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    console.log('\n⏭️  Skip Audd.io? (y/n)');
    const skipAudd = await new Promise(resolve => {
      rl2.question('', answer => {
        rl2.close();
        resolve(answer.trim().toLowerCase() === 'y');
      });
    });
    
    if (!skipAudd) {
      await signupAuddIO(page);
    }
    
    console.log('\n✅ Signup process complete!');
    console.log(`📄 API keys saved to: ${ENV_FILE}`);
    console.log('\n🔍 Review the .env file and add any missing keys manually if needed.');
    
  } catch (error) {
    console.error('\n❌ Error during signup:', error);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
