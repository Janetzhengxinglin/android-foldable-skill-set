---
name: android-foldable-design-guidelines
description: 依据 Google 官方指南逐页审查安卓折叠屏 App 截图中的基础显示问题及明确的整体留白、对齐布局异常，关联依据、条件与位置。默认不判断动态状态、外接设备、点击能力或共享输出，不提供设计优化建议。
---

# 安卓折叠屏设计规范

版本 0.2.8；整体留白与对齐判定修订 2026-11-26。审查截图可确认的 Google 基础显示问题，以及页面整体留白、同级内容对齐中的明确布局异常。官方强制不符合项与可见布局问题分别记录，不把缺少强制条款等同于没有显示问题。

属于安卓 skill set 的判断环节：接收同级 android-foldable-page-capture 整理的稳定截图，向 android-foldable-adaptation-review 交付 review.json。原始录屏用于选帧和核对来源，不自动变成动态功能测试。不负责 Figma／飞书排版和发布。

## 默认执行顺序

批量读 [集中批量审查](../android-foldable-adaptation-review/references/batch-execution.md)。按流程连续查看清晰整页拼图，疑点读原图，集中记录页面／组件观察并批量生成正式检查项；重点复查问题及报告后统一校验。常规引用已核查的当前 profile 与来源，按疑点查相关原文及例外。

读取 [审查范围](references/audit-policy.md)、[判断方法](references/decision-protocol.md)、[可见对象检查](references/component-inspection.md) 和 [来源路由与层级](references/official-source-routing.md)。按 [官方设计参考](references/design-reference.md) 核对适用条件与例外，不限于报告配图。默认 profile 为 screenshot-only，见 [范围配置](references/audit-profiles.json)。

1. 确认截图的显示区、方向和窗口，识别全部组件实例。
2. 先记录可见疑点，再核对对应规则和例外，不能批量预填通过或用一个例外排除整页。每页先查窗口是否铺满、越界、遮挡、明显变形和文字截断；同时观察同级元素边线、基线和间距，按 component-inspection 区分基础显示问题、设计一致性观察与正常例外；整页留白按 design-reference 结合背景、内容分组、边线及固定区域关系判断，区分合理留白与明确布局异常；再查已展示的输入／键盘、菜单、弹层、媒体和主题可读性。
3. 同一页面涉及多个内容状态时，分别套用适用的显示要求，不能只按“场景类别”跳过通用检查。
4. 全页巡检后，回查疑点、已确认问题和报告映射，再汇总全部位置；two-pass 模式才全量重读原图。

~~~bash
python3 scripts/lookup_rules.py --category window
python3 scripts/seed_review.py /path/to/review-input.json /path/to/review.json
~~~

脚本生成逐项记录，不识别页面或判断问题。默认只生成 6 类截图检查卡对应的页面／组件记录，不给每页生成动态、外设或测量待验证项。

## 判断范围

已展示的外屏、展开内屏、分屏窗口及键盘、弹窗、菜单、错误、滚动和播放画面都检查可见显示。1:1 内屏两个方向分别保留，不按图片比例合并。8 个采集状态是项目安排，不代表所有折叠屏硬件比例；额外提供的方形外屏等截图仍按实际窗口检查，见 [屏幕配置](references/screen-contexts.json)。

截图不证明状态保持、真实点击／滚动／关闭、外接设备操作、后台播放、TalkBack 语义、真实热区或接收端输出。本次不执行这些测试，不把它们记成缺陷或逐页“待验证”。未提交的静态屏幕和页面状态在范围说明中集中列出。

图片或相机预览的拉伸需要已知原比例、正常画面或可确认几何参照。等比缩放、正常构图裁切和留边不直接报错；这个例外不排除图片内截字或必要信息缺失，按可见对象检查分别判断。明显模糊、像素化与当前图标不可辨独立检查；不以缺少源素材或数值测量笼统排除。相机启用、生效铰链或系统区域等条件不明确时，只判断已确认的可见遮挡，不猜测硬件区域。

## 官方依据和扩展资料

[official-basis.json](references/official-basis.json) 保存精确条款与测试原文；[sources.json](references/sources.json) 保存全部已登记来源和阅读范围；[conflicts.json](references/conflicts.json) 保存例外及措辞差异。每条检查先核对原文、适用条件、例外及原图。模板、图库和设计指南的已读用途及限制见 [阅读范围](references/design-resource-coverage.json)。未读内容、推荐设计和 Tier 2／1 不能用于判错。

完整 Tier 3 与相关 Core 资料保留在规则库，不代表默认执行全部官方测试。只有用户另外明确委托连续操作、外设、测量或共享测试，才按 [证据格式](references/evidence-contract.md) 启用 submitted-evidence；不得因为收到录屏自动启用。

## 输出与校验

输出 review.json，保留逐页组件观察、例外、证据和官方依据。issue 仅包含已确认问题；no_issue_observed 仅表示当前截图未发现问题；条件未知或原图不足时在内部记录，报告集中说明静态范围，不给页面贴待核实标签。可确认的整体留白或对齐异常按 decision-protocol 写入 reported_issues，由审查主动收录，无需用户另行确认；它们不自动成为 Google 强制不符合项。问题编号和全部发生位置交给汇总 skill，不能添加建议、猜测代码原因或丢失同类问题的其他页面。

~~~bash
python3 scripts/validate_rules.py
python3 scripts/validate_review.py /path/to/review.json
~~~

按 batch 实际回查问题后填写 self_review.finding_ids_rechecked；严格 two-pass 才填写两轮全页及组件复查标志。校验验证引用与记录，不替代视觉判断，也不证明完整 Tier 3 或 Google Play 认证通过。

## 大批量图片读取

全页巡检与重点复查遵守 [图片处理协议](../android-foldable-page-capture/references/image-processing.md)，独立使用时同样分批、记录累计输入和保存接续检查点。小候选图仅用于筛选；清晰成品整页拼图可用于巡检，读不清或有疑点时使用原图。读取预算不减少应审页面和组件。

按图片处理协议执行读取前预算检查、实际输入记账与超限接续。读取批次不拆成独立任务，候选、原图、复查和报告预览共用实际上下文的预算。
