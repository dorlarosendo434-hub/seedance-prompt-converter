# Seedance Prompt Converter

把 Seedance 2.0 风格的视频提示词诊断并重构为更适合 Seedance 2.5 的结构化导演简报。

本仓库根据一份豆包公开分享页中的项目结构、规则说明、示例输出与测试结果进行功能等价还原。分享页没有公开写文件时的原始源码参数，因此本仓库不是字节级复制版本；所有规则和脚本均已重新整理并在本地验证。

## 功能

- 诊断空洞形容词、画质词堆砌、风格冲突和运镜冲突
- 检查负面词、时间线、动作密度和主体锚点
- 检查参考素材职责与声音括号路由
- 按主体、动作、场景、风格、镜头、声音六槽位重构
- 输出诊断结果、可复制提示词和逐条改动说明

## 安装

将仓库克隆到 Codex Skills 目录：

```bash
git clone https://github.com/dorlarosendo434-hub/seedance-prompt-converter.git ~/.codex/skills/seedance-prompt-converter
```

其他支持 `SKILL.md` 的 Agent 环境，可将整个目录放入其个人 Skills 目录。

## 使用

在对话中直接说：

```text
帮我把这条 Seedance 2.0 提示词转换成 2.5：<你的提示词>
```

也可以单独运行诊断脚本：

```bash
python scripts/diagnose_prompt.py "一个美丽的女子缓缓走来，电影感，8K，不要模糊。"
python scripts/diagnose_prompt.py --file prompt.txt
```

脚本无第三方依赖，支持 Python 3.9 及以上版本。

## 目录

```text
seedance-prompt-converter/
├── .gitignore
├── LICENSE
├── README.md
├── SKILL.md
├── references/
│   ├── conversion-rules.md
│   └── examples.md
└── scripts/
    └── diagnose_prompt.py
```

## 注意

AI 视频平台的模型能力、参数和提示词语法可能更新。把本 Skill 当作结构化创作与迁移工具，并用同素材、同时长的 A/B 测试验证具体模型效果。

## 还原来源

- [豆包公开分享页：Seedance 2.0 与 2.5 差异及提示词转换 Skill](https://www.doubao.com/thread/xx6t7f6AMzVrvirKg)

## License

[MIT](LICENSE)
