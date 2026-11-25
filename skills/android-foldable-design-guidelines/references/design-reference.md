# 官方设计参考如何用于审查

逐页判断前必读。设计指南和模板用于理解正常适配方式、核对条件和排除误报；确认问题仍须引用 Tier 3 或应用基本质量要求的原文。只检查已提交截图中的不符合项，不输出设计改进建议。

## 判断时必须核对

| 检查对象 | 如何判断 | 官方设计参考 |
| --- | --- | --- |
| 窗口宽高 | 先确认 App 实际窗口宽度，再确认可用高度。横屏可以更宽但更矮；分屏按 App 窗口判断，不能用整块内屏尺寸代替。尺寸等级之间也需要正常伸缩；只收到固定尺寸截图时，不宣称已验证整个尺寸区间。没有密度信息，不能将截图像素直接当作 dp。 | [Adapt your layout](https://developer.android.com/design/ui/mobile/guides/layout-and-content/adapt-layout)、[Grids and units](https://developer.android.com/design/ui/mobile/guides/layout-and-content/grids-and-units) |
| 内容宽度与留白 | 分开检查 App 窗口、整页根容器和局部内容。App 必须填满实际可用显示区，整体加框属于基础适配问题。正文、表单、卡片或按钮可合理限宽；这个例外不能自动解释整页背景、正文和固定操作一起集中在窄区、其余区域大面积空白。遇到后一种现象先核对整页边界，不能只用“留白允许”判通过；无法确认是否未铺满窗口时保留基础适配疑点和缺口。单栏、留白本身不证明违规，截图也不证明兼容模式；不要求每个容器满宽或强制多栏。 | [Tier 3 Config_Changes](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-3#Config_Changes)；Adapt your layout；Adaptive Design Lab 的 Component behavior |
| 弹窗、底部面板与辅助内容 | 同一功能在窄窗口中可以使用底部面板，在宽窗口中改为侧面板或其他弹层。检查当前呈现中的截字、越界和已确认遮挡，不因位置或组件形态改变判错。正常弹窗遮罩和底层内容暂时被覆盖不直接报错。 | Adapt your layout；[Adaptive UI Samples](https://www.figma.com/community/file/1539759053650269019/android-adaptive-ui-samples) 的 Shopping / Productivity 示例 |
| 系统栏、键盘与挖孔 | 区分系统区域、App 导航区和正文。背景或滚动内容延伸到系统栏下方可以正常；关键文字与控件受到实际遮挡才进入问题判断。系统栏形态可能因厂商、系统版本、手势或三键导航而不同；模板安全区不能直接套成所有设备的固定边距。 | [App Anatomy](https://developer.android.com/design/ui/mobile/guides/layout-and-content/app-anatomy)、[Android system bars](https://developer.android.com/design/ui/mobile/guides/foundations/system-bars)、[Android UI Kit](https://www.figma.com/community/file/1478523627015571873/android-ui-kit) 的 Grids and insets |
| 图片、视频与相机预览 | 区分媒体容器和 App 窗口。等比留边、正常裁切、封面与实际视频使用不同比例均不直接报错。拉伸须有原图、正常画面或可靠几何参照；屏幕比例不能直接作为媒体比例。UI Kit 的 Camera 是系统相机示例，外观可因设备和厂商变化；只检查 App 自有预览，不将系统相机界面差异归为 App 显示问题。 | Postures and orientation；Grids and units；Adaptive UI Samples 的 Media 示例 |
| 折叠与铰链 | 先确认折叠特征是否实际遮挡、分隔内容。平展折痕不自动成为禁区，单栏也不必机械分成两栏。已提供半折叠截图仍查基本显示，但不要求桌面式或书本式专属布局。 | [Postures and orientation](https://developer.android.com/design/ui/mobile/guides/layout-and-content/postures-and-orientation) |
| 屏幕配置 | 官方指南也提到方形外屏。项目中的 1:1、4:3 内屏与对应外屏共 8 个状态是本次采集配置，不代表所有折叠屏只有这些比例。收到其他外屏或窗口截图时，仍按实际窗口检查并在报告中写明覆盖范围。 | Postures and orientation；[Google Play 截图采集](https://developer.android.com/google/play/requirements/screenshots-android-cli) |
| 文字、主题与导航 | 自有设计系统、品牌字体、静态配色可以使用。区分文字可辨性与对比度数值、图标尺寸与实际触控热区；区分 Android 的 Up、Back、Close，但不能只凭截图认定返回行为错误。 | [Translate your designs](https://developer.android.com/design/ui/mobile/guides/foundations/translate-designs)、[Accessibility](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility)、[Color](https://developer.android.com/design/ui/mobile/guides/styles/color) |

## 图库和模板的用途

- [Adaptive App UI Design Gallery](https://developer.android.com/design/ui/gallery)：已读 30 个案例正文。用来理解内容分组、容器伸缩、网格重排、单页与列表详情、底部与侧面辅助内容等适配方式。业务案例的推荐布局不能作为所有 App 的必选布局。
- Android UI Kit：已读内部 Guide，以及 Keyboards、Permissions、Camera 的定义与相关图示，核对相关页面目录和结构。用来识别系统区域、理解安全区和 dp / sp、区分系统模板与 App 自有内容；不能因为模板包含相机、通知、桌面小组件，就要求每个 App 都具备这些功能。
- Adaptive UI Samples：已读介绍，核对 Social、Shopping、Media、Productivity、Reading 页面结构，查看全部五类 Examples 图，并读取 Reading 的示例说明和辅助面板说明。用来对照同类功能在不同窗口中的正常呈现；样例的分栏、导航轨、Material 样式不构成强制要求。
- [Adaptive Design Lab](https://www.figma.com/community/file/1504631597454929506/design-an-adaptive-android-layout)：已读窗口尺寸、布局组成、移动／桌面组件行为、分组与容器说明、练习介绍和列表详情练习步骤，并查看 Completed 页五组完成图。用于理解尺寸等级之间的伸缩、组件固定宽度、重排和等效组件替换。其余练习步骤及内部组件变体未全部核对，不从未读内容建立判断。

模板阅读详情保存在 design-resource-coverage.json。遇到需要精确模板尺寸或尚未核对的变体时，必须读取对应 Frame；不能用封面、目录或元数据代替内容。

## 本次不能据此增加的要求

不要求多栏、导航轨、辅助面板、桌面式／书本式布局、双屏同时显示、拖放、可定制工作区或高级触控笔功能。图库将它们作为适配设计方向，不等于本次 Tier 3 截图审查的必检功能。

不把 Material 的配色、Roboto 字体、4 / 8 dp 网格、示例画布宽度或示例媒体比例当成通用合规阈值。课程的 60 字符行长、16 dp 内边距、五列面板和辅助面板约占三分之一是建议或示例参数，不作为本次通用阈值。12 sp 字号建议也不能单独新增为本次判错规则。官方无障碍数值保留作另行委托的测量依据；有不同字号、对象或例外时按应用基本质量条款核对，不能从截图观感推出数值不达标。
