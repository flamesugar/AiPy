# file: gui/ai_help_tabs.py
# Helper file for AI Assistant Help Dialog tabs content

def create_overview_tab_content():
    """Return content for the overview tab."""
    return """# AI Scientific Assistant - 光度测量数据分析助手

## 系统概述 (System Overview)

本AI助手是一个专门为光度测量数据分析设计的智能助手，集成了Claude AI技术，能够：

### 核心功能 (Core Features)
• 实时数据分析和解释
• 信号模式识别和相关性分析
• 统计假设检验和科学建议
• 可视化图表生成和解释
• 生物标记物发现和洞察
• 实验结果智能解读

### 技术特性 (Technical Features)
• 流式文本显示 - 实时响应感受
• 富文本格式化 - 专业的摘要和关键点显示
• 多模态输入 - 文本+图像理解
• GUI直接控制 - AI可以直接操作界面
• 上下文感知 - 理解当前数据状态

### 适用场景 (Use Cases)
1. **信号分析**: 分析ΔF/F信号模式、噪声特征
2. **峰谷检测**: 智能参数调整和结果解释
3. **相关性分析**: 多通道信号关系分析
4. **PSTH分析**: 刺激响应模式识别
5. **实验设计**: 参数优化建议
6. **结果解读**: 科学意义和统计显著性分析

### 界面特色 (Interface Features)
• 类Claude在线聊天体验
• 智能打字指示器
• 消息分类和视觉分离
• 丰富的格式化支持
• 实时图表共享和分析

### 数据安全 (Data Security)
• 本地数据处理，不上传原始数据
• 仅分享分析摘要和图表
• API密钥本地存储
• 会话数据可选保存
"""

def create_features_tab_content():
    """Return content for the features tab."""
    return """# 功能详细说明 (Detailed Features)

## 1. 智能对话系统 (Intelligent Chat System)

### 流式文本显示 (Streaming Text Display)
• **特性**: 字符逐个显示，模拟真实打字
• **速度**: 25字符/秒，可配置
• **指示器**: 思考中显示 "●" 符号
• **技术**: 异步处理，不阻塞界面

### 富文本格式化 (Rich Text Formatting)
```
支持的格式:
**粗体文本**       → 粗体显示
*斜体文本*         → 斜体显示
`代码文本`         → 等宽字体
# 标题              → 大标题
## 副标题           → 中标题
### 小标题          → 小标题
• 列表项            → 项目符号
1. 编号列表         → 数字列表
---               → 分隔线
***重要内容***      → 高亮显示
```

### 特殊格式化 (Special Formatting)
```
**[SUMMARY]**      → 摘要部分，蓝色高亮
**[KEY POINTS]**   → 关键点，特殊背景
**[ANALYSIS]**     → 分析部分，专业格式
**[CONCLUSION]**   → 结论部分，突出显示
```

## 2. 数据分析能力 (Data Analysis Capabilities)

### 信号处理分析 (Signal Processing Analysis)
• **滤波参数优化**: 自动建议最优滤波设置
• **噪声识别**: 识别和标记信号噪声
• **基线校正**: 分析基线漂移和校正效果
• **采样率分析**: 原始采样率vs降采样效果

### 统计分析 (Statistical Analysis)
• **描述性统计**: 均值、标准差、分布特征
• **假设检验**: t检验、方差分析等
• **相关性分析**: 皮尔逊、斯皮尔曼相关
• **时序分析**: 趋势、周期性、平稳性

### 可视化解读 (Visualization Interpretation)
• **PSTH分析**: 刺激锁定响应模式
• **相关性图**: 多通道关系可视化
• **时频分析**: 频域特征识别
• **峰谷特征**: 形态学特征量化

## 3. GUI控制功能 (GUI Control Functions)

### 直接控制命令 (Direct Control Commands)
```python
# 滤波控制
set_filter_parameters(low_cutoff=0.1, high_cutoff=5.0, filter_type='Bandpass')

# 噪声移除
apply_blanking(start_time=10.0, end_time=20.0)

# 峰检测
set_peak_detection_params(prominence=5.0, width_s=0.5)
detect_peaks_valleys(mode='Peak')

# 显示控制
set_plot_visibility(signal_type='primary_dff', visible=True)

# 降采样
set_downsample_factor(factor=50)
```

### 自动参数优化 (Automatic Parameter Optimization)
• **智能建议**: 根据信号特征自动建议参数
• **批量处理**: 一次性应用多个优化
• **效果预测**: 预测参数改变的影响
• **回滚功能**: 支持参数恢复

## 4. 多模态输入 (Multimodal Input)

### 图像理解 (Image Understanding)
• **实时截图**: 自动捕获当前显示的图表
• **图像分析**: 解读信号模式和特征
• **趋势识别**: 识别上升、下降、振荡等模式
• **异常检测**: 发现异常信号和伪影

### 上下文感知 (Context Awareness)
• **数据状态**: 实时了解加载的数据信息
• **分析历史**: 记住之前的分析步骤
• **参数记忆**: 记录使用过的参数设置
• **会话连续**: 保持对话上下文
"""

def create_commands_tab_content():
    """Return content for the commands tab."""
    return """# 命令参考手册 (Command Reference)

## 基础交互命令 (Basic Interaction Commands)

### 数据共享 (Data Sharing)
```
命令: "Share Data Context" 按钮
功能: 共享当前数据的基本信息
包含: 采样率、时长、信号类型、样本数量
示例输出: 
  - Primary Data: 60s, 1000Hz, 60000 samples
  - Visible signals: ΔF/F, Raw, TTL1, TTL2
```

### 图表更新 (Plot Updates)
```
命令: "Update Plot View" 按钮
功能: 共享当前可视化状态
包含: 可见信号、时间范围、振幅范围、检测特征
自动触发: 开启Auto-update时自动更新
```

## GUI控制命令 (GUI Control Commands)

### 1. 滤波控制 (Filter Control)
```python
# 设置带通滤波器
set_filter_parameters(low_cutoff=0.1, high_cutoff=5.0, filter_type='Bandpass')

# 低通滤波器
set_filter_parameters(high_cutoff=2.0, filter_type='Lowpass')

# 高通滤波器
set_filter_parameters(low_cutoff=0.01, filter_type='Highpass')

# 带阻滤波器
set_filter_parameters(low_cutoff=0.1, high_cutoff=0.5, filter_type='Bandstop')
```

### 2. 信号清理 (Signal Cleaning)
```python
# 移除特定时间段的噪声
apply_blanking(start_time=10.0, end_time=20.0)

# 移除多个时间段
apply_blanking(start_time=5.0, end_time=8.0)
apply_blanking(start_time=15.0, end_time=18.0)

# 高级去噪
apply_advanced_denoising(aggressive=True)
apply_advanced_denoising(aggressive=False)
```

### 3. 峰谷检测 (Peak/Valley Detection)
```python
# 设置峰检测参数
set_peak_detection_params(prominence=5.0, width_s=0.5, distance_s=2.0)

# 运行峰检测
detect_peaks_valleys(mode='Peak')

# 运行谷检测
detect_peaks_valleys(mode='Valley')

# 调整敏感度
set_peak_detection_params(prominence=2.0)  # 更敏感
set_peak_detection_params(prominence=10.0) # 更严格
```

### 4. 显示控制 (Display Control)
```python
# 控制信号可见性
set_plot_visibility(signal_type='primary_dff', visible=True)
set_plot_visibility(signal_type='primary_raw', visible=False)
set_plot_visibility(signal_type='secondary_dff', visible=True)
set_plot_visibility(signal_type='primary_ttl1', visible=True)
set_plot_visibility(signal_type='primary_ttl2', visible=False)

# 重置视图
reset_plot_view()
```

### 5. 性能调整 (Performance Tuning)
```python
# 设置降采样因子
set_downsample_factor(factor=50)   # 默认
set_downsample_factor(factor=10)   # 更高精度
set_downsample_factor(factor=100)  # 更快处理
```

## 自然语言命令 (Natural Language Commands)

### 滤波命令示例 (Filter Command Examples)
```
用户输入: "Apply a 2 Hz lowpass filter"
AI执行: set_filter_parameters(high_cutoff=2.0, filter_type='Lowpass')

用户输入: "Remove noise from 10 to 20 seconds"
AI执行: apply_blanking(start_time=10.0, end_time=20.0)

用户输入: "Set peak detection prominence to 3"
AI执行: set_peak_detection_params(prominence=3.0)

用户输入: "Hide the raw signal"
AI执行: set_plot_visibility(signal_type='primary_raw', visible=False)
```

### 分析命令示例 (Analysis Command Examples)
```
"Analyze the signal pattern in the first 30 seconds"
"What's the correlation between channel 1 and 2?"
"Detect all peaks with prominence > 5"
"Explain the PSTH results"
"Suggest optimal filter parameters for this data"
"Is there significant correlation at lag 2 seconds?"
"What's the signal-to-noise ratio?"
"Identify any artifacts or anomalies"
```

## 快捷键 (Keyboard Shortcuts)

```
Ctrl + Enter  : 发送消息 (Send Message)
Enter        : 发送消息 (Send Message)  
Esc          : 清除输入 (Clear Input)
F1           : 显示帮助 (Show Help)
```

## 按钮功能 (Button Functions)

```
Send Message      : 发送消息给AI
Clear Chat        : 清空聊天记录
Share Data Context: 共享数据上下文
Update Plot View  : 更新图表视图
Auto-update ☑    : 自动更新开关
Help             : 显示此帮助
API Settings     : 配置Claude API
```
"""

def create_technical_tab_content():
    """Return content for the technical specifications tab.""" 
    return """# 技术规格说明 (Technical Specifications)

## 系统架构 (System Architecture)

### 核心组件 (Core Components)
```
AI Assistant Panel (ai_assistant_panel.py)
├── Claude API Integration (anthropic)
├── Streaming Text Engine
├── Rich Text Formatter  
├── GUI Control Interface
├── Context Manager
└── Help System
```

### API集成 (API Integration)
```python
# 支持的Claude模型 (Supported Models)
Models = [
    "claude-3-5-sonnet-20241022",  # 首选
    "claude-3-5-sonnet-20240620",  # 备选
    "claude-3-sonnet-20240229",    # 兼容
    "claude-3-haiku-20240307"      # 轻量
]

# API配置 (API Configuration)
max_tokens: 4000
temperature: 0.1
timeout: 120秒
```

### 性能参数 (Performance Parameters)
```python
# 流式显示 (Streaming Display)
stream_speed: 25 字符/秒
chunk_size: max(1, speed // 10)
update_frequency: 10 Hz
typing_indicator_delay: 800ms

# 内存管理 (Memory Management)
max_chat_history: 无限制
max_context_size: 4000 tokens
image_cache_size: 10 MB
plot_resolution: 100 DPI
```

### 数据格式 (Data Formats)
```python
# 聊天记录格式 (Chat History Format)
chat_entry = {
    'timestamp': '2024-01-01T12:00:00.000Z',
    'sender': 'user|assistant|system',
    'message': 'text content'
}

# 数据上下文格式 (Data Context Format)
data_context = {
    'session_info': {
        'has_primary_data': bool,
        'has_secondary_data': bool,
        'downsample_factor': int
    },
    'data_summary': {
        'primary': {
            'duration_seconds': float,
            'sampling_rate': float,
            'num_samples': int,
            'signals_available': list
        }
    },
    'visible_signals': dict,
    'current_analysis': dict
}
```

## 图像处理 (Image Processing)

### 图像捕获 (Image Capture)
```python
# 支持的图像格式
formats = ['PNG']
encoding = 'base64'
compression = 'lossless'
max_size = '10MB'

# 捕获类型 (Capture Types)
capture_types = [
    'main_plot',      # 主图表
    'psth_plot',      # PSTH分析
    'correlation',    # 相关性分析
    'peak_analysis'   # 峰谷分析
]
```

### 图像分析能力 (Image Analysis Capabilities)
```
• 信号模式识别: 上升、下降、振荡、平稳
• 噪声水平评估: 高、中、低噪声识别
• 峰谷特征提取: 数量、形状、分布
• 时频特征分析: 频域成分识别
• 异常检测: 伪影、突变、缺失
• 相关性可视化: 强度、延迟、方向
```

## 错误处理 (Error Handling)

### API错误处理 (API Error Handling)
```python
Error Types:
- API Key Invalid: 显示设置对话框
- Rate Limit: 自动重试 (3次)
- Network Error: 显示错误消息
- Model Unavailable: 自动切换模型
- Context Too Long: 自动截断
```

### 界面错误处理 (UI Error Handling)
```python
Error Recovery:
- Streaming Interrupted: 自动恢复
- Format Error: 降级为纯文本
- Memory Overflow: 清理缓存
- Timer Error: 重置状态
```

## 安全特性 (Security Features)

### 数据保护 (Data Protection)
```
• API密钥加密存储
• 本地数据处理，不上传原始数据
• 仅共享分析摘要和统计信息
• 图像数据临时缓存，会话结束后清理
• 聊天记录本地存储，用户可选清除
```

### 隐私保护 (Privacy Protection)
```
• 不收集用户数据
• 不存储个人信息
• API通信使用HTTPS加密
• 敏感信息脱敏处理
```

## 扩展性 (Extensibility)

### 插件接口 (Plugin Interface)
```python
# 自定义格式化器
class CustomFormatter:
    def format_text(self, text: str) -> str:
        pass

# 自定义分析器
class CustomAnalyzer:
    def analyze_data(self, data: dict) -> dict:
        pass
```

### 配置选项 (Configuration Options)
```python
config = {
    'stream_speed': 25,        # 流式速度
    'auto_update': True,       # 自动更新
    'format_enabled': True,    # 格式化开关
    'image_quality': 'high',   # 图像质量
    'cache_size': 50,         # 缓存大小
    'debug_mode': False       # 调试模式
}
```

## 系统要求 (System Requirements)

### 最低要求 (Minimum Requirements)
```
Python: 3.7+
Tkinter: 内置
Anthropic: 0.3.0+
PIL/Pillow: 8.0+
NumPy: 1.20+
Matplotlib: 3.3+
Memory: 512MB
Disk: 100MB
```

### 推荐配置 (Recommended Configuration)
```
Python: 3.9+
Memory: 2GB+
CPU: 2核心+
Network: 稳定网络连接
Screen: 1920x1080+
```

### 兼容性 (Compatibility)
```
OS: Windows 10+, macOS 10.14+, Linux
GUI: Tkinter (跨平台)
API: Claude 3.x 系列
Browser: 不需要浏览器
```
"""

def create_troubleshooting_tab_content():
    """Return content for the troubleshooting tab."""
    return """# 故障排除指南 (Troubleshooting Guide)

## 常见问题解决 (Common Issues)

### 1. API连接问题 (API Connection Issues)

#### 问题: API Key无效 (Invalid API Key)
```
症状: 红色状态指示器，"API not available"消息
原因: API密钥错误或过期
解决方案:
1. 点击 "API Settings" 按钮
2. 访问 https://console.anthropic.com/
3. 获取新的API密钥
4. 在设置中输入新密钥
5. 点击"Save"测试连接
```

#### 问题: 网络连接错误 (Network Error)
```
症状: "Error communicating with Claude" 消息
原因: 网络连接问题或防火墙阻止
解决方案:
1. 检查网络连接
2. 检查防火墙设置
3. 尝试使用VPN (如果在受限网络)
4. 检查代理设置
5. 重启应用程序
```

#### 问题: 模型不可用 (Model Unavailable)
```
症状: "Model not available" 错误
原因: 请求的Claude模型暂时不可用
解决方案:
1. 系统会自动尝试备用模型
2. 等待几分钟后重试
3. 检查Anthropic服务状态
4. 重新初始化API连接
```

### 2. 界面显示问题 (UI Display Issues)

#### 问题: 文字显示异常 (Text Display Issues)
```
症状: 乱码、格式错误、字体问题
原因: 字体缺失或编码问题
解决方案:
1. 重启应用程序
2. 检查系统字体设置
3. 更新Python和Tkinter
4. 设置正确的系统语言
```

#### 问题: 流式文本卡顿 (Streaming Text Lag)
```
症状: 文字显示延迟或跳跃
原因: 系统性能不足或资源占用高
解决方案:
1. 关闭其他占用资源的程序
2. 增加系统内存
3. 降低降采样因子
4. 清空聊天记录
```

#### 问题: 图表无法显示 (Charts Not Displaying)
```
症状: "无法捕获图表"或空白图像
原因: Matplotlib后端问题或权限不足
解决方案:
1. 确保有数据加载
2. 检查图表是否正常显示
3. 重新生成图表
4. 重启应用程序
```

### 3. 功能操作问题 (Functionality Issues)

#### 问题: AI无法控制GUI (AI Cannot Control GUI)
```
症状: "ACTION:" 命令执行失败
原因: 参数错误或权限问题
解决方案:
1. 检查命令格式是否正确
2. 确保数据已加载
3. 检查参数范围是否合理
4. 重新加载数据
```

#### 问题: 自动更新不工作 (Auto-update Not Working)
```
症状: 图表状态不自动同步
原因: Auto-update开关关闭或事件绑定问题
解决方案:
1. 检查Auto-update复选框状态
2. 手动点击"Update Plot View"
3. 重新切换Auto-update开关
4. 重启应用程序
```

#### 问题: 帮助系统无响应 (Help System Unresponsive)
```
症状: 点击Help按钮无反应
原因: 对话框被阻塞或系统资源不足
解决方案:
1. 按Esc键关闭可能的隐藏对话框
2. 检查任务管理器中的进程
3. 重启应用程序
4. 检查系统内存使用情况
```

## 性能优化 (Performance Optimization)

### 内存优化 (Memory Optimization)
```
问题: 内存使用过高
解决方案:
1. 定期清空聊天记录
2. 调整降采样因子 (增大数值)
3. 减少同时显示的信号数量
4. 关闭不必要的分析图表
5. 重启应用程序释放内存
```

### 响应速度优化 (Response Speed Optimization)
```
问题: AI响应速度慢
解决方案:
1. 检查网络连接质量
2. 简化问题描述
3. 避免上传过大图片
4. 使用更快的Claude模型
5. 减少上下文长度
```

### 界面流畅度优化 (UI Smoothness Optimization)
```
问题: 界面卡顿或响应慢
解决方案:
1. 降低流式文本速度
2. 减少图表复杂度
3. 关闭实时更新
4. 优化系统性能
5. 使用更快的硬件
```

## 数据问题 (Data Issues)

### 数据加载失败 (Data Loading Failure)
```
症状: "No data available" 或加载错误
原因: 文件格式不支持或文件损坏
解决方案:
1. 检查文件格式 (.ppd)
2. 验证文件完整性
3. 重新导出数据文件
4. 检查文件权限
5. 尝试其他数据文件
```

### 采样率问题 (Sampling Rate Issues)
```
症状: 时间轴显示错误或采样率不正确
原因: 文件头信息错误或解析问题
解决方案:
1. 检查原始文件的采样率设置
2. 手动修正降采样因子
3. 重新记录数据确保正确设置
4. 检查数据导出设置
```

## 日志和调试 (Logging and Debugging)

### 启用调试模式 (Enable Debug Mode)
```python
# 在控制台查看详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看API调用详情
print("API Client:", self.claude_client)
print("Model:", self.current_model)
print("Chat History:", len(self.chat_history))
```

### 常用调试命令 (Common Debug Commands)
```python
# 检查数据状态
print("Primary Data:", bool(self.main_window.primary_data))
print("Context:", self.get_current_data_context())

# 检查AI状态
print("Processing:", self.is_processing)
print("Streaming:", self.is_streaming)

# 检查API状态
print("API Key:", bool(self.api_key))
print("Client:", bool(self.claude_client))
```

## 联系支持 (Contact Support)

### 问题报告 (Issue Reporting)
```
报告问题时请包含:
1. 操作系统和版本
2. Python版本
3. 错误消息的完整文本
4. 重现步骤
5. 相关的数据文件(如可分享)
6. 屏幕截图
```

### 获取帮助 (Getting Help)
```
渠道:
1. 应用内Help按钮
2. 技术文档和FAQ
3. 示例对话和命令
4. 在线帮助资源
```
"""

def create_faq_tab_content():
    """Return content for the FAQ tab."""
    return """# 常见问题解答 (Frequently Asked Questions)

## 基础使用 (Basic Usage)

### Q1: 如何开始使用AI助手？
**A:** 
1. 首先配置Claude API密钥 (点击"API Settings")
2. 加载您的光度测量数据文件
3. 点击"Share Data Context"共享数据信息
4. 开始与AI对话，询问分析问题或请求操作

### Q2: 需要什么样的API密钥？
**A:** 
- 需要Anthropic Claude API密钥
- 访问 https://console.anthropic.com/ 注册账户
- 创建API密钥并复制
- 支持Claude 3.x系列所有模型

### Q3: AI能理解哪些类型的问题？
**A:** 
- 信号分析问题: "这个信号有什么特征？"
- 参数优化: "建议最优的滤波参数"
- 结果解释: "解释这个PSTH结果的生物学意义"
- 操作指导: "如何移除10-20秒的噪声？"
- 统计分析: "两个通道间的相关性如何？"

### Q4: 如何让AI控制GUI界面？
**A:** 
- 直接用自然语言描述需求
- 例如: "应用2Hz低通滤波器"
- AI会自动执行相应的GUI操作
- 支持的操作包括滤波、峰检测、显示控制等

## 功能特性 (Features)

### Q5: 流式文本显示是什么？
**A:** 
- 模拟真实打字效果的文本显示
- 字符逐个出现，创造自然对话感受
- 可配置显示速度 (默认25字符/秒)
- 包含思考指示器和打字动画

### Q6: 富文本格式化支持哪些样式？
**A:** 
- **粗体**: \\*\\*文本\\*\\*
- *斜体*: \\*文本\\*
- `代码`: \\`文本\\`
- 标题: # ## ###
- 列表: • 和 1. 2. 3.
- 特殊区域: [SUMMARY], [KEY POINTS], [ANALYSIS]

### Q7: Auto-update功能是什么？
**A:** 
- 自动同步当前图表状态给AI
- 在进行滤波、峰检测等操作后自动更新
- AI能实时了解您的分析进展
- 可通过复选框开启/关闭

### Q8: AI能看到我的图表吗？
**A:** 
- 是的，AI可以分析您当前显示的图表
- 包括主图表、PSTH、相关性分析等
- 自动捕获并发送图像给Claude
- 能识别信号模式、峰谷、趋势等

## 数据和隐私 (Data & Privacy)

### Q9: 我的数据安全吗？
**A:** 
- 原始数据不会上传到云端
- 仅发送分析摘要和图表截图
- API密钥本地加密存储
- 聊天记录保存在本地
- 可随时清空聊天历史

### Q10: 数据处理是实时的吗？
**A:** 
- 图表捕获和分析是实时的
- API响应取决于网络和服务器状态
- 本地GUI操作是即时的
- 上下文同步自动进行

### Q11: 支持哪些数据格式？
**A:** 
- 主要支持.ppd格式 (光度测量数据)
- 包含多通道信号: ΔF/F, Raw, TTL等
- 支持高采样率数据 (自动降采样优化)
- 兼容不同厂商的数据格式

## 技术问题 (Technical Issues)

### Q12: 为什么AI响应很慢？
**A:** 
- 网络连接质量影响响应时间
- 复杂图像分析需要更多处理时间
- 长对话上下文会增加处理时间
- 建议简化问题或检查网络连接

### Q13: 如何提高分析准确性？
**A:** 
- 提供清晰的数据上下文
- 使用具体的科学术语
- 分享相关的实验设计信息
- 定期更新图表状态
- 询问具体而非宽泛的问题

### Q14: 支持批量分析吗？
**A:** 
- 当前版本主要支持单文件分析
- 可以通过对话指导多步骤分析
- 支持参数化批量操作
- 未来版本将增加批量处理功能

### Q15: 如何保存分析结果？
**A:** 
- 聊天记录自动保存在本地
- 可以复制AI的分析文本
- 截图保存重要的对话内容
- 导出分析参数和设置

## 高级使用 (Advanced Usage)

### Q16: 如何编写有效的分析请求？
**A:** 
好的请求示例:
- "分析前30秒的信号模式，重点关注峰的频率和幅度"
- "比较两个通道在刺激后的响应差异"
- "建议优化当前PSTH分析的参数设置"

避免的请求:
- "分析这个" (太模糊)
- "有什么问题吗？" (没有具体指向)

### Q17: 如何最大化AI的分析能力？
**A:** 
- 保持数据上下文最新
- 提供实验背景信息
- 使用专业术语
- 分步骤进行复杂分析
- 结合可视化和数值分析

### Q18: 能处理多通道数据吗？
**A:** 
- 支持主/次双通道数据
- 可分析通道间相关性
- 支持TTL信号分析
- 可进行跨通道事件检测
- 提供多维度统计分析

### Q19: 如何进行时间序列分析？
**A:** 
- 使用PSTH分析刺激锁定响应
- 相关性分析识别时间延迟
- 峰谷分析量化时间特征
- 滑动窗口分析动态变化
- 频域分析识别周期性

## 实验设计支持 (Experimental Design)

### Q20: AI能帮助实验设计吗？
**A:** 
- 分析现有数据提供设计建议
- 推荐采样参数和滤波设置
- 评估信号质量和噪声水平
- 建议对照实验设计
- 统计功效分析指导

### Q21: 如何解释统计结果？
**A:** 
- AI提供统计显著性解释
- 结合生物学背景解读结果
- 评估效应量和临床意义
- 建议后续验证实验
- 讨论结果的局限性

### Q22: 支持哪些统计方法？
**A:** 
- 描述性统计 (均值、标准差等)
- 假设检验 (t检验、ANOVA等)
- 相关性分析 (Pearson, Spearman)
- 时间序列分析
- 非参数检验
- 多重比较校正

## 故障排除 (Troubleshooting)

### Q23: 为什么看不到AI的回复？
**A:** 
- 检查API密钥是否正确
- 确认网络连接正常
- 查看是否有错误消息
- 尝试重新发送消息
- 重启应用程序

### Q24: 格式显示异常怎么办？
**A:** 
- 重启应用程序
- 检查系统字体设置
- 更新Python和相关库
- 清空聊天记录重新开始
- 检查显示器分辨率设置

### Q25: 如何获得更多帮助？
**A:** 
- 查看完整的技术文档
- 使用应用内示例对话
- 尝试不同的问题表述方式
- 检查网络连接和API状态
- 参考故障排除指南
"""