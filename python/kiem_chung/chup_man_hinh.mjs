// Chụp 5 màn hình của app DSS bằng Chrome headless (giao thức DevTools), độ phân giải 1440 x 1,5.
// Cách dùng: (1) chạy app: .venv/bin/python -m streamlit run python/app_dss.py  (cổng 8501)
// (2) mở Chrome: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9333 --user-data-dir=/tmp/chrome-prof about:blank &
// (3) node python/kiem_chung/chup_man_hinh.mjs  -> ảnh ra /tmp/shots/s1..s5.png (thư mục /tmp/shots phải có sẵn), chép vào results/doc/hinh_app/app_<ngày>_man_hinh_N.png (python/bao_cao/ve_hinh_dss.py đọc tên file này)
import fs from 'fs';
const port = 9333;
const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const page = list.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map();
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 300)); return r.result.result.value; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const W = 1440, DPR = 1.5;
const metrics = h => send('Emulation.setDeviceMetricsOverride', { width: W, height: h, deviceScaleFactor: DPR, mobile: false });
const click = async (x, y) => { for (const t of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type: t, x, y, button: 'left', clickCount: 1 }); };
const rectOf = async (js) => ev(`(()=>{const e=(${js}); if(!e) return null; e.scrollIntoView({block:'center'}); const r=e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
const nav = async (text) => { const r = await rectOf(`[...document.querySelectorAll('[data-testid=stSidebar] *')].filter(e=>e.innerText && e.innerText.replace(/\\s+/g,' ').trim()==='${text}').pop()`); if (!r) throw new Error('no nav ' + text); await click(r.x, r.y); await sleep(4500); };
const enter = async () => { for (const t of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type: t, key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: t === 'keyDown' ? '\r' : undefined }); };
const typeInto = async (findJs, text) => { const r = await rectOf(findJs); if (!r) throw new Error('no input'); await click(r.x, r.y); await ev(`(()=>{const e=document.activeElement; if(e&&e.select) e.select();})()`); await send('Input.insertText', { text }); await enter(); await sleep(3500); };
const shot = async (name) => {
  await metrics(3400); await sleep(2500);
  const h = await ev(`(()=>{const c=document.querySelector('[data-testid=stMainBlockContainer]')||document.body; const m=document.querySelector('[data-testid=stMain]'); const top=m?m.getBoundingClientRect().top:0; return Math.ceil(c.getBoundingClientRect().bottom + 24)})()`);
  const r = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: Math.min(h, 3400), scale: 1 }, captureBeyondViewport: false });
  fs.writeFileSync(`/tmp/shots/${name}.png`, Buffer.from(r.result.data, 'base64'));
  console.log(name, 'height', h);
  await metrics(1000); await sleep(1500);
};
await send('Page.enable'); await metrics(1000);
await send('Page.navigate', { url: 'http://localhost:8501' }); await sleep(7000);
await shot('s1');
await nav('02 Hồ sơ khách hàng');
await typeInto(`document.querySelector('[data-testid=stNumberInput] input')`, '26339');
await shot('s2');
await nav('03 Phân tích kịch bản'); await shot('s3');
await nav('04 Danh sách chăm sóc');
await typeInto(`[...document.querySelectorAll('input')].find(i=>(i.getAttribute('aria-label')||'').startsWith('Lý do'))`, 'Khách đã được liên hệ trực tiếp');
await typeInto(`[...document.querySelectorAll('input')].find(i=>(i.getAttribute('aria-label')||'').startsWith('Thêm'))`, '-26339');
await shot('s4');
await nav('05 Theo dõi mô hình'); await shot('s5');
ws.close(); process.exit(0);
