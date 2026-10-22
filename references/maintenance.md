# 版本维护

维护者：Hao Wu · 状态：active · 更新：2026-10-22

## Skill版本

- `VERSION`为发布版本，须与`SKILL.md`的`metadata.version`及`CHANGELOG.md`最新条目一致。
- PATCH：修正措辞、命令或已发现缺陷；MINOR：兼容地新增能力；MAJOR：改变启动、输入或交付合同。
- 每次实质修改更新相关文档日期，记录具体变化。维护按真实使用问题进行，不自动设置定期任务。
- 发布前验证frontmatter、所有本地引用、命令示例和现实场景。结构校验通过不等于真实工具接入／飞书发布已通过。
- Git使用`vX.Y.Z`标签并发布Release，记录验证范围；不移动已发布标签。同版本本地安装与仓库文件应一致。
- 之后的GitHub同步遵守当前用户授权；本Skill被调用来研究产品，不代表授权修改Skill仓库。

## 研究案例版本

案例资料保存在工作目录，不能进Skill安装目录或公开Git仓库。`case.json`推荐字段：

```json
{
  "category": "用户品类",
  "market": "用户站点",
  "skill_version": "1.0.0",
  "report_version": "1.0.0",
  "stage": "setup",
  "updated_at": "实际时间及用户时区",
  "user_decisions": [],
  "sources": [],
  "data_gaps": [],
  "target_wiki_url": null,
  "route": {"profile": null, "identity": null, "verified": false},
  "artifact_links": {},
  "change_log": []
}
```

新证据改变结论时，备份旧文字／HTML，记录旧判断、新判断及依据，报告版本递增。公开包不携带真实case、报告数据、客户目录链接、抓取原文、截图、凭证或账户配置。公开仓库可见性不自动授予另一个项目的数据公开权，也不自动意味着附加开源许可证。

## Change Log
- 2026-10-22：定义Skill、案例与报告的独立版本线。
