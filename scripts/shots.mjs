// 검증용 실시간 스크린샷: Chrome DevTools Protocol로 슬라이드마다 실제 시간만큼 기다린 뒤 캡처
// 사용법: node scripts/shots.mjs [--mobile] [--wait=4500] [--url=https://...] [슬라이드번호 ...]
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const BASE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const args = process.argv.slice(2);
const mobile = args.includes("--mobile");
const wait = Number((args.find(a => a.startsWith("--wait=")) || "--wait=4500").split("=")[1]);
const urlArg = args.find(a => a.startsWith("--url="));
const URL = urlArg ? urlArg.slice(6) : pathToFileURL(resolve(BASE, "index.html")).href;
const evalArg = args.find(a => a.startsWith("--eval="));
const nums = args.filter(a => /^\d+$/.test(a)).map(Number);
const slides = nums.length ? nums : Array.from({ length: 14 }, (_, i) => i + 1);
const [W, H, tag] = mobile ? [390, 844, "m"] : [1600, 900, "s"];
const OUT = resolve(BASE, "build", "screens");
mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--window-size=${W},${H}`,
  "--hide-scrollbars", "--mute-audio", "--autoplay-policy=no-user-gesture-required",
  `--user-data-dir=${resolve(BASE, "build", "cdp-profile-" + port)}`, "about:blank"], { stdio: "ignore" });

let ws;
for (let i = 0; i < 40 && !ws; i++) {
  await sleep(250);
  try {
    const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
    const page = list.find(t => t.type === "page");
    if (page) ws = new WebSocket(page.webSocketDebuggerUrl);
  } catch {}
}
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
const consoleErrors = [];
ws.addEventListener("message", ev => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  if (msg.method === "Runtime.exceptionThrown") consoleErrors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
  if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") consoleErrors.push(msg.params.entry.text + " " + (msg.params.entry.url || ""));
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });

await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile });
const reduced = args.includes("--reduced");
await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: reduced ? "reduce" : "no-preference" }] });
for (const n of slides) {
  await send("Page.navigate", { url: "about:blank" });
  await sleep(150);
  await send("Page.navigate", { url: `${URL}#${n}` });
  await sleep(wait);
  if (evalArg) {
    const r = await send("Runtime.evaluate", { expression: evalArg.slice(7), returnByValue: true });
    console.log(`#${n} eval:`, JSON.stringify(r.result.result?.value ?? r.result.exceptionDetails?.text));
  }
  const { result } = await send("Page.captureScreenshot", { format: "png" });
  const file = resolve(OUT, `${tag}${String(n).padStart(2, "0")}.png`);
  writeFileSync(file, Buffer.from(result.data, "base64"));
  console.log("saved", file.split(/[\\/]/).pop());
}
console.log(consoleErrors.length ? "CONSOLE ERRORS:\n" + [...new Set(consoleErrors)].join("\n") : "console: no errors");
ws.close(); chrome.kill();
process.exit(0);
