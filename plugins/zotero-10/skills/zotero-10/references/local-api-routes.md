# Zotero 10 本地 API 与命令说明

核对：2026-10-11；官方当前稳定版10.0.6。本地API版本3，不要把插件版本1.0.0当成Zotero客户端版本。

## 连接与权限

基址 `http://127.0.0.1:23119/api/`（也可localhost）；仅本机loopback。读请求不认证。所有写请求要求 `Zotero-Server-ID` 和官方本地API密钥；API密钥不等于云账号密钥。授权端点 `POST /api/local/authorize`，JSON为 `{"appName":"Codex Zotero 10"}`，由用户在官方窗口选择Allow/Always Allow/Deny。不得绕过窗口或从其他程序提取登录凭据。

`GET /api/`返回实例ID。实例变化后重新定位文库和对象；本地version与云端version无关。写入操作使用PATCH和对象version；401需重新授权，412需重新读取、审查目标，409为锁定，428为缺少必需前置条件。连接中断不自动重发创建请求。

设置允许通信的路径：Settings → Advanced → “Allow other applications on this computer to communicate with Zotero”。Zotero10的同步设置页叫Account，旧帮助中的Sync指同一类配置，不能沿用为当前准确菜单名。

## 路由

默认文库 `/api/users/0`；群组使用 `--library groups/<id>`。用户只能编辑有权限的群组数据，群组成员/组织设置并非本地可写。

|资源|读|10+写|
|---|---|---|
|items|列表、top、trash、key、children、筛选、引用及导出|POST批量创建/更新，PATCH/PUT对象，DELETE|
|collections|目录、子目录、目录内条目|POST创建/更新，PATCH/PUT对象，DELETE|
|searches|条件、指定保存检索的items|POST创建/更新，PATCH/PUT对象，DELETE|
|tags|标签列表及单标签|可删除标签；条目标签通过item.tags修改|
|schema/itemTypes/itemFields/itemTypeFields/itemTypeCreatorTypes/creatorFields|动态字段、类型和创建者定义|只读|
|items/key/fulltext|已索引内容与统计|PUT写已核验索引文本；库fulltext支持批量写（官方上限10）|
|items/key/file/view/url|实际本机文件URL|该URL路由不用于文件写入|
|items/key/file|文件内容定位|三阶段上传；不支持本地二进制差分PATCH|
|groups|可见群组信息|成员和群组设置只读|

本地不支持Atom，不采用云S3上传地址，也不要求云API授权。某些云API路由（例如新条目模板）不能假定本地存在；字段以本地schema核对。

## 命令

统一运行 `python3 <skill-dir>/scripts/zotero10.py <command>`，完整参数看`--help`或`<command> --help`。

- status/auth-status：版本、API实例、是否缓存写凭据，不输出密钥。
- authorize：显示官方授权窗口。forget-authorization：忘记本辅助程序的本地密钥，不冒充撤销服务器授权。
- get-item KEY：读取一个对象。
- query：全文/标题作者年份、类型、标签、分类、回收站、排序筛选。
- schema/item-types/item-fields/creator-fields/type-fields TYPE/creator-types TYPE：实时类型与字段。
- annotations ATTACHMENT_KEY：读附件批注，不把书目父条目误作批注父对象。
- update-note KEY --html FILE --mode replace|append|prepend --version N --yes：保留笔记key更新HTML。
- update-item KEY --file JSON --version N --yes：PATCH部分字段。JSON不能覆盖key、version、dateAdded。
- create-note PARENT --html FILE --yes：新增子笔记；独立笔记用write-items。
- write-items/write-collections/write-searches --file JSON --yes：数组，1—50个记录。更新已有对象要有已审查version；新对象可给有效新key，或由辅助程序生成。输出逐条读回与恢复receipt。
- set-collections KEY COLLECTION... / set-tags KEY TAG... --version N --yes：完整替换列表，执行前先保留应保留成员。
- update-collection/update-search KEY --file JSON --version N --yes：部分修改目录或保存检索。
- saved-searches/saved-search-items KEY：读取保存检索与匹配结果。
- reparent-item CHILD PARENT --yes：移动笔记或附件到已有父条目；批注必须归属文档附件。
- relate-items A B --yes：给两个对象增加双向dc:relation，保留其他关系；需要有效文库身份。
- trash-item/restore-item KEY --version N --yes：修改deleted标志。delete-item KEY --permanent --yes：永久删除，不能假称可撤销。
- write-fulltext ATTACHMENT_KEY --file JSON --yes：必须含content及准确非负索引统计；用途不是写论文分析或AI摘要。
- attach-file PARENT FILE --title TITLE --yes：导入stored附件，不删源文件。支持 `--resume-key KEY` 显式恢复未完成上传。
- export-file ATTACHMENT_KEY --out FILE：复制原始附件，SHA-256校验，拒绝覆盖现有文件；不嵌入数据库批注。
- export-library --format bibtex|biblatex|ris|csljson|csv|mods|rdf_zotero --collection KEY --out FILE：元数据导出，不能视为全库备份。
- duplicate-candidates：按DOI或归一标题列疑似组；不自动合并，不等同原生重复算法。
- report KEYS... --out FILE：生成元数据、作者、附件信息与子笔记HTML报告；不是Word动态参考文献。

上游读/导入命令原样保留并转发：enable、disable、restart、probe、inventory、collections、tags、groups、search、export-bibtex、sync-bib、citations、children、fulltext、file-url、cite、selected-target、import-bibtex、import-ris。它们默认个人文库；群组检索优先用新版`--library groups/<id> query`等命令。

## 附件完整流程

1. 核对父条目和源文件，按源SHA-256检查该父条目已有stored附件，完全相同返回alreadyPresent；接受稿与正式版可能不同，不按标题硬删。
2. 上传有多次写请求，在创建附件前检查持久授权。建立imported_file附件元数据；filename只能是纯文件名，不能塞入绝对路径。
3. POST file端点，以MD5、文件名、字节数、毫秒mtime请求上传，传If-None-Match或If-Match。返回地址必须是同一个本机实例的 `/api/local/uploads/<key>`。
4. POST文件原始内容到返回地址，随后POST file端点登记uploadKey。
5. 获取file/view/url并核对存储文件SHA-256。确认后才可按用户授权删除外部源PDF。

中断时留源文件和receipt，说明已经创建的attachmentKey；不重新创建第二个父条目或附件。缓存密钥或批量请求receipt仅在本机私有目录，密钥永不输出。创建/永久删除不承诺Zotero界面Undo；本地API写入也不自动承诺进入Undo历史。

## 官方来源

- https://www.zotero.org/support/dev/web_api/v3/local_api
- https://www.zotero.org/support/dev/web_api/v3/write_requests
- https://www.zotero.org/support/dev/web_api/v3/file_upload
- https://www.zotero.org/support/dev/web_api/v3/fulltext_content
- https://www.zotero.org/support/dev/web_api/v3/types_and_fields
- https://www.zotero.org/support/dev/zotero_10_for_developers
