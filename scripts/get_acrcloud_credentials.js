#!/usr/bin/env node
/**
 * Navigate ACRCloud console to locate and extract identification API credentials
 * (access_key and access_secret)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const ENV_FILE = path.join(__dirname, '..', 'backend', '.env');
const CONSOLE_URL = 'https://console.acrcloud.com/avr?region=eu-west-1#/dashboard';

function updateEnvFile(key, value) {
  let envContent = '';
  if (fs.existsSync(ENV_FILE)) {
    envContent = fs.readFileSync(ENV_FILE, 'utf-8');
  }
  
  // Remove existing key if present (including commented versions)
  envContent = envContent.replace(new RegExp(`^#?\\s*${key}=.*$`, 'gm'), '');
  
  // Add new key
  envContent += `\n${key}=${value}\n`;
  
  fs.writeFileSync(ENV_FILE, envContent);
  console.log(`✅ Saved ${key} to .env`);
}

function waitForUser(message) {
  console.log(`\n⏸️  ${message}`);
  console.log('   Press Enter when ready to continue...');
  return new Promise(resolve => {
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

async function extractCredentials(page) {
  console.log('\n🔍 Searching for ACRCloud identification API credentials...');
  console.log('   Looking for access_key and access_secret...\n');
  
  try {
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Get page content
    const content = await page.content();
    const pageText = await page.textContent('body');
    
    // Look for common patterns:
    // 1. access_key / access_secret in text
    // 2. API credentials in input fields
    // 3. Project settings or API keys section
    
    console.log('📋 Checking page for credential patterns...');
    
    // Pattern 1: Look for input fields with credential-like values
    const inputs = await page.locator('input[type="text"], input[type="password"], input[readonly]').all();
    console.log(`   Found ${inputs.length} input fields`);
    
    for (let i = 0; i < inputs.length; i++) {
      const input = inputs[i];
      const value = await input.inputValue();
      const placeholder = await input.getAttribute('placeholder') || '';
      const name = await input.getAttribute('name') || '';
      const id = await input.getAttribute('id') || '';
      
      // Check if it looks like a credential
      if (value && value.length > 10) {
        const label = placeholder || name || id || `input-${i}`;
        console.log(`   Found input: ${label.substring(0, 50)} = ${value.substring(0, 20)}...`);
        
        // Check if it matches access_key or access_secret patterns
        if (label.toLowerCase().includes('access_key') || 
            label.toLowerCase().includes('accesskey') ||
            id.toLowerCase().includes('access_key')) {
          updateEnvFile('ACRCLOUD_ACCESS_KEY', value);
        } else if (label.toLowerCase().includes('access_secret') || 
                   label.toLowerCase().includes('accesssecret') ||
                   id.toLowerCase().includes('access_secret')) {
          updateEnvFile('ACRCLOUD_ACCESS_SECRET', value);
        }
      }
    }
    
    // Pattern 2: Look for text content that might contain credentials
    // ACRCloud typically shows credentials in a format like:
    // "Access Key: xxxxxx" or "Access Secret: xxxxxx"
    const accessKeyMatch = pageText.match(/access[_\s]?key[:\s]+([a-zA-Z0-9]{20,})/i);
    const accessSecretMatch = pageText.match(/access[_\s]?secret[:\s]+([a-zA-Z0-9]{20,})/i);
    
    if (accessKeyMatch) {
      console.log('   ✅ Found access_key in page text');
      updateEnvFile('ACRCLOUD_ACCESS_KEY', accessKeyMatch[1]);
    }
    
    if (accessSecretMatch) {
      console.log('   ✅ Found access_secret in page text');
      updateEnvFile('ACRCLOUD_ACCESS_SECRET', accessSecretMatch[1]);
    }
    
    // Pattern 3: Look for code blocks or pre-formatted text
    const codeBlocks = await page.locator('code, pre, .code, .credential, .api-key').all();
    for (const block of codeBlocks) {
      const text = await block.textContent();
      if (text && text.length > 20 && text.length < 100) {
        console.log(`   Found code block: ${text.substring(0, 30)}...`);
      }
    }
    
    // Pattern 4: Check for common ACRCloud credential locations
    // Try clicking on "Projects", "API Keys", "Settings", "Credentials"
    const possibleLinks = [
      'Projects', 'Project', 'API', 'API Keys', 'Keys', 'Credentials',
      'Settings', 'Developer', 'Identification', 'AVR'
    ];
    
    for (const linkText of possibleLinks) {
      const link = page.locator(`a:has-text("${linkText}"), button:has-text("${linkText}")`).first();
      if (await link.count() > 0) {
        console.log(`   📍 Found navigation: ${linkText}`);
      }
    }
    
    // Check current URL to see where we are
    const currentUrl = page.url();
    console.log(`\n📍 Current URL: ${currentUrl}`);
    
    // If we're on dashboard, try to navigate to project settings
    if (currentUrl.includes('dashboard')) {
      console.log('\n🔍 On dashboard - looking for project/project settings...');
      
      // Try to find and click on a project or settings link
      const projectLink = page.locator('a:has-text("Project"), a:has-text("Settings"), a:has-text("API")').first();
      if (await projectLink.count() > 0) {
        console.log('   Clicking on project/settings link...');
        await projectLink.click();
        await page.waitForTimeout(2000);
        await extractCredentials(page); // Recursive search
      }
    }
    
    // Read current .env to see what we have
    const currentEnv = fs.existsSync(ENV_FILE) ? fs.readFileSync(ENV_FILE, 'utf-8') : '';
    const hasAccessKey = currentEnv.includes('ACRCLOUD_ACCESS_KEY=') && 
                         !currentEnv.match(/ACRCLOUD_ACCESS_KEY=\s*(your_|#)/);
    const hasAccessSecret = currentEnv.includes('ACRCLOUD_ACCESS_SECRET=') && 
                            !currentEnv.match(/ACRCLOUD_ACCESS_SECRET=\s*(your_|#)/);
    
    if (hasAccessKey && hasAccessSecret) {
      console.log('\n✅ Successfully extracted both credentials!');
      return true;
    } else {
      console.log('\n⚠️  Could not auto-extract credentials from page');
      console.log('   You may need to manually copy them from the console');
      return false;
    }
    
  } catch (error) {
    console.error('   ❌ Error extracting credentials:', error.message);
    return false;
  }
}

async function main() {
  console.log('\n🔍 ACRCloud Credential Extractor');
  console.log('================================');
  console.log('This script will help you locate access_key and access_secret');
  console.log('for the ACRCloud Identification API.\n');
  
  const browser = await chromium.launch({ 
    headless: false,  // Visible browser
    slowMo: 300
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  try {
    // Navigate to ACRCloud console
    console.log(`\n🌐 Navigating to ACRCloud console...`);
    console.log(`   URL: ${CONSOLE_URL}`);
    await page.goto(CONSOLE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // Check if we need to login
    const loginIndicators = await page.locator('input[type="email"], input[type="password"], button:has-text("Sign"), button:has-text("Log")').count();
    if (loginIndicators > 0) {
      console.log('\n⚠️  Login required');
      await waitForUser('Please log in to ACRCloud console, then press Enter');
      await page.waitForTimeout(2000);
    }
    
    // Try to extract credentials
    const success = await extractCredentials(page);
    
    if (!success) {
      console.log('\n📝 Manual extraction guide:');
      console.log('   1. Look for "Projects" or "AVR" in the sidebar');
      console.log('   2. Click on your project');
      console.log('   3. Look for "API Keys", "Credentials", or "Settings"');
      console.log('   4. Find "Access Key" and "Access Secret"');
      console.log('   5. Copy them and we\'ll add to .env\n');
      
      await waitForUser('Navigate to the credentials page, then press Enter');
      
      // Try again after user navigation
      await extractCredentials(page);
      
      // Ask user to paste if still not found
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });
      
      console.log('\n📋 If credentials are visible on screen:');
      console.log('   Paste your Access Key (or press Enter to skip):');
      const accessKey = await new Promise(resolve => {
        rl.question('   > ', answer => resolve(answer.trim()));
      });
      
      if (accessKey) {
        updateEnvFile('ACRCLOUD_ACCESS_KEY', accessKey);
      }
      
      console.log('   Paste your Access Secret (or press Enter to skip):');
      const accessSecret = await new Promise(resolve => {
        rl.question('   > ', answer => resolve(answer.trim()));
      });
      
      if (accessSecret) {
        updateEnvFile('ACRCLOUD_ACCESS_SECRET', accessSecret);
      }
      
      rl.close();
    }
    
    // Verify final state
    const finalEnv = fs.existsSync(ENV_FILE) ? fs.readFileSync(ENV_FILE, 'utf-8') : '';
    const hasKey = finalEnv.match(/ACRCLOUD_ACCESS_KEY=\s*[a-zA-Z0-9]{10,}/);
    const hasSecret = finalEnv.match(/ACRCLOUD_ACCESS_SECRET=\s*[a-zA-Z0-9]{10,}/);
    
    console.log('\n📊 Final Status:');
    console.log(`   Access Key: ${hasKey ? '✅ Found' : '❌ Missing'}`);
    console.log(`   Access Secret: ${hasSecret ? '✅ Found' : '❌ Missing'}`);
    
    if (hasKey && hasSecret) {
      console.log('\n✅ All ACRCloud credentials are now configured!');
      console.log('   The identification API should be ready to use.');
    } else {
      console.log('\n⚠️  Some credentials are still missing.');
      console.log('   Check the ACRCloud console dashboard for your project credentials.');
    }
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.log('\n💡 Tip: Make sure you\'re logged into ACRCloud console');
    console.log('   and have a project created with Identification API enabled.');
  } finally {
    console.log('\n⏸️  Browser will stay open for 10 seconds so you can verify...');
    await page.waitForTimeout(10000);
    await browser.close();
  }
}

main().catch(console.error);
