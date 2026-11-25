# 采集与交接

所有产物放本轮项目目录。原始录屏复制到 source，候选和原始页面分别保存；不覆盖既有运行目录。ffmpeg 依据视频方向元数据提取显示图，截图的实际 PNG 尺寸单独记录，编码尺寸不当成窗口 dp。

sample.json 记录录屏 hash、时长、候选时间及图片 hash。contact-sheet 为候选拼图；执行者按时间顺序查看后建立 selection.json：

- contexts：实际屏幕／窗口上下文，每项有 id，其他字段与设计规范 skill 的 evidence-contract.md 相同。资料不明时用明确的 unknown 上下文并保持字段空值。
- pages：每项有 id、name、context_id、time_s、state、selection_reason。ID 全局唯一；page 是一个页面在特定方向、显示区和布局状态下的画面。可用 logical_page_id 关联同一业务页面、用 scroll_state 标记滚动位置；状态 ID 仍独立。滑动只重复已覆盖组件时可归为采集重复，露出新组件、固定层关系改变或疑似异常时保留补充状态。不能把不同滚动高度直接算成不同业务页面。
- candidate_classifications：每项 id、classification、reason。所有候选均须分类；classification 为 app_state、duplicate_same_context、transition、loading、external 或 other。
- transitions（仅另行委托扩展测试时）：每项 id、start_s、end_s、page_ids、context_ids、actions、before_state、after_state、description。时间在原始录屏内，不截断关键操作；可以多个连续证据引用同一录屏的不同时间段。
- additional_evidence：用户明确说明及真实运行信息；测量和接收输出仅在另行委托扩展测试时提供，按设计规范 skill 的证据格式提供。相对 path 按 selection.json 位置解析。
- facts：已知条件与事实证据，格式沿用设计规范 skill；未知为 null。
- capture_review：all_candidates_classified、all_intervals_reviewed 均为 true，并有 notes。只在真实看完后填写。

finalize 不识别页面、不判断是否适配；完成后逐图核对原始截图。capture.json 含 contexts、pages、evidence、facts。components 初始为空，由设计规范环节在工作副本中逐页登记。使用不同 candidate 目录处理多录屏，集中选帧及回查完成后由入口合并完整 capture.json，保留原始路径和来源 hash。

不要因“采样没有看见”把短暂状态算作不存在。旋转前后比例相同、同页不同键盘／菜单状态不能只凭图像相似度去重。默认不采集外设操作或共享接收输出，也不将它们列为覆盖缺口；只有另行委托对应扩展测试时才整理这些证据。

选稳定帧时，以已有邻近候选或必要的前后帧核对正文和固定层的位置及清晰度；无疑点且已有充分支持时不机械追加抽帧，补查与来源缺口按批量执行协议处理。scene变化帧不等于稳定帧。快速滑动、回顶动画和头部收缩中的帧只能作为区间辅助证据，不能标成静态稳定页。静态截图必须选停顿后的可读画面；短暂异常保留原时间区间并交给审查核实，不因转场标签丢弃。
