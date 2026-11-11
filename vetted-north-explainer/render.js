// Renders the explainer to MP4: node render.js
// Needs playwright (Chromium) and ffmpeg. The body (4s-32s) is identical in every
// version, so it is rendered once and joined to each of the four openings.
const { chromium } = require("playwright");
const { spawn, execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const FPS = 30, HOOK_END = 4, END = 32;
const NAMES = ["master", "variation-1-gamble", "variation-2-who-do-you-call", "variation-3-four-checks"];
const out = path.join(__dirname, "out");
const tmp = path.join(out, ".parts");
const page_url = v => "file://" + path.join(__dirname, "index.html") + "?v=" + v;

async function segment(browser, v, from, to, file) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(page_url(v));
  await page.evaluate(() => document.fonts.ready);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-g", String(FPS), file],
    { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Promise((ok, fail) => ff.on("close", c => (c ? fail(new Error("ffmpeg " + c)) : ok())));
  for (let f = Math.round(from * FPS); f < Math.round(to * FPS); f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const png = await page.screenshot({ type: "png" });
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await done;
  await page.close();
}

(async () => {
  fs.mkdirSync(tmp, { recursive: true });
  const browser = await chromium.launch();
  const body = path.join(tmp, "body.mp4");
  await segment(browser, 0, HOOK_END, END, body);
  for (let v = 0; v < NAMES.length; v++) {
    const hook = path.join(tmp, `hook${v}.mp4`);
    await segment(browser, v, 0, HOOK_END, hook);
    const list = path.join(tmp, `list${v}.txt`);
    fs.writeFileSync(list, `file '${hook}'\nfile '${body}'\n`);
    const file = path.join(out, `vetted-north-explainer-${NAMES[v]}.mp4`);
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list,
      "-c", "copy", "-movflags", "+faststart", file]);
    console.log("wrote", file);
  }
  await browser.close();
  fs.rmSync(tmp, { recursive: true });
})();
