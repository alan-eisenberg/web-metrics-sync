const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

// Load URLs from config file
const configPath = path.join(__dirname, 'automation', 'data', 'links.json');
let urls = [];

try {
  const configData = fs.readFileSync(configPath, 'utf8');
  urls = JSON.parse(configData);
  console.log(`Loaded ${urls.length} URLs from ${configPath}`);
} catch (err) {
  console.error(`Error loading config from ${configPath}:`, err.message);
  process.exit(1);
}

const BATCH_SIZE = 5;
const WAIT_TIME = 30000; // 30 seconds

async function openBatch(batch, batchNumber, totalBatches) {
  console.log(`\n[Batch ${batchNumber}/${totalBatches}] Opening ${batch.length} URLs...`);
  
  const browsers = [];
  
  for (let i = 0; i < batch.length; i++) {
    const url = batch[i];
    console.log(`  [${i + 1}/${batch.length}] Opening: ${url}`);
    
    try {
      const browser = await puppeteer.launch({
        headless: true, // HEADLESS MODE
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      
      browsers.push(browser);
    } catch (err) {
      console.log(`  Error opening ${url}: ${err.message}`);
    }
  }
  
  console.log(`[Batch ${batchNumber}] Waiting ${WAIT_TIME/1000} seconds...`);
  await new Promise(resolve => setTimeout(resolve, WAIT_TIME));
  
  console.log(`[Batch ${batchNumber}] Closing browsers...`);
  for (const browser of browsers) {
    try {
      await browser.close();
    } catch (err) {
      // Ignore close errors
    }
  }
  
  console.log(`[Batch ${batchNumber}] Done.`);
}

async function main() {
  const totalBatches = Math.ceil(urls.length / BATCH_SIZE);
  console.log(`Starting puppeteer batch opener (HEADLESS MODE)`);
  console.log(`Total URLs: ${urls.length}, Batch size: ${BATCH_SIZE}, Wait time: ${WAIT_TIME/1000}s`);
  console.log(`Total batches: ${totalBatches}`);
  
  for (let i = 0; i < urls.length; i += BATCH_SIZE) {
    const batch = urls.slice(i, i + BATCH_SIZE);
    const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
    await openBatch(batch, batchNumber, totalBatches);
  }
  
  console.log('\nAll batches completed!');
  process.exit(0);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
