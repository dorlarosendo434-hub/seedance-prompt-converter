#!/usr/bin/env python3
"""Diagnose common Seedance 2.0-style prompt risks before 2.5 conversion."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


EMPTY_ADJECTIVES = ["美丽的", "优雅的", "华丽的", "史诗级", "大片感", "高级感", "震撼", "极致细节"]
QUALITY_WORDS = ["8k", "4k", "超高清", "最高画质", "uhd"]
NEGATIVE_PATTERNS = [r"不要", r"不能出现", r"避免", r"禁止", r"\bno\s+"]
TIME_PATTERN = re.compile(r"(?:\d{1,2}:\d{2}|\d+(?:\.\d+)?\s*[–—-]\s*\d+(?:\.\d+)?\s*秒)", re.I)
REFERENCE_PATTERN = re.compile(r"@(?:image|video|audio)\d+|参考图\s*\d+|参考视频\s*\d+", re.I)
EXCLUSION_PATTERN = re.compile(r"不使用|只定义|只参考|不要使用|排除")
AUDIO_WORDS = re.compile(r"对白|台词|口播|音效|环境音|音乐|bgm|字幕", re.I)
AUDIO_ROUTING = re.compile(r"\([^\n()]+\)|<[^\n<>]+>|\{[^\n{}]+\}|【[^\n【】]+】")
GENERIC_SUBJECT = re.compile(r"(?:一个|一名)?(?:人物|角色|主角)")
SUBJECT_ANCHORS = re.compile(r"\d+\s*岁|发型|长发|短发|肤色|穿|服装|外套|裙|衬衫|夹克|身高|体型")
ACTION_WORDS = ["走", "跑", "转身", "抬手", "挥手", "微笑", "侧头", "拿起", "放下", "跳", "飞", "结印", "拍", "俯冲", "拉", "摸", "展示"]

STYLE_FAMILIES = {
    "赛博朋克": ["赛博朋克", "霓虹未来"],
    "水墨/国画": ["水墨", "国画", "写意山水"],
    "纪实": ["纪实", "纪录片", "手机实拍"],
    "复古/胶片": ["胶片", "复古", "kodak", "柯达"],
    "暗黑/哥特": ["暗黑", "哥特"],
}

CAMERA_FAMILIES = {
    "推进": ["推进", "推近", "dolly-in", "push-in"],
    "拉远": ["拉远", "dolly-out", "pull-back"],
    "环绕": ["环绕", "orbit", "arc shot"],
    "手持": ["手持", "handheld"],
    "固定": ["固定镜头", "固定机位", "locked-off"],
    "横移": ["横移", "侧移", "lateral track", "truck"],
}


def hits(text: str, words: list[str]) -> list[str]:
    lowered = text.lower()
    return [word for word in words if word.lower() in lowered]


def present_families(text: str, families: dict[str, list[str]]) -> list[str]:
    return [name for name, words in families.items() if hits(text, words)]


def add_issue(issues: list[dict[str, str]], level: str, title: str, detail: str, matched: str = "") -> None:
    issues.append({"level": level, "title": title, "detail": detail, "matched": matched})


def analyze(text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    found = hits(text, EMPTY_ADJECTIVES)
    if found:
        add_issue(issues, "high", "空洞形容词", "这些修饰词无法稳定转换成具体画面，应替换为可检查的外观、光线、尺度或动作描述", "、".join(found))

    found = hits(text, QUALITY_WORDS)
    if found:
        add_issue(issues, "low", "画质词堆砌", "分辨率通常由输出参数控制，提示词中的画质口号容易占用注意力，建议删除", "、".join(found))

    styles = present_families(text, STYLE_FAMILIES)
    if len(styles) > 1:
        add_issue(issues, "high", "风格冲突", "发现多个可能互斥的风格族，应保留一个主风格或明确主次关系", "、".join(styles))

    camera = present_families(text, CAMERA_FAMILIES)
    if len(camera) > 1 and not TIME_PATTERN.search(text):
        add_issue(issues, "high", "运镜冲突", "未分镜的提示词中出现多种主运镜，应只保留一种并写明起止景别", "、".join(camera))

    negatives = [m.group(0) for pattern in NEGATIVE_PATTERNS for m in re.finditer(pattern, text, re.I)]
    if negatives:
        add_issue(issues, "medium", "负面提示词", "将长串负面词改为简短、正向、可逐帧检查的约束", f"共 {len(negatives)} 处")

    if not TIME_PATTERN.search(text):
        add_issue(issues, "medium", "缺少时间线", "未发现时间分段；动作较多或时长超过 15 秒时容易出现节奏拥挤和后半段漂移")

    if REFERENCE_PATTERN.search(text) and not EXCLUSION_PATTERN.search(text):
        add_issue(issues, "high", "参考素材未分工", "为每份参考素材写明使用的属性和不使用的属性，防止背景、服装或身份污染")

    if AUDIO_WORDS.search(text) and not AUDIO_ROUTING.search(text):
        add_issue(issues, "medium", "声音未路由", "使用 (音乐/环境床)、<音效>、{对白}、【字幕】分离声音通道")

    action_count = sum(len(re.findall(re.escape(word), text)) for word in ACTION_WORDS)
    if action_count >= 6 and not TIME_PATTERN.search(text):
        add_issue(issues, "medium", "动作过密", "多个动作没有时间分配；拆成时间段，每段只保留一个核心变化", f"粗略命中 {action_count} 个动作")

    if GENERIC_SUBJECT.search(text) and not SUBJECT_ANCHORS.search(text):
        add_issue(issues, "medium", "主体缺少锚点", "补充年龄段、发型、服装、肤色或体型等可辨认特征，降低跨镜头漂移")

    return issues


def render(issues: list[dict[str, str]]) -> str:
    icons = {"high": "🔴", "medium": "🟡", "low": "⚪"}
    names = {"high": "高优先级", "medium": "中优先级", "low": "低优先级"}
    counts = {level: sum(i["level"] == level for i in issues) for level in icons}
    lines = [
        f"诊断完成：共发现 {len(issues)} 个问题",
        f"  🔴 高优先级：{counts['high']}  |  🟡 中优先级：{counts['medium']}  |  ⚪ 低优先级：{counts['low']}",
        "=" * 60,
    ]
    if not issues:
        lines.append("未发现常见的 2.0 风格风险；仍需人工检查语义、素材职责和镜头连续性。")
        return "\n".join(lines)

    for index, issue in enumerate(issues, 1):
        lines.extend(["", f"{icons[issue['level']]} [{index}] {issue['title']}（{names[issue['level']]}）", f"   {issue['detail']}"])
        if issue["matched"]:
            lines.append(f"   命中：{issue['matched']}")
    lines.extend(["", "=" * 60, "下一步：按 SKILL.md 的七项转换规则重构为 Seedance 2.5 格式。"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="诊断 Seedance 2.0 风格提示词的常见迁移风险")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("prompt", nargs="?", help="直接传入提示词")
    source.add_argument("--file", type=Path, help="从 UTF-8 文本文件读取提示词")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        text = args.file.read_text(encoding="utf-8") if args.file else args.prompt
    except OSError as exc:
        print(f"读取提示词失败：{exc}", file=sys.stderr)
        return 2
    print(render(analyze(text or "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
