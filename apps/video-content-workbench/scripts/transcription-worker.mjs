import { spawn } from "node:child_process";
import { readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

const configPath = process.argv[2];
if (!configPath) process.exit(2);
const config = JSON.parse(await readFile(configPath, "utf8"));
const taskDirectory = path.dirname(configPath);
const markerPath = path.join(taskDirectory, "worker-status.json");

async function writeMarker(payload) {
  const temporary = `${markerPath}.${process.pid}.tmp`;
  await writeFile(temporary, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(temporary, markerPath);
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: config.projectRoot, windowsHide: true, env: { ...process.env, PYTHONUTF8: "1" } });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout = `${stdout}${chunk}`.slice(-12000); });
    child.stderr.on("data", (chunk) => { stderr = `${stderr}${chunk}`.slice(-12000); });
    child.on("error", reject);
    child.on("close", (code) => code === 0 ? resolve({ stdout, stderr }) : reject(new Error(stderr.trim() || stdout.trim() || `本地转写退出码：${code}`)));
  });
}

try {
  await writeMarker({ status: "running", startedAt: new Date().toISOString() });
  const python = process.platform === "win32" ? "py" : "python3";
  const pythonArgs = process.platform === "win32" ? ["-3", "-X", "utf8"] : ["-X", "utf8"];
  const result = await run(python, [...pythonArgs, path.join(config.projectRoot, "transcribe_local.py"), config.sourcePath, "--brand", config.brand, "--brand-url", config.brandUrl, "--output-dir", config.outputDir]);
  await writeMarker({ status: "completed", finishedAt: new Date().toISOString(), summary: result.stdout.trim().slice(-2000) });
} catch (error) {
  await writeMarker({ status: "failed", code: "TRANSCRIPTION_FAILED", message: error instanceof Error ? error.message.slice(-4000) : "本地转写失败", finishedAt: new Date().toISOString() });
  process.exitCode = 1;
}
