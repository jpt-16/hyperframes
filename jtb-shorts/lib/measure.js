// Measure elements inside device viewports, in the page's own pixels (unscaled, unscrolled).
//   node lib/measure.js page.html '["id1","id2"]'   ->   {"id1": {"x":..,"y":..,"w":..,"h":..}, ...}
// The page is loaded with its timeline script disabled, so nothing is mid-animation, and only after
// web fonts are ready, so text wraps exactly as it will in the render.
const { chromium } = require('playwright');
(async () => {
  const [file, idsJson] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + file);
  await page.evaluate(() => document.fonts.ready);
  const out = await page.evaluate((ids) => {
    const res = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) { res[id] = null; continue; }
      const vp = el.closest('.vp');
      const r = el.getBoundingClientRect();
      if (!vp) { res[id] = { x: r.left, y: r.top, w: r.width, h: r.height, canvas: true }; continue; }
      const v = vp.getBoundingClientRect(), s = v.width / vp.offsetWidth;
      res[id] = { x: (r.left - v.left) / s, y: (r.top - v.top) / s, w: r.width / s, h: r.height / s };
    }
    return res;
  }, JSON.parse(idsJson));
  console.log(JSON.stringify(out));
  await browser.close();
})();
