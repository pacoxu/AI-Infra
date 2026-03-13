#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');
const dataPath = path.join(repoRoot, 'diagrams', 'ai-infra-landscape.data.json');
const outPath = path.join(repoRoot, 'diagrams', 'ai-infra-landscape.svg');

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

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

function cardDimensions(name) {
  return {
    width: Math.max(148, 58 + textWidth(name)),
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

function projectNode(project) {
  const group = data.groups[project.group] || data.groups.kernel;
  const baseX = toX(project.x);
  const baseY = toY(project.y);
  const size = cardDimensions(project.name);

  const left = clamp(baseX - size.width / 2, chart.x + 8, chart.x + chart.width - size.width - 8);
  const top = clamp(baseY - size.height / 2, chart.y + 8, chart.y + chart.height - size.height - 8);
  const dashed = project.stage === 'early' ? ' project-early' : '';
  const bubble = logoText(project.name, project.logo);

  return `
    <g class="project${dashed}" data-name="${escapeXml(project.name)}">
      <rect x="${left.toFixed(1)}" y="${top.toFixed(1)}" width="${size.width}" height="${size.height}" rx="8" fill="${group.fill}" stroke="${group.stroke}" />
      <circle cx="${(left + 18).toFixed(1)}" cy="${(top + size.height / 2).toFixed(1)}" r="11.5" fill="white" stroke="${group.stroke}" />
      <text x="${(left + 18).toFixed(1)}" y="${(top + size.height / 2 + 4.2).toFixed(1)}" text-anchor="middle" class="logo">${escapeXml(bubble)}</text>
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

function ecosystemNode(item) {
  const group = data.groups[item.group] || data.groups.training;
  const x = toX(item.x);
  const y = 58;
  const width = Math.max(96, textWidth(item.name) + 34);
  return `
    <g class="ecosystem-item" transform="translate(${(x - width / 2).toFixed(1)}, ${y})">
      <rect x="0" y="0" width="${width}" height="34" rx="17" fill="${group.fill}" stroke="${group.stroke}" />
      <circle cx="18" cy="17" r="8" fill="white" stroke="${group.stroke}" />
      <text x="18" y="21" text-anchor="middle" class="ecosystem-logo">${escapeXml(logoText(item.name))}</text>
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

  <text x="${chart.x}" y="104" class="legend">Legend: dashed border = early stage / under exploration</text>

  ${data.ecosystem.map((item) => ecosystemNode(item)).join('\n  ')}

  ${data.projects.map((project) => projectNode(project)).join('\n  ')}

  ${data.right_notes.map((note) => noteNode(note)).join('\n  ')}

  <text x="${chart.x}" y="${chart.y + chart.height + 38}" class="footer">Scope note: this landscape intentionally excludes storage, networking, and VM-specific projects.</text>
  <text x="${chart.x}" y="${chart.y + chart.height + 58}" class="footer">Maintenance: edit diagrams/ai-infra-landscape.data.json then run node scripts/generate-landscape-svg.js</text>
</svg>
`;

fs.writeFileSync(outPath, svg);
console.log(`Generated ${path.relative(repoRoot, outPath)} from ${path.relative(repoRoot, dataPath)}`);
