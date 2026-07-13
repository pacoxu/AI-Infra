#!/usr/bin/env python3

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "diagrams"

WIDTH = 1600
HEIGHT = 900

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


PALETTE = {
    "bg": "#ffffff",
    "title": "#0f172a",
    "subtitle": "#334155",
    "muted": "#475569",
    "border": "#94a3b8",
    "arrow": "#64748b",
    "panel": "#f8fafc",
    "note_fill": "#ffffff",
    "note_border": "#cbd5e1",
    "blue": "#dbeafe",
    "blue_border": "#60a5fa",
    "teal": "#ccfbf1",
    "teal_border": "#2dd4bf",
    "green": "#dcfce7",
    "green_border": "#4ade80",
    "mint": "#d1fae5",
    "mint_border": "#34d399",
    "amber": "#fef3c7",
    "amber_border": "#f59e0b",
    "rose": "#ffe4e6",
    "rose_border": "#fb7185",
    "violet": "#ede9fe",
    "violet_border": "#8b5cf6",
    "slate": "#f1f5f9",
    "slate_border": "#94a3b8",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=text_font)
    return right - left, bottom - top


def multiline_size(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    text_font: ImageFont.FreeTypeFont,
    spacing: int,
) -> tuple[int, int]:
    width = 0
    height = 0
    cached_lines = list(lines)
    if not cached_lines:
        return 0, 0
    line_height = text_size(draw, "Ag", text_font)[1]
    for index, line in enumerate(cached_lines):
        line_width, _ = text_size(draw, line or " ", text_font)
        width = max(width, line_width)
        height += line_height
        if index < len(cached_lines) - 1:
            height += spacing
    return width, height


def split_long_token(
    draw: ImageDraw.ImageDraw,
    token: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    parts: list[str] = []
    current = ""
    for char in token:
        candidate = current + char
        if text_size(draw, candidate, text_font)[0] <= max_width or not current:
            current = candidate
            continue
        parts.append(current)
        current = char
    if current:
        parts.append(current)
    return parts


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    wrapped: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            wrapped.append("")
            continue
        line = words[0]
        if text_size(draw, line, text_font)[0] > max_width:
            pieces = split_long_token(draw, line, text_font, max_width)
            wrapped.extend(pieces[:-1])
            line = pieces[-1]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if text_size(draw, candidate, text_font)[0] <= max_width:
                line = candidate
                continue
            wrapped.append(line)
            if text_size(draw, word, text_font)[0] <= max_width:
                line = word
                continue
            pieces = split_long_token(draw, word, text_font, max_width)
            wrapped.extend(pieces[:-1])
            line = pieces[-1]
        wrapped.append(line)
    return wrapped


def fit_box_text(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    title: str,
    subtitle: str = "",
    *,
    max_title_size: int = 26,
    min_title_size: int = 14,
    max_subtitle_size: int = 18,
    min_subtitle_size: int = 11,
    padding_x: int = 16,
    padding_y: int = 14,
) -> tuple[list[str], ImageFont.FreeTypeFont, list[str], ImageFont.FreeTypeFont, int, int]:
    x0, y0, x1, y1 = rect
    inner_width = x1 - x0 - padding_x * 2
    inner_height = y1 - y0 - padding_y * 2

    for title_size in range(max_title_size, min_title_size - 1, -1):
        title_font = font(title_size, bold=False)
        subtitle_size = min(max_subtitle_size, max(min_subtitle_size, int(title_size * 0.62)))
        subtitle_font = font(subtitle_size, bold=False)

        title_lines = wrap_text(draw, title, title_font, inner_width)
        subtitle_lines = wrap_text(draw, subtitle, subtitle_font, inner_width) if subtitle else []

        title_spacing = max(4, int(title_size * 0.22))
        subtitle_spacing = max(3, int(subtitle_size * 0.22))
        group_gap = 8 if subtitle_lines else 0

        title_width, title_height = multiline_size(draw, title_lines, title_font, title_spacing)
        subtitle_width, subtitle_height = multiline_size(draw, subtitle_lines, subtitle_font, subtitle_spacing)

        group_width = max(title_width, subtitle_width)
        group_height = title_height + subtitle_height + group_gap

        if group_width <= inner_width and group_height <= inner_height:
            return (
                title_lines,
                title_font,
                subtitle_lines,
                subtitle_font,
                title_spacing,
                subtitle_spacing,
            )

    title_font = font(min_title_size, bold=False)
    subtitle_font = font(min_subtitle_size, bold=False)
    return (
        wrap_text(draw, title, title_font, inner_width),
        title_font,
        wrap_text(draw, subtitle, subtitle_font, inner_width) if subtitle else [],
        subtitle_font,
        max(4, int(min_title_size * 0.22)),
        max(3, int(min_subtitle_size * 0.22)),
    )


def draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    lines: list[str],
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
) -> None:
    if not lines:
        return
    x0, y0, x1, y1 = rect
    total_width, total_height = multiline_size(draw, lines, text_font, spacing)
    current_y = y0 + ((y1 - y0) - total_height) / 2
    line_height = text_size(draw, "Ag", text_font)[1]
    for line in lines:
        line_width, _ = text_size(draw, line or " ", text_font)
        current_x = x0 + ((x1 - x0) - line_width) / 2
        draw.text((current_x, current_y), line, font=text_font, fill=fill)
        current_y += line_height + spacing


def draw_box(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    *,
    fill: str,
    border: str,
    title: str,
    subtitle: str = "",
    radius: int = 22,
    border_width: int = 3,
    max_title_size: int = 26,
    min_title_size: int = 14,
    max_subtitle_size: int = 18,
    min_subtitle_size: int = 11,
    text_fill: str = PALETTE["title"],
) -> None:
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=border, width=border_width)
    title_lines, title_font, subtitle_lines, subtitle_font, title_spacing, subtitle_spacing = fit_box_text(
        draw,
        rect,
        title,
        subtitle,
        max_title_size=max_title_size,
        min_title_size=min_title_size,
        max_subtitle_size=max_subtitle_size,
        min_subtitle_size=min_subtitle_size,
    )

    x0, y0, x1, y1 = rect
    title_width, title_height = multiline_size(draw, title_lines, title_font, title_spacing)
    subtitle_width, subtitle_height = multiline_size(draw, subtitle_lines, subtitle_font, subtitle_spacing)
    group_gap = 8 if subtitle_lines else 0
    group_height = title_height + subtitle_height + group_gap
    group_top = y0 + ((y1 - y0) - group_height) / 2

    draw_centered_lines(
        draw,
        (x0, int(group_top), x1, int(group_top + title_height)),
        title_lines,
        title_font,
        text_fill,
        title_spacing,
    )
    if subtitle_lines:
        subtitle_top = int(group_top + title_height + group_gap)
        draw_centered_lines(
            draw,
            (x0, subtitle_top, x1, subtitle_top + subtitle_height),
            subtitle_lines,
            subtitle_font,
            PALETTE["subtitle"],
            subtitle_spacing,
        )


def draw_note(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    title: str,
    body: str,
) -> None:
    draw_box(
        draw,
        rect,
        fill=PALETTE["note_fill"],
        border=PALETTE["note_border"],
        title=title,
        subtitle=body,
        radius=18,
        border_width=2,
        max_title_size=21,
        min_title_size=15,
        max_subtitle_size=16,
        min_subtitle_size=11,
    )


def draw_tag(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    text: str,
    fill: str,
    border: str,
) -> None:
    draw_box(
        draw,
        rect,
        fill=fill,
        border=border,
        title=text,
        radius=16,
        border_width=2,
        max_title_size=16,
        min_title_size=11,
        max_subtitle_size=14,
        min_subtitle_size=10,
    )


def draw_path(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    *,
    color: str = PALETTE["arrow"],
    width: int = 4,
    arrow: bool = True,
) -> None:
    for start, end in zip(points, points[1:]):
        draw.line((start, end), fill=color, width=width)
    if not arrow or len(points) < 2:
        return
    x0, y0 = points[-2]
    x1, y1 = points[-1]
    angle = math.atan2(y1 - y0, x1 - x0)
    head_length = 16
    head_angle = math.pi / 7
    left = (
        x1 - head_length * math.cos(angle - head_angle),
        y1 - head_length * math.sin(angle - head_angle),
    )
    right = (
        x1 - head_length * math.cos(angle + head_angle),
        y1 - head_length * math.sin(angle + head_angle),
    )
    draw.polygon([points[-1], left, right], fill=color)


def add_heading(
    draw: ImageDraw.ImageDraw,
    title: str,
    subtitle: str,
) -> None:
    title_font = font(34)
    subtitle_font = font(18)
    title_width, title_height = text_size(draw, title, title_font)
    subtitle_width, subtitle_height = text_size(draw, subtitle, subtitle_font)
    draw.text(((WIDTH - title_width) / 2, 42), title, font=title_font, fill=PALETTE["title"])
    draw.text(((WIDTH - subtitle_width) / 2, 84), subtitle, font=subtitle_font, fill=PALETTE["muted"])
    draw.line((72, 118, WIDTH - 72, 118), fill="#e2e8f0", width=2)


def base_canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (WIDTH, HEIGHT), PALETTE["bg"])
    draw = ImageDraw.Draw(image)
    add_heading(draw, title, subtitle)
    return image, draw


def generate_apiserver_interfaces() -> Image.Image:
    image, draw = base_canvas(
        "Pod Lifecycle: APIServer And External Interfaces",
        "Control plane decisions, node-side interfaces, and the status fields operators usually inspect",
    )

    left_y = 220
    box_h = 92
    draw_box(draw, (80, left_y, 220, left_y + box_h), fill=PALETTE["slate"], border=PALETTE["slate_border"], title="Manifest", subtitle="Static Pod")
    draw_box(draw, (80, left_y + 120, 220, left_y + 120 + box_h), fill=PALETTE["slate"], border=PALETTE["slate_border"], title="Controllers", subtitle="Deployment / Job / DS")
    draw_box(draw, (270, left_y + 60, 450, left_y + 60 + box_h), fill=PALETTE["blue"], border=PALETTE["blue_border"], title="API Server", subtitle="spec / status / events")
    draw_box(draw, (520, left_y - 20, 700, left_y - 20 + box_h), fill=PALETTE["violet"], border=PALETTE["violet_border"], title="Admission", subtitle="mutate / validate")
    draw_box(draw, (520, left_y + 140, 720, left_y + 140 + box_h), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="SchedulingGates", subtitle="Pending until cleared")
    draw_box(draw, (790, left_y + 60, 950, left_y + 60 + box_h), fill=PALETTE["green"], border=PALETTE["green_border"], title="Scheduler", subtitle="bind node")
    draw_box(draw, (670, 500, 940, 590), fill=PALETTE["slate"], border=PALETTE["blue_border"], title="PodStatus", subtitle="phase / conditions / deletionTimestamp")

    interface_y = 220
    small_w = 110
    gap = 16
    start_x = 980
    interface_specs = [
        ("CNI", "network / sandbox"),
        ("CRI", "sandbox / containers"),
        ("CSI", "attach / mount"),
        ("DRA", "claim / devices"),
        ("Runtime", "image / pull / start"),
    ]
    for index, (title, subtitle) in enumerate(interface_specs):
        x0 = start_x + index * (small_w + gap)
        draw_box(draw, (x0, interface_y, x0 + small_w, interface_y + 70), fill=PALETTE["panel"], border=PALETTE["slate_border"], title=title, subtitle=subtitle, max_title_size=18, max_subtitle_size=13)
        draw_path(draw, [(x0 + small_w // 2, interface_y + 70), (x0 + small_w // 2, 350)], width=3)

    draw_box(
        draw,
        (980, 350, 1520, 450),
        fill=PALETTE["blue"],
        border=PALETTE["blue_border"],
        title="kubelet",
        subtitle="runtime manager / volume manager / probe manager",
        max_title_size=24,
        max_subtitle_size=16,
    )

    draw_path(draw, [(220, left_y + 46), (270, left_y + 106)])
    draw_path(draw, [(220, left_y + 166), (270, left_y + 106)])
    draw_path(draw, [(450, left_y + 106), (520, left_y + 26)])
    draw_path(draw, [(450, left_y + 106), (520, left_y + 186)])
    draw_path(draw, [(700, left_y + 26 + 46), (790, left_y + 106)])
    draw_path(draw, [(720, left_y + 186 + 46), (790, left_y + 106)], color=PALETTE["amber_border"])
    draw_path(draw, [(870, left_y + 152), (870, 500)])

    draw_note(
        draw,
        (80, 650, 470, 810),
        "APIServer View",
        "Users usually observe spec changes, phase, conditions, events, and deletionTimestamp through the API object.",
    )
    draw_note(
        draw,
        (520, 650, 910, 810),
        "v1.36 Focus",
        "PodReadyToStartContainers, DisruptionTarget, PodResize conditions, and container restart rules now matter in day two debugging.",
    )
    draw_note(
        draw,
        (960, 650, 1530, 810),
        "Interface Split",
        "CNI prepares network, CRI launches sandbox and containers, CSI mounts storage, and DRA allocates devices before workload startup.",
    )
    return image


def generate_main_flow() -> Image.Image:
    image, draw = base_canvas(
        "Pod Lifecycle: Main State Flow",
        "A clearer state path from object creation to terminal outcomes, with the conditions that add useful detail",
    )

    top_y = 250
    boxes = [
        ((80, top_y, 200, top_y + 90), PALETTE["slate"], PALETTE["slate_border"], "Create", "accepted by API"),
        ((250, top_y, 410, top_y + 90), PALETTE["teal"], PALETTE["teal_border"], "Pending", "unscheduled / preparing"),
        ((460, top_y, 650, top_y + 90), PALETTE["blue"], PALETTE["blue_border"], "PodScheduled", "nodeName written back"),
        ((710, top_y, 980, top_y + 90), PALETTE["green"], PALETTE["green_border"], "Ready To Start Containers", "sandbox / network / volumes ready"),
        ((1040, top_y, 1210, top_y + 90), PALETTE["mint"], PALETTE["mint_border"], "Initialized", "init finished"),
        ((1270, top_y, 1530, top_y + 90), PALETTE["teal"], PALETTE["teal_border"], "Running / Ready", "ContainersReady=True  Ready=True"),
    ]
    for rect, fill, border, title, subtitle in boxes:
        draw_box(draw, rect, fill=fill, border=border, title=title, subtitle=subtitle)

    for first, second in zip(boxes, boxes[1:]):
        x0 = first[0][2]
        y0 = (first[0][1] + first[0][3]) // 2
        x1 = second[0][0]
        y1 = (second[0][1] + second[0][3]) // 2
        draw_path(draw, [(x0, y0), (x1, y1)])

    tag_specs = [
        ((485, 372, 625, 402), "PodScheduled", PALETTE["blue"], PALETTE["blue_border"]),
        ((760, 372, 940, 402), "PodReadyToStartContainers", PALETTE["mint"], PALETTE["mint_border"]),
        ((1070, 372, 1185, 402), "Initialized", PALETTE["green"], PALETTE["green_border"]),
        ((1325, 372, 1495, 402), "ContainersReady / Ready", PALETTE["teal"], PALETTE["teal_border"]),
    ]
    for rect, text, fill, border in tag_specs:
        draw_tag(draw, rect, text, fill, border)

    draw_box(draw, (1270, 430, 1435, 500), fill=PALETTE["mint"], border=PALETTE["mint_border"], title="Succeeded", subtitle="clean exit")
    draw_box(draw, (1270, 520, 1435, 590), fill=PALETTE["rose"], border=PALETTE["rose_border"], title="Failed", subtitle="non zero exit")
    draw_box(draw, (1270, 610, 1435, 680), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="Unknown", subtitle="node status missing")
    draw_path(draw, [(1400, top_y + 90), (1400, 430)])
    draw_path(draw, [(1400, top_y + 90), (1470, 555), (1435, 555)])
    draw_path(draw, [(1530, top_y + 45), (1570, 645), (1435, 645)])

    draw_note(
        draw,
        (80, 710, 500, 840),
        "How To Read It",
        "Pending still covers scheduling wait, image pull, sandbox creation, init work, and other preparation before regular containers run.",
    )
    draw_note(
        draw,
        (540, 710, 970, 840),
        "v1.36 Signals",
        "PodResizePending, PodResizeInProgress, DisruptionTarget, container restart rules, and RestartAllContainers can change behavior without creating a new Pod.",
    )
    draw_note(
        draw,
        (1010, 710, 1530, 840),
        "Important Distinction",
        "Terminal phase is not the same as API object removal. Unknown is a reachability state, not a success or failure verdict.",
    )
    return image


def generate_eviction_deletion() -> Image.Image:
    image, draw = base_canvas(
        "Pod Lifecycle: Eviction And Deletion",
        "Where disruption starts, how APIServer signals it, and how kubelet executes the stop path on the node",
    )

    trigger_y = 190
    triggers = [
        ("Delete", "kubectl / controller"),
        ("Evict", "PDB aware API"),
        ("Preempt", "higher priority Pod"),
        ("Node Pressure", "memory / disk / PID"),
        ("Node Shutdown", "graceful shutdown"),
    ]
    start_x = 70
    trigger_w = 180
    gap = 22
    for index, (title, subtitle) in enumerate(triggers):
        x0 = start_x + index * (trigger_w + gap)
        draw_box(draw, (x0, trigger_y, x0 + trigger_w, trigger_y + 84), fill=PALETTE["rose"], border=PALETTE["rose_border"], title=title, subtitle=subtitle)
        draw_path(draw, [(x0 + trigger_w // 2, trigger_y + 84), (x0 + trigger_w // 2, 315)], width=3)

    draw_box(draw, (1110, trigger_y, 1510, trigger_y + 84), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="APIServer Sets deletionTimestamp", subtitle="grace period now becomes visible")

    draw_path(draw, [(160, 315), (1310, 315), (1310, trigger_y + 84)], arrow=False)
    draw_path(draw, [(1310, 315), (1310, 345)], width=4)

    draw_box(draw, (1030, 360, 1530, 450), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="DisruptionTarget=True", subtitle="delete / evict / preempt / shutdown path is now explicit")
    draw_box(draw, (80, 360, 430, 450), fill=PALETTE["slate"], border=PALETTE["slate_border"], title="Running Pod", subtitle="still serving until drain starts")
    draw_box(draw, (470, 360, 980, 450), fill=PALETTE["blue"], border=PALETTE["blue_border"], title="EndpointSlice Drain", subtitle="ready=false  serving may stay true while terminating")

    draw_path(draw, [(430, 405), (470, 405)])
    draw_path(draw, [(980, 405), (1030, 405)])

    draw_box(draw, (150, 540, 430, 625), fill=PALETTE["violet"], border=PALETTE["violet_border"], title="PreStop Hook", subtitle="runs before TERM when defined")
    draw_box(draw, (500, 540, 780, 625), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="stopSignal / SIGTERM", subtitle="grace period countdown starts")
    draw_box(draw, (850, 540, 1130, 625), fill=PALETTE["mint"], border=PALETTE["mint_border"], title="Sidecars Stop Last", subtitle="reverse order for Always init sidecars")
    draw_box(draw, (1200, 540, 1480, 625), fill=PALETTE["rose"], border=PALETTE["rose_border"], title="Force Kill If Needed", subtitle="remaining containers get SIGKILL")

    draw_path(draw, [(1310, 450), (1310, 505), (290, 505), (290, 540)])
    draw_path(draw, [(430, 582), (500, 582)])
    draw_path(draw, [(780, 582), (850, 582)])
    draw_path(draw, [(1130, 582), (1200, 582)])

    draw_box(draw, (210, 700, 540, 785), fill=PALETTE["slate"], border=PALETTE["slate_border"], title="Succeeded / Failed", subtitle="clean terminal status recorded")
    draw_box(draw, (630, 700, 960, 785), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="Unknown", subtitle="node cannot report back")
    draw_box(draw, (1100, 700, 1450, 785), fill=PALETTE["panel"], border=PALETTE["slate_border"], title="API Object Removed", subtitle="after finalizers and grace complete")

    draw_path(draw, [(990, 625), (990, 680), (540, 680), (540, 742)])
    draw_path(draw, [(1340, 625), (1340, 700)])
    draw_path(draw, [(640, 625), (640, 700), (795, 700)])

    draw_note(
        draw,
        (80, 120, 560, 190),
        "Key Point",
        "Eviction starts as an API decision, but kubelet still performs the actual stop sequence on the node.",
    )
    return image


def generate_probe_hook() -> Image.Image:
    image, draw = base_canvas(
        "Pod Lifecycle: Probes, Hooks, And Runtime Control",
        "What keeps a Pod ready, what restarts a container, and what runs during startup and shutdown",
    )

    draw_box(draw, (640, 250, 980, 370), fill=PALETTE["blue"], border=PALETTE["blue_border"], title="Running Pod", subtitle="regular app containers execute here")
    draw_box(draw, (150, 180, 410, 270), fill=PALETTE["violet"], border=PALETTE["violet_border"], title="startupProbe", subtitle="protects slow boot and gates liveness")
    draw_box(draw, (150, 340, 410, 430), fill=PALETTE["mint"], border=PALETTE["mint_border"], title="readinessProbe", subtitle="controls Ready and traffic eligibility")
    draw_box(draw, (150, 500, 410, 590), fill=PALETTE["rose"], border=PALETTE["rose_border"], title="livenessProbe", subtitle="restarts unhealthy containers")

    draw_path(draw, [(410, 225), (640, 300)])
    draw_path(draw, [(410, 385), (640, 310)])
    draw_path(draw, [(410, 545), (640, 320)])

    draw_box(draw, (1130, 180, 1450, 270), fill=PALETTE["blue"], border=PALETTE["blue_border"], title="PostStart Hook", subtitle="runs immediately after container start")
    draw_box(draw, (1130, 340, 1450, 430), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="PreStop Hook", subtitle="runs before TERM while grace remains")
    draw_box(draw, (1130, 500, 1450, 590), fill=PALETTE["amber"], border=PALETTE["amber_border"], title="terminationGracePeriodSeconds", subtitle="defines stop budget")

    draw_path(draw, [(980, 300), (1130, 225)])
    draw_path(draw, [(980, 310), (1130, 385)])
    draw_path(draw, [(980, 320), (1130, 545)])

    draw_box(draw, (520, 470, 760, 560), fill=PALETTE["panel"], border=PALETTE["slate_border"], title="Ephemeral Container", subtitle="debug only  not part of readiness")
    draw_box(draw, (840, 470, 1080, 560), fill=PALETTE["panel"], border=PALETTE["slate_border"], title="Sidecar Pattern", subtitle="initContainer plus restartPolicy=Always")
    draw_path(draw, [(640, 370), (640, 470)])
    draw_path(draw, [(980, 370), (980, 470)])

    draw_note(
        draw,
        (90, 670, 470, 810),
        "Probe Roles",
        "Startup handles slow boot, readiness controls traffic, and liveness restarts a stuck container rather than replacing the whole Pod.",
    )
    draw_note(
        draw,
        (520, 670, 1080, 810),
        "Runtime Details",
        "CrashLoopBackOff backoff is tunable, and RestartAllContainers can rerun init plus app containers while keeping the same Pod identity.",
    )
    draw_note(
        draw,
        (1130, 670, 1510, 810),
        "Shutdown Order",
        "PreStop and stopSignal shape termination, while sidecars stop after main containers when the sidecar pattern is used.",
    )
    return image


def save(image: Image.Image, name: str) -> None:
    output = DIAGRAMS_DIR / name
    image.save(output, format="PNG")
    print(f"wrote {output}")


def main() -> None:
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    save(generate_apiserver_interfaces(), "pod-lifecycle-apiserver-interfaces.png")
    save(generate_main_flow(), "pod-lifecycle-main-flow.png")
    save(generate_eviction_deletion(), "pod-lifecycle-eviction-deletion.png")
    save(generate_probe_hook(), "pod-lifecycle-probe-hook.png")


if __name__ == "__main__":
    main()
