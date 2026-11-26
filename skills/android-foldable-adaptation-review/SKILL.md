---
name: android-foldable-adaptation-review
description: 编排安卓折叠屏 App 录屏审查，联动稳定页面整理、Google 基础适配的可见显示检查，完整汇总问题并按三段式交付 Figma 或指定文档。
---

# 安卓折叠屏适配审查

安卓 skill set 总入口，版本 0.2.18、交接格式 1。用户提交录屏并发起审查即可启动。默认检查截图可确认的 Google 基础适配显示要求及明确的整体留白、对齐布局异常，不提供 Tier 2／1 优化或设计建议。规则仅维护在设计规范 skill，不复制到本入口。

## 执行方式与子智能体

默认主智能体按流程集中执行。独立材料确有分工收益时再读取 [条件分工与交接](references/agent-coordination.md)，分派完整录屏／业务流程，默认同时最多 2 个子智能体。单智能体不建立额外分工文件；主智能体统一验收与发布。

## 启动

运行 scripts/preflight.py，确认三个同级 skill 和 ffmpeg／ffprobe 可用，并校验官方规则。缺失时修复对应依赖，不替换成 Duo 或竞品审查。读取 [执行与交接](references/workflow.md)。

只补问缺失的流程、外屏／内屏和方向、设备信息及输出位置。API、dp 等用户不知道就记录未知，不要求填写技术表格。输出目标未确定时先整理与审查，不自行选定外部文件。已有目标和授权不重复问。

## 批量执行与最终交接

多份录屏先读 [集中批量审查](references/batch-execution.md)：集中选帧与观察、批量生成记录、条件复核、统一报告。不建立多层质量／预审／修补队列。

## 三个环节

1. 读取同级 android-foldable-page-capture/SKILL.md，批量抽帧，集中分类全部候选并确认清晰代表图。每份 recording 各有完整 capture.json；统一交接后按流程连续看图，不能只挑问题页面。
2. 建立 review-input.json 工作副本，读取同级 android-foldable-design-guidelines/SKILL.md，逐页识别全部组件，再建立 review.json 并判断。默认使用 screenshot-only，仅检查截图可见显示；动态变化、外设操作、测量和接收输出不进入本次检查集合，不因收到录屏自动启用扩展测试。先集中保存真实页面／组件观察，再批量填入正式记录；默认清晰拼图全页巡检、疑点读原图；首次证据充分即定论，仅定点复核疑点、冲突或变化；核对全部报告映射后统一运行 validate_review.py。严格双轮仅使用 two-pass。
3. 按 [同页证据去重](references/report-deduplication.md) 区分业务页面、受审状态和报告代表图。同页同组件同一异常的滚动／重复进入状态只展示必要代表图，后台保留全部发生位置，运行 build_report.py，核对编号和全量问题页面，然后按用户指定目标发布、回读。明确留白与对齐布局问题从 review.json.reported_issues 进入同一报告，不只读取 findings，也不等待用户指出问题。

~~~bash
python3 scripts/workflow.py merge RUN_DIR CAPTURE_A.json CAPTURE_B.json
python3 scripts/workflow.py prepare RUN_DIR
# 完成清晰全页巡检，补齐 review-input.json 的组件库存与事实后：
python3 scripts/workflow.py seed RUN_DIR
# 完成逐项判断及必要的条件复核后：
python3 scripts/build_report.py RUN_DIR REPORT_DIR
~~~

脚本不识别页面或判断问题，也不自动发布。补图或更改证据时保留旧轮次，生成修订输入并重新核对受影响结论，不能静默沿用旧 hash。

## 输出

审核策略与交付样式分别维护：batch／two-pass 只改变审核执行，不改变用户已认可的 Duo 展示模板。交付前按 [交付样式](references/output-presentation.md) 和 [Figma 三段式输出](references/figma-output.md) 对照实际成品；本地 report.md／JSON 是后台记录，不能直接作为最终文档交付。

发布前必须读取 [视觉呈现与验收](references/output-presentation.md)，落实简短说明、抽象对应图解、统一对齐、就近图外标号、适中参考尺寸和底部全量去重映射；该文件优先约束展示方式，不改变平台判定规则。

读取 [Figma 三段式输出](references/figma-output.md)、[官方示例选择](references/official-examples.md)和 [排版参数](assets/report-style.json)。按示例与问题的对应关系、适用条件、是否误导和内容核实情况选图，不直接沿用脚本预置图。先按屏幕比例、内外屏和方向分画板，用画板标题区分。每张有问题的画板依次展示：Google 官方规范示例；App 问题示例；问题页面汇总。编号放在截图外，App 说明卡（含待核实项）使用浅灰底；不显示秒数或默认添加局部放大。说明只保留通用异常描述和官方依据，同类归组不省略发生页面或组件。

输出 Figma 时使用当前可用的官方 Figma 工具与相关 skill，在用户指定文件中创建可编辑标题、说明、编号和引线，按原比例置入截图。figma-plan.json 是排版数据，不是“已写入 Figma”的证明。所有展示的审查项（包括待核实项）均须有截图外编号、位置框和同号文字说明，右侧说明执行 build_figma_explanations.py 生成的代码，不临时手写；按 references/figma-output.md 验收卡片结构、字号与标注后再交付。没有已证实问题且没有待核实观察时简短给出结论及范围，不造空问题示例。

用户选择飞书时使用飞书文档能力，保持相同三段式内容并回读；未选择不擅自换目标。发布失败保留本地报告，准确说明未完成的部分。

审查中遇到误报或漏报，定点回查原图与官方依据，修正当前结论及受影响映射。流程问题记入项目记录；只有用户委托维护 skill 时才另行修订和测试，不让每份报告自动触发 skill 修复循环。不能将具体 App 历史问题或素材写入通用 skill。完成与重试边界见 output-presentation.md。

## 图片读取与分批接续

执行各阶段前读取 [图片处理协议](../android-foldable-page-capture/references/image-processing.md)，完整清单在本地交接，图片分批读取并保存累计日志和检查点。默认 batch 保持全页面巡检，原图用于读不清、疑点、冲突或变化的定点补查；汇总及发布预览也计入预算。

按图片处理协议执行读取前预算检查、实际输入记账与超限接续。读取批次不拆成独立任务，候选、原图、复查和报告预览共用实际上下文的预算。

统一执行方法见 [批量执行](references/batch-execution.md)；验收覆盖与现有三段式报告样式不变。
