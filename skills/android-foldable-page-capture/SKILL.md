---
name: android-foldable-page-capture
description: 从安卓折叠屏 App 录屏整理稳定页面截图，保留屏幕状态与来源，交接安卓设计规范审查；连续操作证据仅用于另行委托的扩展测试。
---

# 安卓折叠屏录屏整理

安卓 skill set 的证据整理环节。版本 0.2.11，数据格式 1。只整理材料，不判适配问题或发布报告。

读取 [采集与交接](references/capture-contract.md)。批量或长流程另读 [批量执行](../android-foldable-adaptation-review/references/batch-execution.md)，集中选帧、核对重复状态，只对具体疑点补图。选帧后可用 scripts/review_sheets.py CAPTURE.json SHEET_DIR 生成清晰整页拼图和格位索引，供质量与适配合并巡检。用户提交录屏即可启动；流程、外屏／内屏、方向及设备信息只问缺失项，不要求用户填写时间点或技术参数。未知 API、dp、密度和折叠特征保持空值，不根据图片比例猜测。

1. sample 默认每秒采样一次，沿用 Duo 已执行的批量采集密度；候选拼图仅作定位。页面快速变化、错误／确认弹层或候选间内容接不上时，对该区间定点补帧，不把两个候选之间未看见的状态当成不存在。调用 sample，依次看全部候选及时间间隔，确认 App 页面、键盘、菜单、弹层、错误和滚动状态。短暂出现的页面状态用 frame 补帧，或在新目录缩短采样间隔。不根据相似图片自动合并屏幕方向，尤其 1:1 内屏。
2. 创建 selection.json，记录完整候选分类、实际屏幕上下文、页面选帧和连续片段。旋转、折叠／展开前后分别保留稳定页面，保留原录屏追溯选帧；不判断切换过程或状态保持，不要求补拍外设、共享或其他实测。连续片段仅在另行委托扩展测试时交接。
同一业务页面的截图先建立页面身份和滚动状态关系；新增内容或疑似异常保留采集，报告代表图去重在审查后执行。明显疑点建立疑点清单并标明是否已采集，不能在截图阶段因推测素材、加载或滚动正常而剔除。

3. finalize 生成 capture.json 与原始完整截图。脚本核对尺寸与来源，清晰拼图巡检时同时确认所选截图质量；有疑点才定点补查。完整回查后统一交接，不为每张截图建立质量任务。

~~~bash
python3 scripts/capture.py sample VIDEO CANDIDATE_DIR
python3 scripts/capture.py frame VIDEO SECONDS OUTPUT.png
python3 scripts/capture.py finalize CANDIDATE_DIR SELECTION.json
~~~

脚本依赖 Python 3.9+、ffmpeg 和 ffprobe；不需要 OpenCV／Pillow。候选图和拼图不代表已完成页面识别。

不裁系统栏或 App 内容、不拉伸原图。外部浏览器／系统相机页面排除，App 内嵌网页和相机保留；系统区域保留以判断对 App 的实际遮挡。若需要脱敏，另存展示副本并记录映射，不能用模糊后的区域推断问题。没有授权不得将敏感原图发布到外部。

截图和连续证据统一交给同级 android-foldable-design-guidelines；由 android-foldable-adaptation-review 编排。完整 capture.json 覆盖全部录屏候选和应审状态后统一交接，不先筛选“问题页”。

## 图片处理与读取预算

采样、选帧和质量回查前读取 [图片筛选与接续](references/image-processing.md)。使用压缩候选拼图及完整分组索引分类，图片按预算分批输入；文件生成不等于已读取或审查完成。

按图片处理协议执行读取前预算检查、实际输入记账与超限接续。读取批次不拆成独立任务，候选、原图、复查和报告预览共用实际上下文的预算。

统一执行方法见 [图片协议](references/image-processing.md)；验收覆盖与现有三段式报告样式不变。
