# 官方文档核对记录

核对日期：2026-10-11。官方changelog显示最新发布版10.0.6（2026-10-07）；本机运行版本同为10.0.6。不是按“Zotero 10”名称推断所有未来小版本兼容。

本次读取了42个官方文档页面/入口，覆盖帮助首页主要功能目录、10版发布与开发变更、API、JavaScript、附件/批注/笔记/引用/同步/协作/备份。候选URL中不存在的旧路径没有写入功能引用，已用有效页面或10版发布记录替代。

## 已纠正的冲突

- 旧Codex插件说本地API只读：10版已支持官方写入和授权。
- 通用Searching页仍说独立高级检索窗口、不能多文库选择：以10版主窗口高级检索、多选和嵌套组为准。
- Settings/Sync页有旧截图和旧名：10版改为Account，不把旧菜单名说成当前布局。
- 旧JS单选getters、fulltextWord、CookieSandbox、advancedSearch.xhtml及索引表：按10版开发文档更新，不生成过时内部脚本。
- 附件“导出原文件”与“导出嵌入批注”分别处理；新批注不自动写进原PDF。
- API实例ID、本地版本号与云端版本区别，401/412/428和多阶段文件上传按当前实现处理。
- 文献元数据导出不等于完整备份；上游只提供引用键插入，不等于Word动态字段。

## 官方来源

- [start](https://www.zotero.org/support/)
- [changelog](https://www.zotero.org/support/changelog)
- [quick_start_guide](https://www.zotero.org/support/quick_start_guide)
- [adding_items_to_zotero](https://www.zotero.org/support/adding_items_to_zotero)
- [retrieve_pdf_metadata](https://www.zotero.org/support/retrieve_pdf_metadata)
- [collections_and_tags](https://www.zotero.org/support/collections_and_tags)
- [searching](https://www.zotero.org/support/searching)
- [related](https://www.zotero.org/support/related)
- [duplicate_detection](https://www.zotero.org/support/duplicate_detection)
- [notes](https://www.zotero.org/support/notes)
- [pdf_reader](https://www.zotero.org/support/pdf_reader)
- [file_sync](https://www.zotero.org/support/file_sync)
- [sync](https://www.zotero.org/support/sync)
- [word_processor_plugin_usage](https://www.zotero.org/support/word_processor_plugin_usage)
- [creating_bibliographies](https://www.zotero.org/support/creating_bibliographies)
- [feeds](https://www.zotero.org/support/feeds)
- [groups](https://www.zotero.org/support/groups)
- [preferences](https://www.zotero.org/support/preferences)
- [dev/client_coding/javascript_api](https://www.zotero.org/support/dev/client_coding/javascript_api)
- [dev/web_api/v3/local_api](https://www.zotero.org/support/dev/web_api/v3/local_api)
- [dev/web_api/v3/basics](https://www.zotero.org/support/dev/web_api/v3/basics)
- [dev/web_api/v3/write_requests](https://www.zotero.org/support/dev/web_api/v3/write_requests)
- [dev/web_api/v3/file_upload](https://www.zotero.org/support/dev/web_api/v3/file_upload)
- [dev/web_api/v3/fulltext_content](https://www.zotero.org/support/dev/web_api/v3/fulltext_content)
- [dev/web_api/v3/types_and_fields](https://www.zotero.org/support/dev/web_api/v3/types_and_fields)
- [dev/zotero_7_for_developers](https://www.zotero.org/support/dev/zotero_7_for_developers)
- [dev/zotero_10_for_developers](https://www.zotero.org/support/dev/zotero_10_for_developers)
- [attaching_files](https://www.zotero.org/support/attaching_files)
- [moving_to_zotero](https://www.zotero.org/support/moving_to_zotero)
- [sorting](https://www.zotero.org/support/sorting)
- [styles](https://www.zotero.org/support/styles)
- [reports](https://www.zotero.org/support/reports)
- [my_publications](https://www.zotero.org/support/my_publications)
- [zotero_data](https://www.zotero.org/support/zotero_data)
- [connector_preferences](https://www.zotero.org/support/connector_preferences)
- [supported_languages](https://www.zotero.org/support/supported_languages)
- [plugins](https://www.zotero.org/support/plugins)
- [kb/annotations_in_database](https://www.zotero.org/support/kb/annotations_in_database)
- [preferences/export](https://www.zotero.org/support/preferences/export)
- [preferences/search](https://www.zotero.org/support/preferences/search)
- [preferences/advanced](https://www.zotero.org/support/preferences/advanced)
- [kb/item_types_and_fields](https://www.zotero.org/support/kb/item_types_and_fields)

## 本机实现交叉核对

核对了安装包内server_localAPI.js的授权、PATCH、批量对象、文件三阶段上传、全文、标签与保存检索路由，以及10.0.6的版本头。没有向真实文库发出测试写入。新增代码在隔离的模拟客户端验证；运行中的只读检查另行记录。

## 来源与版本

上游：OpenAI Zotero 0.1.2，原包声明MIT许可。本地fork插件标识zotero-10、显示名Zotero 10、版本1.0.0。不是Zotero官方扩展或OpenAI发布的新版本。保留上游Python读/引用/导入辅助程序，新增zotero10.py与新版工作说明。
