# 证据与交接格式

默认 profile 为 screenshot-only，只生成页面／组件的可见检查。录屏用于取稳定帧与追溯来源；以下动态、测量、语义和接收输出字段是另行明确委托 submitted-evidence 时使用的扩展格式，不是默认必交材料。

只使用本地运行目录；业务截图、录屏、报告与临时文件不放入 skill。三个安卓 skill 通过以下格式交接，schema_version 为 1。相对路径按引用它的 JSON 所在目录解析；独立使用也遵守此约定。

## 输入 review-input.json

录屏整理 skill 后续提供原始采集数据。设计规范环节创建工作副本，保留原文件与 hash，再补齐组件库存和已知条件；不改原始证据文件。seed_review.py 接收补齐后的工作副本。

顶层字段：

- contexts：设备／窗口上下文数组。每项有 id、platform、API（api）、device_family、display（outer／inner）、rotation、window_size_dp、size_px、density、window_mode、target_sdk、fold_feature；未知为空。另有 facts。
- evidence：证据数组，详见下节。
- pages：页面数组。每项有 id、name、context_id、image_evidence_id、components、facts。
- facts：App 层已知条件。每个条件均为 {value: true／false／null, reason: 说明, evidence_ids: 来源证据编号数组}。已知 true／false 必须有理由与证据。页面、上下文、组件也可定义 facts；越具体的对象优先。
- original_capture：可选原始采集文件 path 与 sha256，供后续录屏整理环节交接。

components 每项有全局唯一 id、kind、description、facts。kind 为 text、button、input、navigation、list、card、media、overlay 或 other。重复卡片、文字与按钮分别登记。列表／选择器等实际可滚动对象也可用 other，以避免组件类型掩盖所需检查。

条件名称由 rules.json 的 conditions 定义。重点条件包括 in_app_camera、in_app_projection、exclusive_resources、continuous_updates、text_input、external_keyboard_supported、pointer_supported、stylus_supported、handwriting_supported_by_platform、audio_playback、video_playback、pip_supported，以及组件 clickable、selectable、scrollable、touch_target、reading_text_block、meaningful_visual、semantic_label_required。未知时不猜测。

## 证据记录

每项 evidence 有 id、kind、path、sha256、description、page_ids、context_ids。事实来自用户明确说明时，将原话保存为本地文本，使用 user_context；不得把分析推断写成用户事实。

- image：原始完整截图，另有 width_px、height_px。保留窗口边界和系统区域。缩放／标注副本不能替代原图。
- transition_clip：连续录屏片段，另有 start_s、end_s、actions、before_state、after_state。起止是该文件内时间；记录动作、前后输入／滚动／播放状态及切换次数。
- interaction_record：本地操作记录或操作录屏；注明外设、动作、结果和所涉页面。
- runtime_context：本地环境／运行信息，注明设备、API、窗口、密度、资源抢占、功能启动来源等相关事实。
- receiver_output：共享接收端／录制输出；注明与发起流程的对应时间和整屏／单窗口。
- audio_record：带声音的实际播放证据，不以静音录屏证明音频行为。
- semantics_record：TalkBack 或语义树的实际记录。
- measurement：JSON 文件，包含 measurements 数组，每项有 type、subject_id、method、source。数值检查不能只引用测量工具的截图而不保存具体数据。

测量类型：

- touch_target：width、height、unit 必须为 dp，actual_hit_area 必须为 true。source 记录热区来源和密度换算，不能把图标尺寸当点击范围。
- contrast：ratio、content_class（large_text／small_text／graphic）、class_basis、foreground、background。字号分类须解释原文 pt 与实际字号单位，不能直接用 PNG 像素划档。
- line_length：language、reading_block=true、lines（逐行原文字符串）、last_line_included（是否包含末行）。记录是否完整文本块和末行，按官方原文核对，不能强行给短标签凑字符数。

一个证据可供多个检查，但必须在 page_ids 中关联每个发生页面，并在 context_ids 中关联实际环境。工具只能校验引用关系，仍需看原证据确认相关性和真实性。

## 输出 review.json

seed_review.py 默认为全部提交页面生成页面和组件可见检查。只有显式选择 submitted-evidence 时才增加运行场景和测量检查。它不会生成任何问题或通过结论。

顶层字段：schema_version、rule_version、input_path、input_sha256、scope、checks、findings、inventory_review、self_review。scope.page_ids 为受审页面；excluded_pages 每项包含 page_id 和 reason。材料中的每页必须纳入或明确排除，修改范围后须同步重新生成检查集合，不覆盖已有判断。

每条 checks 包含：

- id、rule_id、subject_type、subject_id、page_ids：由种子生成，固定指向对象。
- status：issue／no_issue_observed／not_applicable／not_verified。
- applicability：result 为 yes／no／unknown，与条件 facts 对应；reason 说明条件；evidence_ids 指向事实证据。
- evidence_ids、observation、exception_review、evaluated_basis_ids：实际观察及核对的原文与例外。issue 和 no_issue_observed 必须达到规则的证据门槛。
- coverage_details：tested_actions、missing_actions、notes，写实际检查了什么，尚缺什么；不声称单一成功场景覆盖全部测试。
- priority：规则的执行顺序。

findings 只保存 issue。每项含 id（问题编号）、check_ids、problem、impact、priority、requirement_wording、basis_ids、locations。共性归组保留全部检查与发生位置；should 与强制措辞不能混为同一个问题。

locations 每项有 page_id，以及原图 bbox_px=[x,y,width,height] 或 scenario_description；有组件定位时带 component_id。不同屏幕状态是不同页面，不通过图片宽高比去重。汇总 skill 后续用统一编号生成标准、问题示例说明、全部问题页面三段式 Figma 输出。

inventory_review.page_ids_verified 记录已核对库存的全部受审页面，notes 说明库存检查。默认 review_strategy="batch"：visual_review.page_ids_reviewed 和 notes 记录全页清晰巡检；self_review.finding_ids_rechecked 和 notes 记录实际问题回查。review_strategy="two-pass" 或旧记录未声明策略时，self_review.all_pages_rechecked、all_components_rechecked 及 notes 记录第二轮全量复查。校验脚本不代替真实复查。

## 脚本边界

validate_review.py 检查证据文件及 hash、适用条件、完整检查集合、证据类型、数值记录、问题与标号、所选策略的巡检／复查记录。它不会自动识别截图中的缺陷、判断原文语义或计算全部规范是否满足。缺少证据保留 not_verified，输出范围说明；不要制造页面缺陷标签或完整通过结论。
