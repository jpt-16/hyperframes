// Captures cloverdownsdetailing.com for the egg reel. Nothing is submitted: the form is typed into, never sent.
const { chromium } = require('playwright');
const BASE = 'https://cloverdownsdetailing.com';
const ROUTE = async ctx => ctx.route('**/*', async route => {
  for (let k = 0; k < 4; k++) { try { await route.fulfill({ response: await route.fetch() }); return; } catch (e) { await new Promise(r => setTimeout(r, 500 * (k + 1))); } }
  await route.abort(); });
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY } });
  const open = async (opts, path) => {
    const ctx = await b.newContext({ ...opts, reducedMotion: 'reduce' }); await ROUTE(ctx); const p = await ctx.newPage();
    await p.goto(BASE + path, { waitUntil: 'networkidle', timeout: 60000 });
    await p.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });
    const h = await p.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < h; y += 400) { await p.evaluate(yy => window.scrollTo(0, yy), y); await sleep(90); }   // wake lazy images + reveals
    await p.evaluate(() => window.scrollTo(0, 0)); await sleep(1200);
    return [ctx, p];
  };
  const DESK = { viewport: { width: 1200, height: 732 }, deviceScaleFactor: 2 };
  const MOB = { viewport: { width: 390, height: 802 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };

  let [ctx, p] = await open(DESK, '/');
  await p.screenshot({ path: 'desk-hero.png' });
  // the quote form, being filled in (frames at 30 fps)
  const fy = await p.evaluate(() => { const r = document.querySelector('#q-name').closest('form').getBoundingClientRect(); return r.top + scrollY; });
  await p.evaluate(y => window.scrollTo(0, y), Math.max(0, fy - 150)); await sleep(1500);
  let f = 0; const snap = async () => p.screenshot({ path: `fr/form/${String(f++).padStart(3, '0')}.png` });
  await snap(); await snap();
  const typeIn = async (sel, text, per) => { await p.focus(sel); for (let i = 0; i < text.length; i += per) { await p.type(sel, text.slice(i, i + per)); await snap(); } };
  await typeIn('#q-name', 'Mike Russo', 3);
  await typeIn('#q-phone', '(978) 555-0199', 4);
  await typeIn('#q-town', 'Beverly', 4);
  await typeIn('#q-vehicle', '2021 Toyota RAV4', 4);
  const opts = await p.$$eval('#q-service option', os => os.map(o => o.value).filter(Boolean));
  if (opts.length) { await p.selectOption('#q-service', opts[0]); }
  await snap();
  const btn = p.locator('#quote button[type=submit], #quote button:has-text("FREE QUOTE")').first();
  await btn.hover(); await sleep(250);
  for (let k = 0; k < 6; k++) await snap();
  console.log('form frames', f, 'service', opts[0]);
  await ctx.close();

  // mobile home: a real scroll from the top (frames at 30 fps, eased)
  [ctx, p] = await open(MOB, '/');
  await p.screenshot({ path: 'mob-top.png' });
  const N = 26, DIST = 980;
  for (let i = 0; i < N; i++) {
    const u = i / (N - 1), e = u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
    await p.evaluate(y => window.scrollTo(0, y), Math.round(DIST * e)); await sleep(140);
    await p.screenshot({ path: `fr/mob/${String(i).padStart(3, '0')}.png` });
  }
  await ctx.close();

  // town pages, top of each
  for (const t of ['beverly', 'salem', 'danvers']) {
    [ctx, p] = await open(MOB, '/mobile-detailing/' + t); await p.screenshot({ path: `mob-${t}.png` }); await ctx.close();
  }
  await b.close();
})();
