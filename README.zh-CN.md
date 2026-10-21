# Zotero 10 本地插件

[English](README.md) · MIT · 独立社区维护版

面向 Codex 等智能体宿主的插件：检索文库、修改原笔记、上传存储附件、管理分类标签、
读取批注、保存检索、全文索引、导入导出与引用。基于 OpenAI Zotero 0.1.2 扩展；
安装在智能体宿主中，不是装进 Zotero 的 XPI 扩展。

## 安装与使用

需要 Python 3.10+、本地 Zotero 和支持插件或 Agent Skills 的宿主。无需额外 Python 库。
官方本地 API 写入需要 Zotero 10+；先按实际客户端版本检查功能，必要时在 Zotero 设置里
启用本地 API。

从 [Releases](https://github.com/YkxbGcl2001/zotero-10-local-plugin/releases) 下载并解压 source ZIP，
或克隆仓库。支持插件市场的 Codex CLI 可以运行：

```sh
codex plugin marketplace add YkxbGcl2001/zotero-10-local-plugin
codex plugin add zotero-10@research-local
```

市场标识是 `research-local`；若已使用同名的其他市场，可改用下面的独立 Skill 安装，避免冲突。
支持导入目录的宿主可选择 `plugins/zotero-10`，或解压 plugin ZIP。安装后新建聊天，
选择 Zotero 10。发现与安装能力取决于宿主版本。

也可在解压后的源码目录执行 `python3 scripts/install_skill.py`，将完整 Skill 安装到
`~/.agents/skills/zotero-10`；使用 `--dest` 指定其他宿主的技能目录，如旧版
`~/.codex/skills`。安装器不会覆盖已有目录，也不修改全局配置。

只读检查：

```sh
python3 plugins/zotero-10/skills/zotero-10/scripts/zotero10.py status --json
python3 plugins/zotero-10/skills/zotero-10/scripts/zotero10.py --help
```

写入前由 Zotero 自己弹出授权窗口，由你选择允许或始终允许。附件多步骤上传需要持久授权。
密钥只存在本机私有状态目录，不随插件发布。写命令的 `--yes` 表示执行已经得到用户授权的任务。
发生版本冲突会停止并报告，不跳过保护；不会删除外部原 PDF，也不会直接编辑数据库。

## 验证与来源

在仓库根目录执行：

```sh
python3 -B -m unittest discover -s plugins/zotero-10/tests -v
python3 -B scripts/build.py
```

30 项测试使用模拟 HTTP 和临时文件，不触碰真实文库；不能据此称真实写入已验证。
发布检查不写文库、不重启 Zotero。macOS 做过本地使用核查；Windows/Linux 的路径支持
已实现，但本次没有实体系统测试。桌面专属功能及第三方扩展边界见
[功能表](plugins/zotero-10/skills/zotero-10/references/features-and-compatibility.md)。

source ZIP 包含源码、测试、安装器、构建器、市场清单与说明；plugin ZIP 包含双清单、
全部运行脚本、引用资料和图标。两者均不包含密钥和文库数据。
[第三方来源](THIRD_PARTY_NOTICES.md) 保留 OpenAI 署名，采用 [MIT 许可](LICENSE)。
