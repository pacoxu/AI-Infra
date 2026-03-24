#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');
const dataPath = path.join(repoRoot, 'diagrams', 'mcm-multicluster-radar.data.json');
const outEnPath = path.join(repoRoot, 'diagrams', 'mcm-multicluster-radar.svg');
const outZhPath = path.join(repoRoot, 'diagrams', 'mcm-multicluster-radar.zh-CN.svg');

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

const canvas = { width: 1880, height: 1260 };
const radar = { cx: 560, cy: 640, innerRadius: 86, outerRadius: 500 };
const legend = { x: 1080, y: 128, width: 730, height: 1010 };
const ringThickness = (radar.outerRadius - radar.innerRadius) / data.rings.length;

const logoCache = new Map();
const FALLBACK_SOURCE = data.sources.ecosystem || {
  label: 'Ecosystem',
  fill: '#FFF4E8',
  stroke: '#D97706'
};

const localeMap = {
  en: {
    title: data.meta.title,
    subtitle: `${data.meta.version} | updated ${data.meta.last_updated}`,
    legendTitle: 'Index',
    legendNote: 'Logo-first MCM radar with CNCF and non-CNCF ecosystem projects (issue #267).',
    maintenance: 'Maintenance: edit diagrams/mcm-multicluster-radar.data.json and run node scripts/generate-mcm-radar-svg.js',
    scope:
      'Scope: multi-cluster management for AI infra (control plane, delivery, lifecycle, tenancy, portal, and scale testing).',
    ringLabels: {
      adopt: 'ADOPT',
      trial: 'TRIAL',
      assess: 'ASSESS',
      hold: 'HOLD'
    },
    ringDescriptions: {
      adopt: 'Production default choices for most teams',
      trial: 'Strong candidates to evaluate in production pilots',
      assess: 'Promising options that need focused validation',
      hold: 'Legacy patterns to avoid for new designs'
    },
    sectorLabels: {
      control: 'Control Plane & Orchestration',
      delivery: 'GitOps & App Delivery',
      lifecycle: 'Cluster Lifecycle & IaC',
      tenancy: 'Tenancy & API Virtualization',
      ui: 'Portal & Visibility',
      testing: 'Scale Testing & Scheduling'
    },
    sourceLabels: {
      cncf: 'CNCF',
      ecosystem: 'Ecosystem (Non-CNCF)',
      kubewharf: 'Kubewharf Ecosystem'
    }
  },
  'zh-CN': {
    title: '多集群管理雷达图',
    subtitle: `${data.meta.version} | 更新于 ${data.meta.last_updated}`,
    legendTitle: '索引',
    legendNote: '以 logo 为主展示，整合 CNCF 与非 CNCF 生态项目（issue #267）。',
    maintenance: '维护：编辑 diagrams/mcm-multicluster-radar.data.json，然后运行 node scripts/generate-mcm-radar-svg.js',
    scope: '范围：AI Infra 多集群管理（控制面、交付、生命周期、多租户、门户与压测调度）。',
    ringLabels: {
      adopt: '采用',
      trial: '试用',
      assess: '评估',
      hold: '暂缓'
    },
    ringDescriptions: {
      adopt: '大多数团队可直接在生产使用',
      trial: '建议开展生产试点验证',
      assess: '有潜力，但需要重点评估',
      hold: '新方案不建议采用的模式'
    },
    sectorLabels: {
      control: '控制面与编排',
      delivery: 'GitOps 与应用交付',
      lifecycle: '集群生命周期与 IaC',
      tenancy: '多租户与 API 虚拟化',
      ui: '门户与可观测可视化',
      testing: '大规模压测与调度'
    },
    sourceLabels: {
      cncf: 'CNCF',
      ecosystem: '生态（非 CNCF）',
      kubewharf: 'Kubewharf 体系'
    }
  }
};

function escapeXml(input) {
  return String(input)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function toRadians(deg) {
  return (deg * Math.PI) / 180;
}

function polarToCartesian(cx, cy, r, angle) {
  const rad = toRadians(angle);
  return {
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad)
  };
}

function sectorPath(cx, cy, inner, outer, start, end) {
  const outerStart = polarToCartesian(cx, cy, outer, start);
  const outerEnd = polarToCartesian(cx, cy, outer, end);
  const innerEnd = polarToCartesian(cx, cy, inner, end);
  const innerStart = polarToCartesian(cx, cy, inner, start);
  const delta = ((end - start) % 360 + 360) % 360;
  const largeArc = delta > 180 ? 1 : 0;

  return [
    `M ${outerStart.x.toFixed(2)} ${outerStart.y.toFixed(2)}`,
    `A ${outer} ${outer} 0 ${largeArc} 1 ${outerEnd.x.toFixed(2)} ${outerEnd.y.toFixed(2)}`,
    `L ${innerEnd.x.toFixed(2)} ${innerEnd.y.toFixed(2)}`,
    `A ${inner} ${inner} 0 ${largeArc} 0 ${innerStart.x.toFixed(2)} ${innerStart.y.toFixed(2)}`,
    'Z'
  ].join(' ');
}

function shortLogo(name) {
  return name
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

function truncateText(input, maxChars) {
  if (input.length <= maxChars) return input;
  return `${input.slice(0, Math.max(1, maxChars - 1))}…`;
}

function detectMime(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.svg') return 'image/svg+xml';
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.webp') return 'image/webp';
  return 'image/png';
}

function logoDataUri(logoPath) {
  if (!logoPath) return null;
  const absolutePath = path.isAbsolute(logoPath) ? logoPath : path.join(repoRoot, logoPath);
  if (!fs.existsSync(absolutePath)) return null;
  if (logoCache.has(absolutePath)) return logoCache.get(absolutePath);

  const mime = detectMime(absolutePath);
  const raw = fs.readFileSync(absolutePath);
  const dataUri = `data:${mime};base64,${raw.toString('base64')}`;
  logoCache.set(absolutePath, dataUri);
  return dataUri;
}

function buildPlacedProjects() {
  const rings = data.rings.map((ring, index) => {
    const inner = radar.innerRadius + ringThickness * index;
    const outer = radar.innerRadius + ringThickness * (index + 1);
    return {
      ...ring,
      index,
      inner,
      outer,
      mid: (inner + outer) / 2
    };
  });

  const sectors = data.sectors.map((sector, index) => ({
    ...sector,
    index,
    mid: (sector.start + sector.end) / 2
  }));

  const ringIndex = new Map(rings.map((ring) => [ring.id, ring.index]));
  const ringById = new Map(rings.map((ring) => [ring.id, ring]));
  const sectorIndex = new Map(sectors.map((sector) => [sector.id, sector.index]));
  const sectorById = new Map(sectors.map((sector) => [sector.id, sector]));

  const projects = data.projects
    .slice()
    .sort((a, b) => {
      const ringDiff = (ringIndex.get(a.ring) ?? 999) - (ringIndex.get(b.ring) ?? 999);
      if (ringDiff !== 0) return ringDiff;
      const sectorDiff = (sectorIndex.get(a.sector) ?? 999) - (sectorIndex.get(b.sector) ?? 999);
      if (sectorDiff !== 0) return sectorDiff;
      return a.name.localeCompare(b.name, 'en', { sensitivity: 'base' });
    });

  const grouped = new Map();
  for (const project of projects) {
    const key = `${project.ring}::${project.sector}`;
    const arr = grouped.get(key) || [];
    arr.push(project);
    grouped.set(key, arr);
  }

  const radialSteps = [0.34, 0.56, 0.78];
  const placedProjects = [];

  for (const [key, groupProjects] of grouped.entries()) {
    const [ringId, sectorId] = key.split('::');
    const ring = ringById.get(ringId);
    const sector = sectorById.get(sectorId);
    if (!ring || !sector) continue;

    const total = groupProjects.length;
    for (let i = 0; i < total; i += 1) {
      const project = groupProjects[i];
      const angle =
        typeof project.angle === 'number'
          ? project.angle
          : sector.start + ((i + 1) / (total + 1)) * (sector.end - sector.start);
      const radial =
        typeof project.radial === 'number' ? project.radial : radialSteps[i % radialSteps.length];
      const radius = ring.inner + radial * (ring.outer - ring.inner);
      const point = polarToCartesian(radar.cx, radar.cy, radius, angle);

      placedProjects.push({
        ...project,
        ring,
        sector,
        sourceId: project.source,
        source: data.sources[project.source] || FALLBACK_SOURCE,
        x: point.x,
        y: point.y,
        logoDataUri: logoDataUri(project.logo)
      });
    }
  }

  placedProjects.sort((a, b) => {
    const ringDiff = a.ring.index - b.ring.index;
    if (ringDiff !== 0) return ringDiff;
    const sectorDiff = a.sector.index - b.sector.index;
    if (sectorDiff !== 0) return sectorDiff;
    return a.name.localeCompare(b.name, 'en', { sensitivity: 'base' });
  });

  for (let i = 0; i < placedProjects.length; i += 1) {
    placedProjects[i].id = String(i + 1).padStart(2, '0');
  }

  return { rings, sectors, placedProjects };
}

function renderProjectDot(project) {
  const x = project.x.toFixed(2);
  const y = project.y.toFixed(2);
  const ringStroke = project.source.stroke;

  let content = '';
  if (project.logoDataUri) {
    content = `<image x="${(project.x - 11).toFixed(2)}" y="${(project.y - 11).toFixed(2)}" width="22" height="22" href="${project.logoDataUri}" preserveAspectRatio="xMidYMid meet" clip-path="url(#clip-circle)" />`;
  } else {
    content = `<text x="${x}" y="${(project.y + 4.2).toFixed(2)}" text-anchor="middle" class="dot-fallback">${escapeXml(
      shortLogo(project.name)
    )}</text>`;
  }

  return `
    <g class="project-dot">
      <circle cx="${x}" cy="${y}" r="14.5" fill="#FFFFFF" stroke="${ringStroke}" stroke-width="2.2" />
      ${content}
    </g>`;
}

function renderLegendItem(project, locale, y) {
  const name = truncateText(project.name, 38);
  const sector = locale.sectorLabels[project.sector.id] || project.sector.label;
  const sourceLabel = locale.sourceLabels[project.sourceId] || project.source.label;

  const logoMarkup = project.logoDataUri
    ? `<image x="-1" y="-14" width="18" height="18" href="${project.logoDataUri}" preserveAspectRatio="xMidYMid meet" clip-path="url(#clip-circle)" />`
    : `<text x="8" y="-2" text-anchor="middle" class="legend-fallback">${escapeXml(shortLogo(project.name))}</text>`;

  return `
    <g transform="translate(${legend.x + 28}, ${y})">
      <circle cx="8" cy="-5" r="10" fill="#FFFFFF" stroke="${project.source.stroke}" stroke-width="1.5" />
      ${logoMarkup}
      <text x="26" y="-1" class="legend-item">${escapeXml(name)}</text>
      <text x="26" y="13" class="legend-item-meta">${escapeXml(`${sector} | ${sourceLabel}`)}</text>
    </g>`;
}

function renderLocale(localeKey, outPath) {
  const locale = localeMap[localeKey] || localeMap.en;
  const { rings, sectors, placedProjects } = buildPlacedProjects();

  const sectorBackgrounds = sectors
    .map((sector, index) => {
      const fill = index % 2 === 0 ? '#FAFCFF' : '#F7FAFC';
      return `<path d="${sectorPath(
        radar.cx,
        radar.cy,
        radar.innerRadius,
        radar.outerRadius,
        sector.start,
        sector.end
      )}" fill="${fill}" />`;
    })
    .join('\n  ');

  const ringCircles = rings
    .map(
      (ring) =>
        `<circle cx="${radar.cx}" cy="${radar.cy}" r="${ring.outer.toFixed(2)}" fill="${ring.fill}" fill-opacity="0.36" stroke="${ring.stroke}" stroke-width="1.4" />`
    )
    .reverse()
    .join('\n  ');

  const ringBoundaries = rings
    .map(
      (ring) =>
        `<circle cx="${radar.cx}" cy="${radar.cy}" r="${ring.outer.toFixed(
          2
        )}" fill="none" stroke="#8A94A6" stroke-width="0.8" stroke-dasharray="4 5" />`
    )
    .join('\n  ');

  const sectorLines = sectors
    .map((sector) => {
      const start = polarToCartesian(radar.cx, radar.cy, radar.innerRadius, sector.start);
      const end = polarToCartesian(radar.cx, radar.cy, radar.outerRadius, sector.start);
      return `<line x1="${start.x.toFixed(2)}" y1="${start.y.toFixed(2)}" x2="${end.x.toFixed(
        2
      )}" y2="${end.y.toFixed(2)}" stroke="#99A3B2" stroke-width="1.1" />`;
    })
    .join('\n  ');

  const sectorLabels = sectors
    .map((sector) => {
      const pos = polarToCartesian(radar.cx, radar.cy, radar.outerRadius + 34, sector.mid);
      const cos = Math.cos(toRadians(sector.mid));
      const anchor = cos > 0.24 ? 'start' : cos < -0.24 ? 'end' : 'middle';
      const label = locale.sectorLabels[sector.id] || sector.label;
      return `<text x="${pos.x.toFixed(2)}" y="${(pos.y + 4).toFixed(2)}" text-anchor="${anchor}" class="sector-label">${escapeXml(
        label
      )}</text>`;
    })
    .join('\n  ');

  const ringLabels = rings
    .map((ring) => {
      const pos = polarToCartesian(radar.cx, radar.cy, ring.mid, -104);
      const label = locale.ringLabels[ring.id] || ring.label;
      return `<text x="${(pos.x - 12).toFixed(2)}" y="${(pos.y + 4).toFixed(
        2
      )}" text-anchor="end" class="ring-label">${escapeXml(label)}</text>`;
    })
    .join('\n  ');

  const projectDots = placedProjects.map((project) => renderProjectDot(project)).join('\n  ');

  const sourceLegendEntries = Object.entries(data.sources)
    .map(([id, source], index) => {
      const x = legend.x + 28 + index * 220;
      const y = legend.y + 80;
      const label = locale.sourceLabels[id] || source.label;
      return `
    <g transform="translate(${x}, ${y})">
      <circle cx="0" cy="0" r="9" fill="${source.fill}" stroke="${source.stroke}" stroke-width="2" />
      <text x="16" y="4.5" class="legend-source">${escapeXml(label)}</text>
    </g>`;
    })
    .join('\n  ');

  const projectsByRing = new Map(rings.map((ring) => [ring.id, []]));
  for (const project of placedProjects) {
    projectsByRing.get(project.ring.id).push(project);
  }

  let legendY = legend.y + 136;
  let ringDetails = '';

  for (const ring of rings) {
    const items = projectsByRing.get(ring.id) || [];
    const ringTitle = locale.ringLabels[ring.id] || ring.label;
    const ringDesc = locale.ringDescriptions[ring.id] || ring.description;

    ringDetails += `<text x="${legend.x + 18}" y="${legendY}" class="legend-ring-title" fill="${ring.stroke}">${escapeXml(
      `${ringTitle} (${items.length})`
    )}</text>\n`;
    legendY += 18;
    ringDetails += `<text x="${legend.x + 18}" y="${legendY}" class="legend-ring-desc">${escapeXml(
      ringDesc
    )}</text>\n`;
    legendY += 18;

    for (const item of items) {
      ringDetails += `${renderLegendItem(item, locale, legendY)}\n`;
      legendY += 24;
    }

    legendY += 10;
  }

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${canvas.width}" height="${canvas.height}" viewBox="0 0 ${canvas.width} ${canvas.height}" role="img" aria-labelledby="title desc">
  <title id="title">${escapeXml(locale.title)} (${escapeXml(data.meta.version)})</title>
  <desc id="desc">Data-driven multi-cluster management radar with logo-based project markers.</desc>
  <defs>
    <clipPath id="clip-circle" clipPathUnits="objectBoundingBox">
      <circle cx="0.5" cy="0.5" r="0.5" />
    </clipPath>
    <style>
      .title { font: 700 42px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .subtitle { font: 500 19px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #4B5563; }
      .sector-label { font: 600 13px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #334155; }
      .ring-label { font: 700 14px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #475569; letter-spacing: 0.6px; }
      .dot-fallback { font: 700 11.2px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .legend-fallback { font: 700 9.2px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .legend-title { font: 700 24px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #111827; }
      .legend-note { font: 500 13.5px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #4B5563; }
      .legend-source { font: 600 13px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #334155; }
      .legend-ring-title { font: 700 16px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; }
      .legend-ring-desc { font: 500 12.5px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #64748B; }
      .legend-item { font: 600 12px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #1F2937; }
      .legend-item-meta { font: 500 11px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #64748B; }
      .footer { font: 500 13px ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; fill: #64748B; }
    </style>
  </defs>

  <rect x="0" y="0" width="${canvas.width}" height="${canvas.height}" fill="#F3F5F8" />
  <rect x="${legend.x}" y="${legend.y}" width="${legend.width}" height="${legend.height}" rx="16" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.4" />

  <text x="76" y="72" class="title">${escapeXml(locale.title)}</text>
  <text x="76" y="102" class="subtitle">${escapeXml(locale.subtitle)}</text>

  ${sectorBackgrounds}
  ${ringCircles}
  ${ringBoundaries}
  ${sectorLines}
  ${sectorLabels}
  ${ringLabels}

  <circle cx="${radar.cx}" cy="${radar.cy}" r="${radar.innerRadius - 2}" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.2" />
  <text x="${radar.cx}" y="${radar.cy - 4}" text-anchor="middle" class="ring-label">MCM</text>
  <text x="${radar.cx}" y="${radar.cy + 14}" text-anchor="middle" class="legend-note">2026Q1</text>

  ${projectDots}

  <text x="${legend.x + 18}" y="${legend.y + 40}" class="legend-title">${escapeXml(locale.legendTitle)}</text>
  <text x="${legend.x + 18}" y="${legend.y + 60}" class="legend-note">${escapeXml(locale.legendNote)}</text>
  ${sourceLegendEntries}
  ${ringDetails}

  <text x="76" y="1186" class="footer">${escapeXml(locale.maintenance)}</text>
  <text x="76" y="1208" class="footer">${escapeXml(locale.scope)}</text>
</svg>
`;

  fs.writeFileSync(outPath, svg);
}

renderLocale('en', outEnPath);
renderLocale('zh-CN', outZhPath);

console.log(
  `Generated ${path.relative(repoRoot, outEnPath)} and ${path.relative(repoRoot, outZhPath)} from ${path.relative(repoRoot, dataPath)}`
);
