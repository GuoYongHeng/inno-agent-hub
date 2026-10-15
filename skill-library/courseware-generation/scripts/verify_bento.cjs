// 用 Edge/Chrome(CDP) 逐页截图校验课件：按 → 翻页，每页存一张 PNG
// 用法: node verify_bento.cjs "<课件.html>" "<截图输出目录>" [页数]
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');

// 浏览器自动探测（Windows Edge / Chrome 常见安装位），避免换机后路径失效
const CANDIDATES = [
  process.env.CHROME,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
].filter(Boolean);
const CHROME = CANDIDATES.find(p => { try { return fs.existsSync(p); } catch (e) { return false; } });
if (!CHROME) {
  console.error('未找到 Edge/Chrome。请设置环境变量 CHROME 指向浏览器 exe，例如：');
  console.error('  set CHROME=C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe');
  process.exit(1);
}

if (!process.argv[2] || !process.argv[3]) {
  console.error('用法: node verify_bento.cjs "<课件.html>" "<截图输出目录>" [页数，默认20]');
  process.exit(1);
}
const PORT = 9355;
const FILE = process.argv[2];
const OUT = process.argv[3];
const PAGE = 'file:///' + encodeURI(FILE);
const N = parseInt(process.argv[4] || '20', 10);
const sleep = ms => new Promise(r => setTimeout(r, ms));

fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const chrome = spawn(CHROME, [
    '--headless=new', '--remote-debugging-port=' + PORT, '--disable-gpu',
    '--no-first-run', '--no-sandbox',
    '--user-data-dir=' + path.join(os.tmpdir(), 'vs' + Date.now()),
    '--allow-file-access-from-files', '--window-size=1440,810', PAGE
  ], { stdio: ['ignore', 'pipe', 'pipe'] });

  let target = null;
  for (let i = 0; i < 80 && !target; i++) {
    await sleep(500);
    try {
      const l = await (await fetch('http://127.0.0.1:' + PORT + '/json/list')).json();
      target = l.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
    } catch (e) {}
  }
  if (!target) { console.log('无法连接 CDP'); chrome.kill(); process.exit(1); }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let id = 0; const pend = new Map();
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (method, params) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const js = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.result.value;

  await sleep(4000);
  const key = async k => {
    for (const type of ['rawKeyDown', 'char', 'keyUp']) {
      await send('Input.dispatchKeyEvent', { type, key: k, code: k, windowsVirtualKeyCode: k === 'ArrowRight' ? 39 : 37 });
    }
  };

  for (let i = 0; i < N; i++) {
    if (i > 0) { await key('ArrowRight'); await sleep(700); }
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(OUT, 'p' + (i + 1) + '.png'), Buffer.from(shot.result.data, 'base64'));
    process.stdout.write('P' + (i + 1) + ' ');
  }
  console.log('\n截图目录:', OUT);
  ws.close();
  chrome.kill();
  process.exit(0);
})();
