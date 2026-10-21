# Zotero 10 功能与兼容性总表

基准为2026-10-11官方发布记录的10.0.6。这里覆盖官方帮助目录的主要使用模块及10.0新增功能；不是把整站每一篇排错文章复制到插件，也不宣称所有桌面按钮都已有外部接口。

“后台”指本插件已有命令或受版本校验的通用JSON操作；“指导”指提供官方工作流与边界，不能当作已经实现后台调用。用户要求执行时仍需核对目标、授权和结果。

## 收集、整理与写作

|模块|新版能力|关键说明与官方来源|
|---|---|---|
|书目、作者、期刊、学位论文、Extra字段|后台读、创建、PATCH更新；动态schema核对|[Adding Items](https://www.zotero.org/support/adding_items_to_zotero)、[类型字段](https://www.zotero.org/support/kb/item_types_and_fields)。作者顺序和单/双字段模式应根据原文核对；缺失元数据不补造。|
|DOI、ISBN、PMID、arXiv、ADS标识符|文献检索/元数据核对及导入流程；原生魔棒属于客户端功能|不要把import-bibtex命令说成能自动触发魔棒。优先出版社或标识符权威来源，再验证导入结果。|
|网页保存、浏览器Connector、网站translators|保留Connector导入；浏览器抓取按连接能力另行处理|元数据网页通常优于直接PDF；普通网页可创建webpage，snapshot是独立附件。|
|PDF元数据识别、Find Full Text|官方工作流指导|识别会向Zotero服务发送PDF前几页文本；不是纯离线。10.0.6修复Find Full Text站点识别/服务器错误停滞。不承诺本地API提供元数据识别或自动寻找全文路由。|
|RIS/BibTeX导入、从其他管理器迁移|保留导入命令与导入前核对|Mendeley/EndNote等工具的大范围迁移走官方对应流程；不把新导入认作已有条目合并。|
|分类树、子分类、多分类归属|后台创建、修改、读取、分配|分类相当于播放列表，同条目入多个分类不复制PDF。移出分类与删除条目分开。|
|标签、自动标签、颜色标签、emoji|条目标签后台读写；颜色/排序设置指导|set-tags完整替换列表；保留不应删的自动标签。色标设置不伪装成普通tag值。|
|关联文献|relate-items双向关系|保留其他关系；只能用正确文库URI，不凭名字构造错误用户ID。|
|疑似重复、原生Merge|后台列候选；原生合并指导|候选不是完整原生重复算法；合并保留分类、标签、附件及Word引文关系，不能用删父条目替代。|
|回收站、恢复、永久删除|trash-item/restore-item/delete-item|移入回收站可恢复；永久删除必须明确要求，不承诺Undo。|
|中文搜索、全部字段、全文筛选|query及保留search|10版重音/排版字符不敏感，CJK短语检索与全文检索改善；使用当前引擎，不自己重建索引表。|
|保存检索、嵌套布尔逻辑|读写保存检索与其结果；动态conditions|10版groups/resultLevel，支持item/attachment/note/annotation层级；旧required/fulltextWord不能继续用。|
|排序、多分类/多文库选择|API排序与明确文库逐次查询；界面多选指导|跨库对象key不全局唯一，命令必须指定library；不能把多选后的第一行当全部目标。|
|子笔记、独立笔记、三段式用途笔记|原笔记更新、创建、追加、父归属与标签|修改优先保留key；完整HTML替换前先读原文；不要删除图片/引用属性。|
|笔记图片、嵌入引文、引用来源链接|保留已有HTML；复杂嵌入功能指导|不能将图片attachment直接当普通HTML字符串上传；普通JSON笔记写入不等于原生注释转笔记全过程。|
|PDF/EPUB/HTML文档附件|stored文件后台上传、查重、归属、原文件导出|文件实际归属和SHA-256核查；不同版本分别挂载，同一文件不重复导入。|
|stored与linked文件、文件改名|stored上传已实现；linked和改名走官方流程或验证后的内部操作|linked不走文件同步，也不支持群组共享；API中的filename只能是纯文件名。不能移动storage目录绕过Zotero。|
|PDF批注|annotations读取；通用JSON可更新已核查批注字段|父对象是附件；不要凭文本猜坐标。原生高亮/区域绘制按阅读器；不要改变PDF页序破坏批注定位。|
|批注到笔记、带批注PDF导出|获取批注数据与笔记整理；原生导出指导|Zotero批注存在数据库，export-file复制原PDF不会将它们嵌入。[官方解释](https://www.zotero.org/support/kb/annotations_in_database)。|
|全文索引、OCR结果|读取索引、everything查询，write-fulltext写核验文本|支持PDF/EPUB/HTML/纯文本，Word不自动有全文。索引不全不能宣称已通读全文；无文本扫描件先OCR。|
|参考文献、CSL格式、语言|citations与导出；CSL安装/样式维护指导|按用户指定格式，不猜GB/T样式ID；引用样式和应用界面语言不同。|
|LaTeX/Markdown、BibTeX引用键|保留cite/sync-bib/export-bibtex|Zotero对象key≠BibTeX键；BibTeX导出不保证Better BibTeX独有功能。|
|Word/LibreOffice/Google Docs动态引用|官方工作流指导；不改造成普通文本冒充动态字段|新引用预览面板属于10版客户端；Unlink Citations不可恢复，仅按明确要求在最终副本处理。|
|格式导出、文献报告|新增多格式export-library与report|元数据导出不是全库/附件备份；报告包括作者、元数据、子笔记和附件索引。|

## Zotero 10 新功能与内部接口变更

以[10版发布记录](https://www.zotero.org/support/changelog)和[10版开发文档](https://www.zotero.org/support/dev/zotero_10_for_developers)为准。

|新增或变化|对本插件的处理|
|---|---|
|新版高级检索嵌入主窗口、嵌套条件组、选择结果层级、新条件|更新指导和保存检索JSON流程；旧帮助“独立窗口/不能多文库”与10版冲突时标明过时。|
|多分类/保存检索/文库同时选择|任何内部JS用plural getters；本插件日常API明确library和key，不依赖当前界面选择。|
|批量编辑多条目|write-items，最多50条，逐条检查失败及读回；不能把HTTP200当整批成功。|
|Undo/Redo|官方JS的saveTx需undoAction才纳入历史；本包API更新不能假称都有Ctrl-Z；保留操作receipt及读回核验。创建和永久删除不承诺Undo。|
|Reading Mode：可重排文本、保留图表、跨视图共享批注位置|加入阅读指导；阅读/视觉检查仍结合原始PDF页面，不将重排文本当原版版式。没有后台切换阅读模式命令。|
|Read Aloud：跳过引用/页眉表格等，句子高亮与新版快捷键|加入指导。10.0.6已恢复macOS27本地声音；不把TTS控制认作本地文库API。|
|全文FTS5、CJK短语检索、去重音匹配|使用当前全文引擎；不访问已移除的fulltextWords/fulltextItemWords，内部JS用fulltextContent。|
|Safari Connector更新、PDF JPEG2000渲染、EPUB定位、引文预览|记录版本行为与排错来源；浏览器/阅读器界面功能由原生组件负责，不写假后台入口。|
|Sync设置改名Account|所有新版指导标注Account；尚未更新的通用页面中的Sync名称按旧名理解。|
|local API正式写入、独立本地version、serverID、授权窗口|本包已实现，不再沿用“只读”。浏览器样式请求需官方允许请求头；本辅助程序为Python客户端，不伪装Mozilla浏览器。|
|校验强化：特殊itemType转换、存储filename、WAL数据库|不强制转换普通条目到笔记/附件；stored filename不写完整路径；不直接修改SQLite或复制运行中的主库当完整备份。|
|CookieSandbox移除、HTTP.download返回Response、单选getters与旧窗口移除|仅在需要内部JS时按10版API编写；本包不安装内部执行扩展。|

## 同步、协作、设置与其他模块

- 数据同步与文件同步分开：书目/文本笔记同步不等于PDF已上传。内嵌笔记图片使用文件存储；不将全文读取API说成云存储接口。[Sync](https://www.zotero.org/support/sync)
- 群组为独立文库；API按groups/<id>读写有权限的内容。群组创建、角色与成员管理以及公开发布用官方网站流程，不通过本地写入越过权限。[Groups](https://www.zotero.org/support/groups)
- My Publications是公开分享自己的作品，并涉及许可选择；默认不发布，不将论文筛选导入等同公开分享。[My Publications](https://www.zotero.org/support/my_publications)
- RSS支持URL、OPML、更新频率、已读状态；本包提供官方使用指导，不擅自创建订阅或定时自动化。[Feeds](https://www.zotero.org/support/feeds)
- 备份：元数据导出不是完整备份，数据库在运行时采用WAL。按官方备份流程关闭应用后保存完整数据目录；不要将活跃数据库放进OneDrive同步目录。按需引用[数据目录与备份](https://www.zotero.org/support/zotero_data)，不会为普通笔记更新自动拷贝整库。
- 语言、快捷键、颜色标签、应用排版、存储、WebDAV和CSL样式均按官方设置指导；本包不擅自改设置、不要求额外注册云账号、不管理订阅费用。
- 茉莉花、Better BibTeX、Better Notes及其他第三方插件，先检查其独立接口和版本；Zotero核心API不代表这些插件可被后台触发。移动端/网页端使用与本机接口分开。

## 后续维护

每次用户要求升级或运行版本改变，核对changelog、10版开发页和涉及功能的官方页；记录日期与已测试版本，不宣称今天的静态文档永远最新。对官方文档也要辨别过时段落，不能照搬旧截图或菜单名。
