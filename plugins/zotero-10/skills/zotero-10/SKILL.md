---
name: zotero-10
description: 管理 Zotero 10 桌面文库；通过官方本地 API 检索、修改原笔记、管理附件、分类、标签、保存检索、批注和全文索引，导入导出及生成引用。用户提到 Zotero、文献整理、笔记、PDF附件或引用时使用；界面专有功能和第三方插件须按能力边界处理。
---

# Zotero 10

这是基于 OpenAI Zotero 0.1.2 的个人本地版，不是 Zotero 官方扩展，也不是安装到 Zotero 内的扩展。基准：2026-10-11核对官方10.0.6（2026-10-07发布）、10版开发变更和功能帮助。原有检索、导出、引用和Connector导入保留；新增官方本地写入。若旧 Zotero skill仍说“本地API只读”，对已确认的10+客户端使用本skill的新版说明。

## 入口与验证

本skill目录下的 `scripts/zotero10.py` 是统一入口，用系统 `python3` 即可，无需第三方依赖。

```bash
python3 <skill-dir>/scripts/zotero10.py status --json
```

- 先检查实际运行版本、API连通性、`Zotero-Server-ID`、授权是否已缓存。不要靠插件名推断客户端版本。
- 10+的 `/api/` 支持读写；较旧版本仍可检索和Connector导入，但拒绝本地写入，不宣称任何版本都是只读。
- 只在用户要求使用Zotero而API关闭时，用保留的 `enable --restart`。不要为了读取或测试重启应用。
- 检索、字段类型和JSON架构以运行中的 `/api/schema` 等为准；跨实例/云端的版本号不能混用。
- 用户要求新功能、方法发生冲突或Zotero版本变化时，先读[功能与兼容性总表](references/features-and-compatibility.md)，再打开该功能的官方页。通用帮助有些尚未更新，优先级为本机实现与运行验证、10版变更/开发文档、最新API页、旧通用帮助。

## 外部自动化优先走官方本地 API

读请求不需要密钥。写入授权与zotero.org云API密钥不同：

```bash
python3 <skill-dir>/scripts/zotero10.py authorize --app-name 'Codex Zotero 10'
```

Zotero会弹出其官方授权窗口，用户选择Allow、Always Allow或Deny。普通操作已经获得用户授权时，不重复请求聊天确认；但不能代替用户批准这个官方窗口。一次授权只消费一次写请求，可能在版本冲突时也被消费。附件多步骤上传需要持久授权；辅助程序在创建附件前检查，不在操作到一半时反复弹窗。不要强迫用户选择持久授权，若选择一次允许，应按实际步骤与用户协调。

密钥仅存于本机私有目录 `~/.codex/zotero10/authorizations/`，按服务器实例与地址隔离，文件0600；不打印、不写进笔记、不放进插件源码或总文献库。`forget-authorization`仅忘记本辅助程序的缓存；撤销Zotero端已记住的授权使用Settings → Advanced → Clear Write Authorizations。此授权允许访问用户可编辑的文库，并非按Codex账号或单个分类隔离。

所有写命令需要 `--yes`，它表示执行已被用户授权的工作，不是要求每次重新问用户。更新使用当前对象版本和PATCH；412/409/401/428或连接中断时报告准确原因，不盲目重试、不取消版本保护、不转为直接修改SQLite。

## 常规整理

```bash
python3 <skill-dir>/scripts/zotero10.py search '13X' --json
python3 <skill-dir>/scripts/zotero10.py query --q '硫酸镁' --qmode everything --item-type journalArticle
python3 <skill-dir>/scripts/zotero10.py get-item ABCD2345
python3 <skill-dir>/scripts/zotero10.py children ABCD2345 --json
python3 <skill-dir>/scripts/zotero10.py update-note N234ABCD --html reviewed.html --version 12 --yes
python3 <skill-dir>/scripts/zotero10.py attach-file ABCD2345 supplemental.pdf --title '接受稿及补充材料' --yes
```

- 明确父条目、子笔记、附件各自的key。引用用的BibTeX键不是Zotero对象key。
- 修改笔记优先在原key上保存；读取原HTML后构造完整的新HTML，保留原意、引用和来源。`append`适合原样追加，不能替代内容上的合并。不得仅因旧接口限制，默认不停创建补充笔记。
- 需要学位论文用途笔记时，可按用户要求分为三个HTML段落：“主要工作”“学位论文用途”“参考位置”。保持模块换行；段落来自全文核查，不把摘要推测写成实验结论。
- 同一文献用一个父条目，可加入多个collection；同一条目下可以保留正式版、接受稿和补充材料等不同附件。`attach-file`按SHA-256查重并核验最终存储文件；不同版本不得因DOI相同而误删。
- 原PDF转存后是否删除依据用户要求；先确认存储完整、归属正确，再删除外部副本。辅助程序本身不会删除源文件。OneDrive云占位文件不为盘点自动读取下载；全文任务所需文件另行确认。
- 学位论文用thesis类型，核对作者、学校、学位、年份与扉页；未核实字段不补造。DOI/ISBN元数据检索是导入来源工作，不等于本地API自动替你做标识符检索。茉莉花、Better BibTeX等功能不自动等同于Zotero核心API；没有已验证入口时如实说明。
- 分类/标签列表是完整替换，先读取并保留应保留的成员；不要误删其他分类、自动标签、关系。`set-collections`/`set-tags`表示明确的完整列表。
- 疑似重复用 `duplicate-candidates` 初筛后核对全文/DOI/作者版本；它不等于Zotero原生重复检测。正式合并父条目优先使用Zotero的Merge功能，保留引用历史；不得将“搬附件后删除父条目”假称原生合并。
- 合并补充笔记：核对两条HTML，保存原笔记，读回验证，再按用户授权 `trash-item` 处理多余笔记。默认可恢复移至回收站；永久删除仅在用户明确要求时使用 `delete-item --permanent --yes`。

## 完整功能路由

- 检索/排序/批注筛选/字段验证：`query`、`schema`、`item-types`、`type-fields`、`creator-types`、`annotations`。批注的父对象是文档附件；不要只读取书目条目的children就声称读完批注。
- 原笔记、元数据、标签、分类、父子归属和关联：`update-note`、`update-item`、`set-tags`、`set-collections`、`reparent-item`、`relate-items`。
- 批量对象和保存检索：`write-items`、`write-collections`、`write-searches`、`update-collection`、`update-search`、`saved-search-items`。每次至多50对象，检查单个失败，HTTP200不代表整批成功。嵌套条件按10版condition groups/resultLevel和运行中的架构处理。
- 全文：保留 `fulltext` 读取；`write-fulltext`仅在用户确实要导入已核验的OCR/外部索引文本时使用，不能把摘要或AI生成内容伪装成全文索引。支持PDF/EPUB/HTML/纯文本；Word文件不等于可全文索引。
- 附件：`attach-file`、`export-file`。API管理的附件为stored file；导出原文件不等于将Zotero批注嵌入PDF。后者用原生Export PDF或经核验的内部JS，保持区分。
- 参考文献：保留 `citations --style ...`、`export-bibtex`、`cite`；新增 `export-library`（BibTeX/BibLaTeX/RIS/CSL JSON/CSV/MODS/Zotero RDF）、`report`（元数据与笔记HTML报告）。LaTeX/Markdown引用插入不等于Word动态引文字段；Word/LibreOffice/Google Docs仍用对应官方集成。
- 阅读模式、朗读、嵌入批注导出、原生重复合并、RSS订阅、Sync/Account、CSL安装、数据库备份和设置管理：读[功能总表](references/features-and-compatibility.md)，按已验证能力执行或给出准确界面操作；没有后台接口不宣称支持自动调用。用户禁止Computer Use时遵守。
- JS只是剩余内部专用功能的候选路径。当前包不提供任意JS远程执行，不需要给Zotero装执行扩展；不能因“内部JS能做”便声称外部已能调用。确需内部JS时用10版API，避免旧单选getters、`fulltextWord`、`CookieSandbox`、旧advancedSearch窗口及数据库表。

读[API与命令说明](references/local-api-routes.md)了解写入、附件恢复及命令格式。读[官方文档核对记录](references/official-documentation-audit.md)了解核对日期、最新版本和旧帮助冲突。

## 完成验证

报告实际改动和未完成步骤。写操作读回核对目标key、parentItem、分类和内容；上传核对存储文件SHA-256。首次接入授权前可进行只读和隔离模拟测试，但不能写“真实文库写入已测试”。源码保留在个人本地插件目录；缓存安装副本可能被刷新，不直接维护上游缓存。不要混淆本机源码复用与不同账号各自的安装/启用状态。
