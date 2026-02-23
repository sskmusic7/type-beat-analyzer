/**
 * Playwright E2E tests for Type Beat Analyzer
 * Tests audio upload and analysis flow
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';
const TEST_TRACKS_DIR = path.join(__dirname, '..', 'ref docs', 'tstt tracks]');

// Get all test tracks
function getTestTracks() {
  const tracksDir = TEST_TRACKS_DIR;
  if (!fs.existsSync(tracksDir)) {
    console.warn(`Test tracks directory not found: ${tracksDir}`);
    return [];
  }
  
  const files = fs.readdirSync(tracksDir)
    .filter(file => file.endsWith('.mp3'))
    .map(file => ({
      name: file,
      path: path.join(tracksDir, file)
    }));
  
  return files;
}

test.describe('Type Beat Analyzer - Audio Analysis', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for backend to be ready
    try {
      const response = await fetch(`${BACKEND_URL}/`);
      if (!response.ok) {
        throw new Error('Backend not ready');
      }
    } catch (error) {
      test.skip(true, 'Backend is not running. Start it with: ./scripts/start_test_environment.sh');
    }
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
  });

  test('should load the homepage', async ({ page }) => {
    // Check for main heading
    await expect(page.locator('text=Know Your Sound')).toBeVisible();
    
    // Check for upload area
    await expect(page.locator('text=Upload Your Beat')).toBeVisible();
    
    // Check for stats
    await expect(page.locator('text=697')).toBeVisible(); // Trained Fingerprints
    await expect(page.locator('text=74')).toBeVisible(); // Artists
  });

  test('should display upload area', async ({ page }) => {
    const uploadText = page.locator('text=Drag & drop your beat here');
    await expect(uploadText).toBeVisible();
    
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
  });

  // Test each track
  const testTracks = getTestTracks();
  
  if (testTracks.length > 0) {
    for (const track of testTracks) {
      test(`should analyze track: ${track.name}`, async ({ page }) => {
        // Wait for upload area
        await page.waitForSelector('input[type="file"]', { state: 'visible' });
        
        // Upload file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(track.path);
        
        // Wait for loading state
        await expect(page.locator('text=Analyzing your beat...')).toBeVisible({ timeout: 10000 });
        
        // Wait for results (or no matches message)
        // Results should appear within 60 seconds for large files
        const resultsSection = page.locator('text=Analysis Results').or(page.locator('text=No matches found'));
        await resultsSection.waitFor({ timeout: 60000 });
        
        // Check if we got results or a no matches message
        const hasResults = await page.locator('text=Analysis Results').isVisible().catch(() => false);
        const hasNoMatches = await page.locator('text=No matches found').isVisible().catch(() => false);
        
        // Either results or no matches is acceptable
        expect(hasResults || hasNoMatches).toBeTruthy();
        
        // If results exist, check they're formatted correctly
        if (hasResults) {
          // Check for at least one match
          const matchCards = page.locator('[class*="bg-slate"]').filter({ hasText: /% match/ });
          const matchCount = await matchCards.count();
          
          console.log(`Track "${track.name}": Found ${matchCount} match(es)`);
          
          if (matchCount > 0) {
            // Check first match has artist name and confidence
            const firstMatch = matchCards.first();
            await expect(firstMatch.locator('text=/\\d+% match/')).toBeVisible();
          }
        } else {
          console.log(`Track "${track.name}": No matches found`);
        }
      });
    }
  } else {
    test('skip - no test tracks found', async () => {
      test.skip(true, 'No test tracks found in test directory');
    });
  }

  test('should handle invalid file upload gracefully', async ({ page }) => {
    // Create a dummy text file
    const dummyFile = path.join(__dirname, 'dummy.txt');
    fs.writeFileSync(dummyFile, 'This is not an audio file');
    
    try {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(dummyFile);
      
      // Should show error
      await expect(page.locator('text=/error|failed/i')).toBeVisible({ timeout: 10000 });
    } finally {
      // Cleanup
      if (fs.existsSync(dummyFile)) {
        fs.unlinkSync(dummyFile);
      }
    }
  });

  test('should display trending artists section', async ({ page }) => {
    // Scroll to trending section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Check for trending section
    await expect(page.locator('text=Top Artists This Week')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('API Health Checks', () => {
  test('backend health check', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  test('trending artists endpoint', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/trending?limit=10`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });
});
