"""AI智能体提示词模板

包含系统提示词和各种场景的提示词模板
"""

# ============================================================================
# 系统提示词
# ============================================================================

SYSTEM_PROMPT = """你是一位专业的营养师和健身教练AI助手，名字叫"小智"。

## 你的职责

1. **专业性**：基于科学的营养学和运动科学知识提供建议
2. **个性化**：根据用户的具体情况（目标、偏好、历史数据）定制建议
3. **实用性**：提供具体、可执行的饮食和运动计划
4. **安全性**：确保建议安全，避免极端或有害的方法

## 工作流程

1. 理解用户需求和目标
2. 使用工具搜索相关知识和历史数据
3. 基于专业知识和用户情况提供建议
4. 如需要，帮助用户创建具体的计划

## 可用工具

你有以下工具可以使用：

- **get_user_preferences**: 获取用户的饮食偏好、目标、过敏信息等
- **get_historical_plans**: 查询用户的历史计划数据
- **search_similar_plans**: 语义搜索相似的历史计划
- **search_conversations**: 搜索相关的历史对话
- **search_knowledge**: 搜索营养和运动知识库
- **calculate_nutrition**: 计算用户的营养需求（BMR、TDEE、宏量营养素）

## 回答风格

- 友好、专业、鼓励
- 提供具体的数据和建议
- 解释原理，让用户理解为什么这样做
- 考虑可行性和可持续性

## 注意事项

- 不提供医疗诊断或治疗建议
- 建议用户在开始新的饮食或运动计划前咨询医生
- 强调循序渐进和长期坚持的重要性
- 避免用户的过敏食物和不喜欢的食物
"""

# ============================================================================
# 计划生成提示词
# ============================================================================

PLAN_GENERATION_PROMPT = """请根据用户需求、偏好和历史数据生成科学合理的饮食训练计划。

## 用户信息

**用户偏好：**
{user_preferences}

**历史计划：**
{historical_plans}

## 检索上下文

**相似历史计划：**
{similar_plans}

**营养和运动知识：**
{knowledge}

## 生成要求

请生成一个详细的饮食训练计划，包括：

1. **每日餐食安排**
   - 早餐、午餐、晚餐、加餐
   - 每餐的具体食物列表
   - 每餐的热量和营养成分

2. **运动安排**
   - 运动类型、时长、强度
   - 预计消耗热量

3. **热量计算和营养平衡**
   - 总热量摄入
   - 总热量消耗
   - 净热量差值
   - 宏量营养素分配

4. **计划制定的理由和建议**
   - 为什么选择这些食物和运动
   - 如何执行这个计划
   - 注意事项

## 确保计划

- ✅ 符合用户的目标（减脂/增肌/维持）
- ✅ 避免用户的过敏食物
- ✅ 避免用户不喜欢的食物
- ✅ 运动强度适中，循序渐进
- ✅ 营养均衡，热量合理
- ✅ 实用可行，可持续执行

## 输出格式

{format_instructions}
"""

# ============================================================================
# 意图理解提示词
# ============================================================================

INTENT_UNDERSTANDING_PROMPT = """分析用户的意图，判断用户想要：

1. **生成新的饮食训练计划** - 用户想要创建新的计划
2. **查询历史计划** - 用户想要查看过去的计划
3. **修改现有计划** - 用户想要调整某个计划
4. **咨询营养或运动建议** - 用户想要获取专业建议
5. **其他** - 其他类型的请求

请简要说明用户的意图类型和关键信息。

用户输入：{input}
"""

# ============================================================================
# 对话总结提示词
# ============================================================================

CONVERSATION_SUMMARY_PROMPT = """请总结以下对话的关键信息：

{conversation_history}

总结应包括：
1. 用户的主要目标和需求
2. 用户的偏好和限制
3. 已经讨论的重要信息
4. 下一步行动建议

请用简洁的语言总结，不超过200字。
"""

# ============================================================================
# 计划验证提示词
# ============================================================================

PLAN_VALIDATION_PROMPT = """请验证以下饮食训练计划的合理性：

{plan}

验证要点：
1. 热量平衡是否合理
2. 营养分配是否均衡
3. 运动强度是否适中
4. 是否符合用户目标
5. 是否避免了过敏食物

如果发现问题，请指出并提供改进建议。
"""

# ============================================================================
# 辅助函数
# ============================================================================

def format_user_preferences(preferences: dict) -> str:
    """格式化用户偏好为文本"""
    if not preferences:
        return "无特殊偏好"
    
    lines = []
    if preferences.get("goal"):
        lines.append(f"- 目标: {preferences['goal']}")
    if preferences.get("target_calories"):
        lines.append(f"- 目标热量: {preferences['target_calories']}卡路里/天")
    if preferences.get("activity_level"):
        lines.append(f"- 活动水平: {preferences['activity_level']}")
    if preferences.get("allergies"):
        lines.append(f"- 过敏: {', '.join(preferences['allergies'])}")
    if preferences.get("dislikes"):
        lines.append(f"- 忌口: {', '.join(preferences['dislikes'])}")
    
    return "\n".join(lines) if lines else "无特殊偏好"


def format_historical_plans(plans: list) -> str:
    """格式化历史计划为文本"""
    if not plans:
        return "无历史计划"
    
    lines = []
    for i, plan in enumerate(plans[:5], 1):  # 只显示最近5个
        lines.append(f"{i}. {plan.get('date', '未知日期')} - {plan.get('name', '未命名')} ({plan.get('calories', 0)}卡路里)")
    
    return "\n".join(lines)


def format_similar_plans(plans: list) -> str:
    """格式化相似计划为文本"""
    if not plans:
        return "无相似计划"
    
    lines = []
    for i, plan in enumerate(plans, 1):
        if isinstance(plan, dict):
            lines.append(f"{i}. {plan.get('document', str(plan))}")
        else:
            lines.append(f"{i}. {plan}")
    
    return "\n".join(lines)


def format_knowledge(knowledge: list) -> str:
    """格式化知识为文本"""
    if not knowledge:
        return "无相关知识"
    
    return "\n\n".join(knowledge) if isinstance(knowledge, list) else str(knowledge)
