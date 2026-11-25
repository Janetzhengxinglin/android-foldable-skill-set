# 执行与交接

三个同级目录组成一套：android-foldable-page-capture → android-foldable-design-guidelines → android-foldable-adaptation-review。入口负责集中批量执行和输出，采集只整理，设计规范只判断。批量默认遵守 [集中批量审查](batch-execution.md)，先保存真实观察，再批量生成正式记录；以下脚本只接收真实完成的完整输入。

本轮目录建议保存 intake.json、raw/ 各录屏采集、capture.json、review-input.json、review.json 和 report-v1/。intake 记录用户已有的流程、材料、设备／屏幕与输出目标；只问缺失信息。没有运行目录时在当前项目中建立，不把素材放入安装目录。

workflow.py merge 将全部完成的 capture.json 合并，给不同录屏的页面、上下文与证据加唯一前缀，并重写引用，保留原始采集文件及 hash。不会按图像内容去重，因此正方形方向、键盘和弹层等状态仍分开。逐页核对最终清单后再 prepare。

prepare 保留原 capture.json，复制为 review-input.json，并记入 original_capture hash。设计规范环节先在工作副本补齐组件实例、已知屏幕／功能条件，再 seed。默认 seed 使用 screenshot-only，仅生成可见检查。新增原图和条件证据 path 按工作副本的位置解析。动态、外设、测量和共享字段只有另行委托扩展测试才使用。

按设计规范要求完成检查与第二轮复查。not_verified 进入范围说明，不能包装成问题。汇总 findings 保持同一编号，多页或多实例都保存 locations；不同措辞的 should 与强制要求不混为同一问题。修改归组后重新运行 validate_review.py。

build_report.py 校验 review.json 后生成 report.json、figma-plan.json 与本地 report.md。它读取已完成的判断，不补写结论、不创造建议、不写外部应用。发布前核对所有问题位置进入第三段、每个问题编号在第二段有解释，示例页可以跨问题共享。

publication.json 在实际回读后记录 target_url、report_sha256、节点／块映射、写入和回读结果。修订报告另存新版本，保留旧结果。没有实际发布时不要生成成功记录。
