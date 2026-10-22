# 双报告与飞书交付

维护者：Hao Wu · 状态：active · 更新：2026-10-22

## 写作与页面生成前必须完成

先读[可读性合同](readability.md)，完成主线／详情／附录取舍。文字报告必须自身易读；不能把“聊天简短”误用于删减必要分析，也不能把完整性误解为连续大段。HTML采用包内[结构模型](report-schema.md)与渲染器，默认subtitle＋折叠详情；核心对比、业务含义与必要限制直接可见。

两版来自同一核验数据与结论，不手填两套数字。数字审核、文字阅读、HTML内容阅读和实际交互分别验收；不能只有技术检查就发布。完整样本与采集排障放附录。每张图保留单位、日期、分母、来源和一句解读；计数不可靠时做定性关系图，不造比例。

保留Metadata（标题、维护者、状态、更新时间）、来源与Change Log。刷新先读线上最新内容并与本地基线比较，合并用户修改。以下发布顺序不改变内容质量门槛：文字先完成并验收，再写入；HTML也须完成阅读及交互验收后才上传。不得上传空壳占位或未经审核的草稿冒充完成。

## 发布步骤

先读`setup.md`完成目标路由；每条业务命令显式带`--profile`和`--as`。以下是已验证CLI命令形态示例，实际执行先看本机`--help`；占位值必须来自当前用户和实际返回，不照抄。

1. 新建文字报告为用户所指定Wiki目录的子节点：

```bash
lark-cli docs +create --profile '<已验证profile>' --as user --parent-token '<目录wiki token>' --title '<品类>选品调研' --doc-format markdown --content @report.md
```

2. 已有文字报告：先fetch并合并，再用对应更新方式。全文重写仅在已授权更新该报告且用户修改已合并时使用：

```bash
lark-cli docs +fetch --profile '<已验证profile>' --as user --doc '<真实doc token>' --format json
lark-cli docs +update --profile '<已验证profile>' --as user --doc '<真实doc token>' --command overwrite --doc-format markdown --content @report.md
```

若用户只给父目录但要求更新，先用案例已存链接或列出目录子节点查找现有两份报告。唯一匹配且内容核实后沿用；存在同名历史版本或无法唯一定位时只问应更新哪份，不猜、不新建替代。原生列节点接口先查schema。

写后回读关键结论、数字和图片；Markdown本地图按本机文档导入指南处理，避免把磁盘路径当成线上图像。

3. 文字成功后生成并审核HTML。上传到用户目录的下一级，而不是覆盖目录正文：

```bash
lark-cli drive +upload --profile '<已验证profile>' --as user --file report.html --wiki-token '<目录wiki token>' --name '<品类>选品调研.html'
```

更新既有HTML时添加返回的`--file-token`以保持原链接；若文字与HTML指定不同目录，分别沿用。不要为一次更新重复建节点。对不确定的写入结果先查目标再重试。

4. 下载并核对字节／哈希；核Wiki父子关系与实际URL。不要假定上传HTML等于托管网站，飞书可能提供附件预览或下载；只报告实际可访问的交付方式。

```bash
lark-cli drive +download --profile '<已验证profile>' --as user --file-token '<上传返回的file token>' --output downloaded-report.html
```

两份报告的发布状态分别记录：`text_version/text_status`与`html_version/html_status`。文字已更新但HTML生成、审核或上传失败时，标记`partial`并保留新版文字与旧HTML对应版本，简短告诉用户当前哪份已更新和剩余动作；不称双版完成，不自动回滚用户内容。恢复时先回读远端状态，继续失败步骤而不重复新建。仅两份验证成功才把案例标为完成。

如果目录权限或文件类型受限，保留本地结果，指出具体阻塞；不能悄悄换到个人云盘或公开网站。用户允许在指定目录交付即覆盖这些正常写入，无需每步重复申请许可。

最终聊天只给两份链接、最重要的结论变化，以及会影响决策的未解决缺口。将host/profile/identity、验证结果和是否刷新令牌记在本地case状态，不公开凭证。

## Change Log
- 2026-10-22：1.1.0，写作前强制读取可读性合同，使用结构化渲染器并分开验收文字与HTML。
- 2026-10-22：建立双报告顺序、渐进披露、UI复核与原位更新规则。
