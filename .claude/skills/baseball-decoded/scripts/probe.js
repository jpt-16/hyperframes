const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const [root, port, expr] = process.argv.slice(2);
const srv = http.createServer((q, r) => { let f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  const ty = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': ty }); r.end(d); }); }).listen(+port);
(async () => { const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }); const p = await b.newPage({ viewport: { width: 540, height: 960 } });
  p.on('pageerror', (e) => console.log('pageerror:', e.message.slice(0, 400)));
  await p.goto(`http://localhost:${port}/`); for (let i = 0; i < 240 && !(await p.evaluate(() => !!window.__dbg)); i++) await p.waitForTimeout(500);
  console.log(JSON.stringify(await p.evaluate(expr), null, 0)); await b.close(); srv.close(); })();
