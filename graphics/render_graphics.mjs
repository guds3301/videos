// Render graphics specs to transparent clips for the CapCut timeline.
//
//   node render_graphics.mjs [--specs <dir>] [--out <dir>] [--format mov|webm] [--stills] [--only <id>]
//
// A spec is a JSON file: { "id": "...", "composition": "ChapterTitle|MeasureLine|ComponentDiagram",
//   "duration_frames": 96, "fps": 24, "props": { ... } }
// Output: <out>/<id>.mov (ProRes 4444 with alpha, default) or .webm (VP9 with alpha),
// plus <out>/manifest.json describing every clip. --stills also writes <id>.png (a mid-clip frame on
// the graphite background) for quick visual review without opening an editor.
//
// Set REMOTION_BROWSER_EXECUTABLE to use an installed Chrome/Chromium instead of letting Remotion
// download its own.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : fallback;
};
const flag = (name) => args.includes(`--${name}`);

const specsDir = path.resolve(opt('specs', path.join(here, 'specs')));
const outDir = path.resolve(opt('out', path.join(here, 'out')));
const format = opt('format', 'mov');
const only = opt('only', null);
const withStills = flag('stills');
const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE || undefined;

if (!['mov', 'webm'].includes(format)) {
  console.error(`--format must be mov or webm, got ${format}`);
  process.exit(2);
}
if (!fs.existsSync(specsDir)) {
  console.error(`specs folder not found: ${specsDir}`);
  process.exit(2);
}

const specFiles = fs.readdirSync(specsDir).filter((f) => f.endsWith('.json')).sort();
const specs = specFiles
  .map((f) => ({file: f, spec: JSON.parse(fs.readFileSync(path.join(specsDir, f), 'utf8'))}))
  .filter(({spec}) => !only || spec.id === only);
if (specs.length === 0) {
  console.error(`no specs to render in ${specsDir}${only ? ` matching id ${only}` : ''}`);
  process.exit(2);
}

const ids = new Set();
for (const {file, spec} of specs) {
  for (const key of ['id', 'composition', 'duration_frames']) {
    if (spec[key] === undefined) {
      console.error(`${file}: missing "${key}"`);
      process.exit(2);
    }
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(spec.id)) {
    console.error(`${file}: invalid id "${spec.id}"`);
    process.exit(2);
  }
  if (ids.has(spec.id)) {
    console.error(`${file}: duplicate id "${spec.id}"`);
    process.exit(2);
  }
  ids.add(spec.id);
  if (!Number.isInteger(spec.duration_frames) || spec.duration_frames < 1) {
    console.error(`${file}: duration_frames must be a positive integer`);
    process.exit(2);
  }
}

fs.mkdirSync(outDir, {recursive: true});
console.log(`Bundling (${specs.length} spec${specs.length === 1 ? '' : 's'})...`);
const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.js')});

const manifest = [];
for (const {spec} of specs) {
  const fps = spec.fps ?? 24;
  const inputProps = {...(spec.props ?? {}), duration_frames: spec.duration_frames, fps};
  const composition = await selectComposition({serveUrl, id: spec.composition, inputProps, browserExecutable});
  const outputLocation = path.join(outDir, `${spec.id}.${format}`);
  console.log(`Rendering ${spec.id} (${spec.composition}, ${spec.duration_frames} frames @ ${fps} fps)...`);

  const common = {composition, serveUrl, inputProps, outputLocation, browserExecutable, overwrite: true, logLevel: 'error'};
  if (format === 'mov') {
    await renderMedia({...common, codec: 'prores', proResProfile: '4444', pixelFormat: 'yuva444p10le', imageFormat: 'png', audioCodec: 'pcm-16'});
  } else {
    await renderMedia({...common, codec: 'vp9', pixelFormat: 'yuva420p', imageFormat: 'png'});
  }

  if (withStills) {
    await renderStill({
      composition,
      serveUrl,
      inputProps,
      browserExecutable,
      frame: Math.floor(spec.duration_frames / 2),
      output: path.join(outDir, `${spec.id}.png`),
      imageFormat: 'png',
      overwrite: true,
      logLevel: 'error',
    });
  }

  manifest.push({
    id: spec.id,
    composition: spec.composition,
    file: path.basename(outputLocation),
    format,
    alpha: true,
    duration_frames: spec.duration_frames,
    fps,
    width: composition.width,
    height: composition.height,
    props: spec.props ?? {},
    rendered_at: new Date().toISOString(),
  });
}

// Merge with an existing manifest so rendering one clip with --only never drops the others.
const manifestPath = path.join(outDir, 'manifest.json');
let existing = [];
if (fs.existsSync(manifestPath)) {
  try {
    existing = JSON.parse(fs.readFileSync(manifestPath, 'utf8')).clips ?? [];
  } catch {
    existing = [];
  }
}
const rendered = new Set(manifest.map((c) => c.id));
const merged = [...existing.filter((c) => !rendered.has(c.id)), ...manifest].sort((a, b) => a.id.localeCompare(b.id));
fs.writeFileSync(manifestPath, JSON.stringify({clips: merged}, null, 2));
console.log(`Done. ${manifest.length} clip(s) in ${outDir}`);
