// Full-page, high-res capture using a FRESH throwaway profile (non-default => CDP allowed).
// Flow: capture login pages (logged out) -> wait for YOU to log in -> capture all data pages.
// You type your own credentials in the opened window; this script never handles them.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const PROFILE = path.join(__dirname, '_autoprofile');
const OUT = path.join(__dirname, 'captures');
fs.mkdirSync(OUT, { recursive: true });

const B = 'https://app.gts.sa';
const LOGIN_PAGES = [
  ['login_main', B + '/Account/Login'],
  ['login_temp', 'https://app.gts.sa:446/'],
];
const PAGES = [
  ['dash',          B + '/'],
  ['myprofile',     B + '/employee/MyProfile'],
  ['attendance',    B + '/Employee/Attendance'],
  ['joinreports',   B + '/Employee/JoinReports'],
  ['payment',       B + '/employee/paymentrequests'],
  ['payroll',       B + '/Employee/Payroll'],
  ['overtime',      B + '/Employee/Overtime'],
  ['pettycash',     B + '/employee/mypettycash'],
  ['businesstrips', B + '/Employee/BusinessTripRequests'],
  ['tdy',           B + '/employee/tdys'],
  ['leave',         B + '/Employee/EmployeeLeaveRequests'],
  ['vacations',     B + '/Employee/EmployeeVacations'],
  ['airtickets',    B + '/Employee/AirTickets'],
  ['exit',          B + '/Employee/ExitReentries'],
  ['insurance',     B + '/Employee/InsuranceRequests'],
  ['support',       B + '/Employee/Tickets'],
  ['statistics',    B + '/Employee/Statistics'],
  ['performance',   B + '/Employee/MyPerformanceReviews'],
  ['temp_dash',     'https://app.gts.sa:446/'],
];

const report = [];

async function settle(page) {
  try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch {}
  await page.waitForTimeout(3200);
  await page.addStyleTag({ content: '*{transition:none!important;animation:none!important}' }).catch(()=>{});
  await page.waitForTimeout(300);
}
async function shoot(page, key, full = true) {
  const f = path.join(OUT, key + '.png');
  await page.screenshot({ path: f, fullPage: full });
  const h = await page.evaluate(() => document.documentElement.scrollHeight).catch(()=>0);
  report.push({ key, url: page.url(), scrollH: h });
  console.log(`  OK ${key.padEnd(14)} h=${h}px  -> ${key}.png`);
}
async function isLoggedIn(page) {
  return await page.evaluate(() => /Hello,|Dashboard/i.test(document.body.innerText) && !/Welcome Back|Account\/Login/i.test(document.body.innerText+location.href)).catch(()=>false);
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    channel: 'chrome',
    headless: false,
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    ignoreHTTPSErrors: true,
    args: ['--start-maximized'],
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });

  // 1) LOGIN PAGES (logged out) -----------------------------------------
  console.log('== LOGIN PAGES ==');
  for (const [key, url] of LOGIN_PAGES) {
    try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 }); await settle(page); await shoot(page, key); }
    catch (e) { console.log(`  x ${key}: ${e.message}`); }
  }

  // 2) WAIT FOR MANUAL LOGIN ---------------------------------------------
  console.log('\n>>> ACTION NEEDED: log in as mofouad@gts.sa in the opened Chrome window. <<<');
  console.log('>>> Waiting up to 6 minutes for login... <<<');
  await page.goto(B + '/', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(()=>{});
  const deadline = Date.now() + 6 * 60 * 1000;
  let ok = false;
  while (Date.now() < deadline) {
    await page.waitForTimeout(3000);
    if (await isLoggedIn(page)) { ok = true; break; }
  }
  if (!ok) { console.log('LOGIN NOT DETECTED - aborting data capture.'); fs.writeFileSync(path.join(OUT,'_report.json'), JSON.stringify(report,null,2)); await ctx.close(); return; }
  console.log('Login detected. Capturing data pages...\n');

  // 3) DATA PAGES --------------------------------------------------------
  console.log('== DATA PAGES ==');
  for (const [key, url] of PAGES) {
    try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 }); await settle(page); await shoot(page, key); }
    catch (e) { console.log(`  x ${key}: ${e.message}`); report.push({ key, error: e.message }); }
  }

  fs.writeFileSync(path.join(OUT, '_report.json'), JSON.stringify(report, null, 2));
  await ctx.close();
  console.log('\nDONE. See captures/_report.json');
})();
