# 首次使用与配置引导

维护者：Hao Wu · 状态：active · 更新：2026-10-22

此页供Agent按阻塞项查阅，不整页展示给运营。每步只说“现在做什么、完成后我检查什么”。已配置就验证并复用，不重装、不改全局默认账号。

## 1. Bright Data MCP

先在当前客户端发现Bright Data工具。若不存在，先从当前环境识别AI客户端，未知才询问用户，再读取该客户端当前官方连接指南；不同客户端配置入口不同，不猜菜单。

> 你现在用的是 Codex、Claude 还是其他工具？我给你对应的一步连接指引，密钥不用发给我。

官方[远程快速开始](https://docs.brightdata.com/products/mcp-server/remote/quickstart)提供远程MCP连接，省去本地服务安装。入口形态为：

```text
https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN
```

真实token由用户在自己的客户端安全配置中填入，不要求粘贴到聊天，也不回显包含真实token的URL。仅提供上述占位入口。需要本地模式时按[官方仓库](https://github.com/brightdata/brightdata-mcp)配置`@brightdata/mcp`和`API_TOKEN`；不把凭证写入Skill。

连接后，先发现工具与scraper、读schema，再在已有授权和额度范围内进行一条最小只读试采；只读不代表免费。若必须新开付费能力或超出已知授权额度，先说明具体调用范围并取得该动作授权，期间可完成schema核查；费用／额度无法确定时先核账户说明，不以“验证连接”为由盲调用。工具列表可见只说明发现成功。查看[当前概览](https://docs.brightdata.com/products/mcp-server/overview)，核对账户和功能范围；不承诺免费额度或总费用。当前文档与历史示例存在工具分组差异，不固化`pro=1`、`groups=ecommerce`或旧Amazon专用工具名。产品采集以当前可用的发现→详情schema→运行链路为准。

## 2. 飞书 CLI

先做只读检查：

```bash
lark-cli --version
lark-cli profile list
```

未安装时指向[飞书官方CLI仓库](https://github.com/larksuite/cli)。2026-10-22核验的官方安装入口：

```bash
npx @larksuite/cli@latest install
```

只在用户授权的配置范围内安装；否则给这一步让用户执行。缺Node.js时先引导安装Node.js，再继续。已安装时不为本任务自动升级CLI。

首次配置先读`lark-cli config init --help`，当前版本支持`config init --new --name '<新profile>'`；已有应用按CLI指引复用。OpenClaw／Hermes等环境可能需要`config bind`，不要自动用`--force-init`绕过。

给用户的是“打开这个授权页面完成登录”，而不是一串权限术语。应用配置和用户授权是不同步骤；每次仅引导当前一步。执行认证前读本机`auth login --help`，按目标命令实际缺失的最小scope授权，保留正确profile；用户自行在官方页面登录，不索要App Secret或token。某些版本支持`--no-wait --json`返回授权链接并用device code接续，按实际help操作，不保存这些临时信息到公开文件。

## 3. 知识库目录与账号路由

用户不会找目录时：

> 打开飞书知识库，进入希望存放报告的父级页面，复制浏览器地址发我。文字报告和HTML文件会放在它下面。

用户已给两个不同位置时分别沿用；仅给一个父目录时默认两个产物作为子节点放入。不要擅自创建新知识空间，也不把指定目录正文替换成报告。

先用`profile list`枚举，按URL host、资源归属与身份选择，再验证：

```bash
lark-cli auth status --profile '<匹配profile>' --verify --json
lark-cli wiki +node-get --node-token '<用户提供的完整Wiki目录URL>' --profile '<匹配profile>' --as user
```

当前CLI支持上述shortcut；若版本不同，查help。原生API必须先`schema`再操作。Wiki token不是文档token，记录解析返回的space/node/obj类型和token；不猜URL或对象类型。

成功后回显目录标题，继续已授权任务；读取成功仅证明可读，不声称已验证写入。每条后续业务命令带显式`--profile`和`--as user|bot`，不改全局默认配置。bot不能通过用户登录修复权限，选身份要匹配资源与授权。

失败分情况处理：认证过期先原profile刷新；scope不足按错误申请最小scope；网络错误有限重试；权限错误先对已配置且匹配的候选身份做只读核验。只有身份和scope有效仍无法读取，才称资源权限不足。不要反复让用户重新登录，也不静默换目录。

## Change Log
- 2026-10-22：核验Bright Data官方文档、飞书CLI官方入口与本机命令形态；加入渐进式引导和租户路由。
