# Claude-Style Skills System for LangChain

一个模块化、可扩展的 Skill 管理系统，为 LangChain/LangGraph 实现类似 Claude Skills 的动态工具加载机制。
<img width="1910" height="915" alt="425535ba89a897f49ee33e1ba7215c6" src="https://github.com/user-attachments/assets/5be5cef4-60c5-4097-898b-2a5fcba17e3f" />

## ✨ 核心特性

- 🔄 **动态 Skill 加载**：运行时按需激活能力，减少 token 消耗
- 🎯 **智能工具过滤**：中间件自动过滤无关工具，降低认知负荷
- 📦 **模块化设计**：每个 Skill 独立封装，易于开发和维护
- ⚙️ **灵活状态管理**：支持 Replace/Accumulate/FIFO 三种模式
- 🔐 **权限控制**：基于可见性和权限的访问控制
- 🚀 **高性能**：减少延迟和错误率，提升 Agent 决策质量

## 📦 安装

```bash
# 克隆仓库
cd skill_system

# 安装依赖
pip install langchain langgraph langchain-openai pdfplumber pandas numpy matplotlib
```


## 🎓 最佳实践

### 1. Skill 设计原则

- **单一职责**：每个 Skill 专注一个领域
- **独立性**：Skill 之间应该解耦
- **清晰命名**：Skill 名称应描述性强
- **完善文档**：提供详细的 instructions.md

### 2. System Prompt 优化

```python
custom_prompt = """
你是一个专业的 AI 助手。

重要规则：
1. 在使用工具前，先检查是否需要加载对应的 Skill
2. 如果需要 PDF 处理，先调用 skill_pdf_processing
3. 如果需要数据分析，先调用 skill_data_analysis
4. Skill 一旦加载，工具即可使用

工作流程：
分析任务 → 识别所需 Skill → 加载 Skill → 使用工具 → 完成任务
"""

agent = create_skill_agent(
    model=ChatOpenAI(model="gpt-4"),
    custom_system_prompt=custom_prompt
)
```

### 3. 状态模式选择

- **Replace 模式**：简单任务，每次只需一个 Skill
- **Accumulate 模式**：复杂任务，需要多个 Skill 协作
- **FIFO 模式**：控制成本，限制同时加载数量



## 🤝 贡献

欢迎贡献新的 Skills 或改进核心功能！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingSkill`)
3. 提交更改 (`git commit -m 'Add AmazingSkill'`)
4. 推送到分支 (`git push origin feature/AmazingSkill`)
5. 创建 Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

本项目灵感来自：
- [Anthropic Claude Skills](https://claude.com/blog/skills)
- [Building Claude-Style Skills in LangChain v1](https://www.linkedin.com/pulse/building-claude-style-skills-langchain-v1-batiste-roger-e5pdf)

## 📧 联系

- 作者：maifree
- 项目：[GitHub Repository](https://github.com/maifree123)
- 问题反馈：[Issues](https://github.com/maifree123/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
