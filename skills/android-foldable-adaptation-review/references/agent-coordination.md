# 条件分工与交接

仅在实际分工时读取。批量默认由主智能体集中执行，文件下载、抽帧和排版可用脚本并发；单智能体不建立 delegation-plan 或 handoff 文件。

材料独立且分工收益明确时，默认最多两个子智能体，按完整录屏或业务流程分派。关联滚动、弹层对照和跨姿态证据放同一任务；不拆成每几张图一个执行者，也不建立多个质量／预审／修补层级。执行者取得必要原图、来源索引、规则和用户事实，按批量协议连续处理阶段工作，优先独立上下文，不继承完整图片历史。用户要求单智能体时遵从；工具不可用时主智能体执行。

主智能体从真实材料建立完整工作单元清单，任务在独立目录写结果，禁止多个执行者修改同一主文件或并发发布。每个阶段分配不重叠，完成后覆盖全部工作单元；默认 batch 完成全页巡检和问题重点复查；two-pass 才另建第二轮全量工作单元。

分工时使用 references/handoff.json 的现有格式和 scripts/validate_handoffs.py 核对任务身份、覆盖、结果目录及证据 hash。manifest 分阶段保存，phase 为 capture、review 或 recheck；expected_units 由主智能体核对，evidence 保存实际路径和 hash。任务完成时提交 handoff.json；中断保留已完成结果及 pending_units，不重复发送整批图片或大 JSON。

~~~bash
python3 scripts/validate_handoffs.py PHASE_MANIFEST --plan-only
# 实际完成交接后统一核对：
python3 scripts/validate_handoffs.py PHASE_MANIFEST
~~~

脚本仅核对交接结构，不能识别页面、判断问题或自动合并 review。主智能体按安卓 merge／prepare／seed 的真实 schema 合并组件与观察，核对全部状态、所选策略的巡检／回查覆盖及引用，再运行平台校验、统一编号、发布及回读。证据变化重审受影响判断，缺项保持未完成；不能凭任务自报 complete 或收据通过宣称审核完成。
