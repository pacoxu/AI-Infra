#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');
const dataPath = path.join(repoRoot, 'diagrams', 'ai-infra-landscape.data.json');
const outPath = path.join(repoRoot, 'diagrams', 'ai-infra-landscape.svg');

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const logoCache = new Map();

const canvas = { width: 1800, height: 1150 };
const chart = { x: 110, y: 130, width: 1420, height: 900 };
const notesX = chart.x + chart.width + 30;
const notesWidth = 220;

function escapeXml(input) {
  return String(input)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function toX(value) {
  return chart.x + (value / 100) * chart.width;
}

function toY(value) {
  return chart.y + ((100 - value) / 100) * chart.height;
}

function textWidth(name) {
  return Math.max(88, Math.round([...name].length * 7.4));
}

function hasTag(entity, tag) {
  return Array.isArray(entity?.tags) && entity.tags.includes(tag);
}

function cardDimensions(project) {
  const baseWidth = Math.max(148, 58 + textWidth(project.name));
  const tagExtra = hasTag(project, 'k8s-feature') ? 44 : 0;
  return {
    width: baseWidth + tagExtra,
    height: 34
  };
}

function clamp(num, min, max) {
  return Math.min(max, Math.max(min, num));
}

function logoText(name, manual) {
  if (manual) return manual;
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

function sanitizeId(input) {
  const slug = String(input)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'item';
}

function detectLogoMime(buffer, logoPath) {
  if (
    buffer.length >= 8 &&
    buffer[0] === 0x89 &&
    buffer[1] === 0x50 &&
    buffer[2] === 0x4e &&
    buffer[3] === 0x47 &&
    buffer[4] === 0x0d &&
    buffer[5] === 0x0a &&
    buffer[6] === 0x1a &&
    buffer[7] === 0x0a
  ) {
    return 'image/png';
  }

  if (buffer.length >= 2 && buffer[0] === 0xff && buffer[1] === 0xd8) {
    return 'image/jpeg';
  }

  if (
    buffer.length >= 12 &&
    buffer.toString('ascii', 0, 4) === 'RIFF' &&
    buffer.toString('ascii', 8, 12) === 'WEBP'
  ) {
    return 'image/webp';
  }

  const sniff = buffer.subarray(0, 512).toString('utf8').trimStart();
  if (sniff.startsWith('<svg') || sniff.startsWith('<?xml') || sniff.includes('<svg')) {
    return 'image/svg+xml';
  }

  const ext = path.extname(logoPath).toLowerCase();
  if (ext === '.svg') return 'image/svg+xml';
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.webp') return 'image/webp';
  return 'image/png';
}

function logoHref(logoPath) {
  if (!logoPath) return null;
  if (logoCache.has(logoPath)) return logoCache.get(logoPath);

  const absolutePath = path.join(repoRoot, logoPath);
  if (!fs.existsSync(absolutePath)) {
    console.warn(`Missing logo file: ${logoPath}`);
    logoCache.set(logoPath, null);
    return null;
  }

  const buffer = fs.readFileSync(absolutePath);
  const mimeType = detectLogoMime(buffer, logoPath);
  const href = `data:${mimeType};base64,${buffer.toString('base64')}`;
  logoCache.set(logoPath, href);
  return href;
}

function badgeIconMarkup({ cx, cy, radius, stroke, fallbackText, fallbackClass, logoImage, clipId }) {
  const circleMarkup = `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${radius}" fill="white" stroke="${stroke}" />`;
  const href = logoHref(logoImage);

  if (!href) {
    return `${circleMarkup}
      <text x="${cx.toFixed(1)}" y="${(cy + 4.2).toFixed(1)}" text-anchor="middle" class="${fallbackClass}">${escapeXml(fallbackText)}</text>`;
  }

  const innerRadius = radius - 1.2;
  const imageSize = innerRadius * 2;
  const imageX = cx - innerRadius;
  const imageY = cy - innerRadius;
  return `${circleMarkup}
      <defs>
        <clipPath id="${clipId}">
          <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${innerRadius.toFixed(1)}" />
        </clipPath>
      </defs>
      <image x="${imageX.toFixed(1)}" y="${imageY.toFixed(1)}" width="${imageSize.toFixed(1)}" height="${imageSize.toFixed(1)}" href="${href}" preserveAspectRatio="xMidYMid meet" clip-path="url(#${clipId})" />`;
}

function wrapWords(text, maxChars) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';

  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length <= maxChars || current.length === 0) {
      current = next;
      continue;
    }
    lines.push(current);
    current = word;
  }
  if (current) lines.push(current);
  return lines.length ? lines : [text];
}

function projectNode(project, index) {
  const group = data.groups[project.group] || data.groups.kernel;
  const baseX = toX(project.x);
  const baseY = toY(project.y);
  const size = cardDimensions(project);

  const left = clamp(baseX - size.width / 2, chart.x + 8, chart.x + chart.width - size.width - 8);
  const top = clamp(baseY - size.height / 2, chart.y + 8, chart.y + chart.height - size.height - 8);
  const dashed = project.stage === 'early' ? ' project-early' : '';
  const k8sFeature = hasTag(project, 'k8s-feature');
  const bubble = logoText(project.name, project.logo);
  const iconCx = left + 18;
  const iconCy = top + size.height / 2;
  const clipId = `project-logo-${index}-${sanitizeId(project.name)}`;
  const iconMarkup = badgeIconMarkup({
    cx: iconCx,
    cy: iconCy,
    radius: 11.5,
    stroke: group.stroke,
    fallbackText: bubble,
    fallbackClass: 'logo',
    logoImage: project.logo_image,
    clipId
  });
  const k8sTagWidth = 34;
  const k8sTagHeight = 14;
  const k8sTagX = left + size.width - k8sTagWidth - 8;
  const k8sTagY = top + 3;
  const k8sTagMarkup = k8sFeature
    ? `
      <g class="project-tag-k8s">
        <rect x="${k8sTagX.toFixed(1)}" y="${k8sTagY.toFixed(1)}" width="${k8sTagWidth}" height="${k8sTagHeight}" rx="4" />
        <text x="${(k8sTagX + k8sTagWidth / 2).toFixed(1)}" y="${(k8sTagY + 10.2).toFixed(1)}" text-anchor="middle">K8s</text>
      </g>`
    : '';

  return `
    <g class="project${dashed}" data-name="${escapeXml(project.name)}">
      <rect x="${left.toFixed(1)}" y="${top.toFixed(1)}" width="${size.width}" height="${size.height}" rx="8" fill="${group.fill}" stroke="${group.stroke}" />
      ${iconMarkup}
      ${k8sTagMarkup}
      <text x="${(left + 36).toFixed(1)}" y="${(top + size.height / 2 + 5).toFixed(1)}" class="project-label">${escapeXml(project.name)}</text>
    </g>`;
}

function noteNode(note) {
  const group = data.groups[note.group] || data.groups.kernel;
  const y = toY(note.y);
  const lines = wrapWords(note.label, 20);
  const lineHeight = 16;
  const textStart = lines.length > 1 ? 20 : 28;
  const height = Math.max(44, 14 + lines.length * lineHeight);
  const lineMarkup = lines
    .map((line, index) => `<tspan x="14" y="${textStart + index * lineHeight}">${escapeXml(line)}</tspan>`)
    .join('');
  return `
    <g class="note" transform="translate(${notesX}, ${y - height / 2})">
      <rect x="0" y="0" width="${notesWidth}" height="${height}" rx="2" fill="${group.fill}" stroke="${group.stroke}" />
      <text class="note-label">${lineMarkup}</text>
    </g>`;
}

function ecosystemNode(item, index) {
  const group = data.groups[item.group] || data.groups.training;
  const x = toX(item.x);
  const y = 58;
  const width = Math.max(96, textWidth(item.name) + 34);
  const bubble = logoText(item.name, item.logo);
  const iconCx = 18;
  const iconCy = 17;
  const clipId = `ecosystem-logo-${index}-${sanitizeId(item.name)}`;
  const iconMarkup = badgeIconMarkup({
    cx: iconCx,
    cy: iconCy,
    radius: 8,
    stroke: group.stroke,
    fallbackText: bubble,
    fallbackClass: 'ecosystem-logo',
    logoImage: item.logo_image,
    clipId
  });

  return `
    <g class="ecosystem-item" transform="translate(${(x - width / 2).toFixed(1)}, ${y})">
      <rect x="0" y="0" width="${width}" height="34" rx="17" fill="${group.fill}" stroke="${group.stroke}" />
      ${iconMarkup}
      <text x="32" y="22" class="ecosystem-label">${escapeXml(item.name)}</text>
    </g>`;
}

const quadrantBackgrounds = [
  { x: chart.x, y: chart.y, width: chart.width / 2, height: chart.height / 2, fill: '#FBFCFF' },
  { x: chart.x + chart.width / 2, y: chart.y, width: chart.width / 2, height: chart.height / 2, fill: '#FAFDFF' },
  { x: chart.x, y: chart.y + chart.height / 2, width: chart.width / 2, height: chart.height / 2, fill: '#FCFCFD' },
  { x: chart.x + chart.width / 2, y: chart.y + chart.height / 2, width: chart.width / 2, height: chart.height / 2, fill: '#FBFCFE' }
];

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${canvas.width}" height="${canvas.height}" viewBox="0 0 ${canvas.width} ${canvas.height}" role="img" aria-labelledby="title desc">
  <title id="title">${escapeXml(data.meta.title)} (${escapeXml(data.meta.version)})</title>
  <desc id="desc">Four-quadrant AI infra landscape generated from data for easy maintenance.</desc>
  <defs>
    <style>
      .title { font: 700 42px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .subtitle { font: 500 19px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #4b5563; }
      .axis-label { font: 600 26px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #374151; }
      .quad-label { font: 600 16px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #6b7280; }
      .legend { font: 500 15px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #374151; }
      .project-label { font: 600 14px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .logo { font: 700 10px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #374151; }
      .project-tag-k8s rect { fill: #DBEAFE; stroke: #3B82F6; }
      .project-tag-k8s text { font: 700 9px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #1D4ED8; }
      .ecosystem-label { font: 600 13px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .ecosystem-logo { font: 700 8px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #374151; }
      .note-label { font: 600 15px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #1f2937; }
      .project-early rect,
      .project-early circle { stroke-dasharray: 4 4; }
      .footer { font: 500 13px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #6b7280; }
    </style>
  </defs>

  <rect x="0" y="0" width="${canvas.width}" height="${canvas.height}" fill="#f4f5f7" />

  <text x="${chart.x}" y="52" class="title">${escapeXml(data.meta.title)}</text>
  <text x="${chart.x}" y="82" class="subtitle">${escapeXml(data.meta.version)} | Last updated ${escapeXml(data.meta.last_updated)}</text>

  ${quadrantBackgrounds
    .map((q) => `<rect x="${q.x}" y="${q.y}" width="${q.width}" height="${q.height}" fill="${q.fill}" />`)
    .join('\n  ')}

  <rect x="${chart.x}" y="${chart.y}" width="${chart.width}" height="${chart.height}" fill="none" stroke="#1f2937" stroke-width="2" stroke-dasharray="6 5" />
  <line x1="${chart.x + chart.width / 2}" y1="${chart.y}" x2="${chart.x + chart.width / 2}" y2="${chart.y + chart.height}" stroke="#4b5563" stroke-width="2" stroke-dasharray="6 5" />
  <line x1="${chart.x}" y1="${chart.y + chart.height / 2}" x2="${chart.x + chart.width}" y2="${chart.y + chart.height / 2}" stroke="#4b5563" stroke-width="2" stroke-dasharray="6 5" />

  <text x="${chart.x + chart.width / 2}" y="${chart.y - 24}" text-anchor="middle" class="axis-label">${escapeXml(data.axes.y_top)}</text>
  <text x="${chart.x + chart.width / 2}" y="${chart.y + chart.height + 78}" text-anchor="middle" class="axis-label">${escapeXml(data.axes.y_bottom)}</text>
  <text x="${chart.x - 18}" y="${chart.y + chart.height / 2}" text-anchor="end" class="axis-label">${escapeXml(data.axes.x_left)}</text>
  <text x="${chart.x + chart.width + 18}" y="${chart.y + chart.height / 2}" class="axis-label">${escapeXml(data.axes.x_right)}</text>

  ${data.quadrants
    .map(
      (q) =>
        `<text x="${toX(q.x)}" y="${toY(q.y)}" class="quad-label">${escapeXml(q.label)}</text>`
    )
    .join('\n  ')}

  <text x="${chart.x}" y="104" class="legend">Legend: dashed border = early stage / under exploration | K8s tag = Kubernetes native feature</text>

  ${data.ecosystem.map((item, index) => ecosystemNode(item, index)).join('\n  ')}

  ${data.projects.map((project, index) => projectNode(project, index)).join('\n  ')}

  ${data.right_notes.map((note) => noteNode(note)).join('\n  ')}

  <text x="${chart.x}" y="${chart.y + chart.height + 38}" class="footer">Scope note: this landscape includes selected runtime projects when they are directly relevant to AI/agent workloads.</text>
  <text x="${chart.x}" y="${chart.y + chart.height + 58}" class="footer">Maintenance: edit diagrams/ai-infra-landscape.data.json then run node scripts/generate-landscape-svg.js</text>
</svg>
`;

fs.writeFileSync(outPath, svg.replace(/[ \t]+$/gm, ''));
console.log(`Generated ${path.relative(repoRoot, outPath)} from ${path.relative(repoRoot, dataPath)}`);
