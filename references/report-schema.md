# 结构化 HTML 报告合同

## Metadata

- 标题：选品报告内容结构与渲染器
- 维护者：amazon-selection-research contributors
- 状态：active
- 更新：2026-10-22
- 版本：1.1.0

## 用法

```bash
python3 scripts/render_report.py assets/example-report.json /tmp/example-report.html
python3 -m unittest discover -s tests -v
```

Python 标准库即可运行。输出是包含 CSS 和少量导航脚本的单文件 HTML；不依赖网络字体、图标库或外部 JavaScript。外部来源链接仅在读者点击时打开。

**这不是 Markdown 转 HTML 工具。** 先选结论、安排阅读顺序、决定合适的图表，再填写 JSON。示例明确标注为虚构，不能搬用示例数字。渲染器负责结构与输入校验，无法替代来源核验或真人视角的 UI 审核。

## 根结构

```json
{
  "title": "类目与研究主题",
  "subtitle": "一句话说明本报告帮助做什么决定",
  "metadata": {"owner":"维护者","status":"判断状态","updated":"YYYY-MM-DD","version":"报告版本"},
  "sections": [],
  "appendix": [],
  "links": [{"text":"飞书文字报告","url":"https://example.com/report"}]
}
```

`sections` 为 2–9 节。`appendix` 可省略，只接受默认折叠的 `details`。`links` 可省略。仅虚构示例设置 `fictional_example: true`，它会在首页显示醒目声明。

## 每节

```json
{
  "id":"competition",
  "headline":"成熟评价积累增加进入难度，但并非绝对壁垒",
  "nav_label":"竞争压力",
  "subtitle":"同规格观察购买活动与评价积累，区分事实与判断。",
  "key_points":["关键结论一","关键边界二"],
  "blocks":[]
}
```

- `id`：唯一小写 ASCII slug，不超过 41 字符。
- `headline`：结论型标题，最多 70 字符；`nav_label` 最多 24 字符。
- `subtitle`：最多 160 字符；不要在副标题塞满方法解释。
- `key_points`：1–4 条，每条最多 160 字符。用于可直接扫读的结论和会改变决策的重要限制。
- `blocks`：1–8 块，至少一块默认可见的分析图表／卡片／行动流程。
- 不支持把长段落数组塞进页面。补充解释放 `details` 中，关键结论、价格数字、同规格比较和重要边界不能全部折叠。

## 内容块

所有内容块可选 `title`。除 `details` 外可选 `note`，最多 240 字符，显示为可见的提醒。文本只支持纯文本，不解释 Markdown 或内嵌 HTML。

| type | 用途 | 必填字段 |
|---|---|---|
| `cards` | 2–4 个候选方向／决策 | `items`：每项 `title`、`verdict`、`points`（1–4 条） |
| `comparison` | 同规格默认可见比较 | `columns`（2–6列）、`rows`（1–24行）、`source` |
| `ranges` | 有真实数字和样本量的区间图 | `unit`、`source`、`rows`：每项 `label/low/median/high/n` |
| `issues` | 定性问题→证据→产品行动 | `source`、`items`：每项 `problem/evidence/action` |
| `steps` | 下一步验证与责任 | `items`：每项 `title/action` |
| `illustration` | 解释场景、产品结构或使用路径 | `path/alt/caption/source/label`；本地 PNG/JPEG，内联后离线可读 |
| `details` | 补充依据，默认折叠 | `title`、`blocks` |
| `notes` | 折叠后的说明与来源 | `items`：纯文本或链接；仅可出现在 `details` 内 |

### 比较表

```json
{"type":"comparison","title":"商业对标","columns":["商品","规格","价格"],"rows":[[{"text":"商品A","url":"https://example.com/a"},"同一规格","$20"]],"source":"观察日期与样本范围","note":"评分可能在同父体间共享，不重复累计。"}
```

需要在手机同时比较两款商品时，添加 `"mobile_layout":"compact"`，并转置为三列：`字段 | 对手A | 对手B`；行写规格、价格、购买提示、评分与定位，单元格保持简短。此模式手机保持三列矩阵，不转成长卡；只接受三列。优先把同规格最关键的两款并排，其余对手另列或放折叠明细。不要把多商品六列大表强塞入手机。

表格每行长度必须与列数一致。桌面为表格；手机以带字段名的行卡展示，避免横向拖动。首列应为可识别的商品或方向。主线只选最有决策价值的几行，全量明细放附录，别把 24 行上限当推荐行数。

### 区间图

```json
{"type":"ranges","title":"同规格价格分布","unit":"美元","source":"来源和观察日期；n为独立商品数","rows":[{"label":"规格A","low":12,"median":19.5,"high":28,"n":8}],"note":"这是供给价格分布，不等于需求份额。"}
```

低值／中位／高值必须是有限数字且有序，n 为正整数。`null`、字符串数值、NaN、Infinity 均拒绝，缺失值不会变零。图上默认显示所有数字、单位、样本数、来源与共同刻度。只有一个观测可用 `n:1` 且三个数相同；不要伪造区间。没有可比数值时用 `issues`、`steps` 或比较表，不能为了有图而估数。

### 定性问题

```json
{"type":"issues","title":"用户问题与产品要求","source":"原文来源范围；不能推断发生率","items":[{"problem":"卷边影响日常通行","evidence":"说明具体原文或主题证据，并标明国家、变体等限制。","action":"明确需要改变什么，以及如何验证改善。"}]}
```

`problem` 写出用户影响，`evidence` 最多 250 字符，`action` 最多 200 字符。缺少可靠分母时不生成占比或排名。

### 折叠补充

```json
{"type":"details","title":"查看同父体去重和样本边界","blocks":[{"type":"notes","items":["补充解释。",{"text":"可追溯来源","url":"https://example.com/source"}]}]}
```

原生 `<details>` 默认关闭，键盘可用。可在内部放比较表，但不要把核心比较藏在这里。支持最多两层嵌套，通常一层足够。附录也采用此结构。

### 配图

```json
{"type":"illustration","title":"进门后的使用场景","path":"assets/entry-scene.png","alt":"犬只进门经过地垫的场景示意","caption":"帮助理解放置位置，不代表实际吸水或清洁效果。","source":"AI生成示意，非竞品实拍","label":"示意图"}
```

- 只读输入 JSON 所在目录及其子目录的 PNG/JPEG，每张最多 4 MiB；拒绝绝对路径、路径逃逸和 SVG。图片缺失明确报错，不能发布破图。
- `alt`、`caption`、`source` 和 `label` 必填；文件被内联为 data URI，脚本不抓取远程图片。
- 配图应解释用户场景、操作路径或产品结构。不要堆装饰图。AI示意不能当实测证据；来源和“示意图”标签默认可见。
- 插图不能单独满足每章的分析块要求；对应的判断、比较或行动仍需默认可见。
- 直接调用 Python API 时用 `render(data, asset_root=Path(...))` 指明 JSON 所在目录；CLI 自动采用输入目录。

## 输入与交互约束

- 所有外部输入按文本转义；仅接受绝对 http(s) 来源链接，禁止凭证、危险协议和控制字符。输入不能注入 HTML、样式或脚本。
- 原生锚点保留浏览器前进后退与复制深链接。粘性导航动态测高，为标题预留空间；脚本不替换历史记录。
- 图表不依赖悬浮提示；比较数字默认可见；不提供无用的下载／打印／全局折叠按钮。
- 生成后仍必须实测桌面、320px 手机、折叠、键盘、深链接与前进后退；同时用真实阅读任务检查是否能快速找到候选、证据、限制和下一步。

## Change Log

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-22 | 1.1.0 | 增加标准库渲染器、结构化内容合同、虚构示例、本地PNG/JPEG内联配图与安全／语义校验；禁止仅用长段落包装 HTML。 |
