"""
知识库数据

包含营养和运动相关的专业知识，用于RAG（检索增强生成）
"""

# 营养知识
NUTRITION_KNOWLEDGE = [
    {
        "id": "nutrition_001",
        "content": "蛋白质是肌肉生长和修复的重要营养素。建议每公斤体重摄入1.6-2.2克蛋白质，优质蛋白质来源包括鸡胸肉、鱼类、蛋类、豆类和乳制品。",
        "category": "nutrition",
        "topic": "protein",
        "tags": ["蛋白质", "增肌", "营养素"]
    },
    {
        "id": "nutrition_002",
        "content": "碳水化合物是身体的主要能量来源。建议选择复合碳水化合物如燕麦、糙米、红薯、全麦面包，避免过多精制糖和白面包。",
        "category": "nutrition",
        "topic": "carbohydrates",
        "tags": ["碳水化合物", "能量", "主食"]
    },
    {
        "id": "nutrition_003",
        "content": "健康脂肪对激素分泌和细胞功能至关重要。推荐来源包括牛油果、坚果、橄榄油、深海鱼类。每日脂肪摄入应占总热量的20-35%。",
        "category": "nutrition",
        "topic": "fats",
        "tags": ["脂肪", "健康脂肪", "营养素"]
    },
    {
        "id": "nutrition_004",
        "content": "减脂期间需要创造热量缺口，建议每日热量摄入比TDEE（总能量消耗）少300-500卡路里。保持高蛋白摄入以保护肌肉，适量减少碳水和脂肪。",
        "category": "nutrition",
        "topic": "weight_loss",
        "tags": ["减脂", "热量缺口", "饮食计划"]
    },
    {
        "id": "nutrition_005",
        "content": "增肌期间需要热量盈余，建议每日热量摄入比TDEE多200-300卡路里。确保充足的蛋白质摄入（每公斤体重2克以上），配合力量训练。",
        "category": "nutrition",
        "topic": "muscle_gain",
        "tags": ["增肌", "热量盈余", "饮食计划"]
    },
    {
        "id": "nutrition_006",
        "content": "水分对身体机能至关重要。建议每日饮水量为体重（公斤）×30-40毫升。运动时需要额外补充水分，每小时运动补充500-1000毫升。",
        "category": "nutrition",
        "topic": "hydration",
        "tags": ["水分", "补水", "健康"]
    },
    {
        "id": "nutrition_007",
        "content": "维生素和矿物质是微量营养素，对身体健康至关重要。建议通过多样化饮食获取，包括各色蔬菜、水果、全谷物和瘦肉。",
        "category": "nutrition",
        "topic": "vitamins_minerals",
        "tags": ["维生素", "矿物质", "微量营养素"]
    },
    {
        "id": "nutrition_008",
        "content": "膳食纤维有助于消化健康和血糖控制。建议每日摄入25-35克纤维，来源包括蔬菜、水果、全谷物、豆类和坚果。",
        "category": "nutrition",
        "topic": "fiber",
        "tags": ["膳食纤维", "消化", "健康"]
    },
    {
        "id": "nutrition_009",
        "content": "餐前餐后的营养时机很重要。运动前1-2小时摄入碳水化合物提供能量，运动后30分钟内摄入蛋白质和碳水促进恢复。",
        "category": "nutrition",
        "topic": "meal_timing",
        "tags": ["营养时机", "运动营养", "恢复"]
    },
    {
        "id": "nutrition_010",
        "content": "健康的饮食应该多样化和均衡。建议每餐包含蛋白质、复合碳水、健康脂肪和大量蔬菜，避免过度加工食品。",
        "category": "nutrition",
        "topic": "balanced_diet",
        "tags": ["均衡饮食", "健康饮食", "营养"]
    }
]

# 运动知识
EXERCISE_KNOWLEDGE = [
    {
        "id": "exercise_001",
        "content": "有氧运动可以有效燃烧脂肪和提高心肺功能。建议每周进行3-5次，每次30-60分钟。常见有氧运动包括跑步、游泳、骑行、跳绳。",
        "category": "exercise",
        "topic": "cardio",
        "tags": ["有氧运动", "减脂", "心肺功能"]
    },
    {
        "id": "exercise_002",
        "content": "力量训练可以增加肌肉量、提高基础代谢率和改善身体线条。建议每周进行3-4次，每次45-60分钟，训练各大肌群。",
        "category": "exercise",
        "topic": "strength_training",
        "tags": ["力量训练", "增肌", "代谢"]
    },
    {
        "id": "exercise_003",
        "content": "HIIT（高强度间歇训练）结合了有氧和无氧运动，可以在短时间内高效燃脂。建议每周2-3次，每次20-30分钟。",
        "category": "exercise",
        "topic": "hiit",
        "tags": ["HIIT", "高强度", "燃脂"]
    },
    {
        "id": "exercise_004",
        "content": "拉伸和柔韧性训练可以提高关节活动度、预防受伤、缓解肌肉紧张。建议每次运动后进行10-15分钟静态拉伸。",
        "category": "exercise",
        "topic": "stretching",
        "tags": ["拉伸", "柔韧性", "恢复"]
    },
    {
        "id": "exercise_005",
        "content": "核心训练对姿势、平衡和整体力量至关重要。推荐动作包括平板支撑、卷腹、俄罗斯转体、鸟狗式。每周3-4次。",
        "category": "exercise",
        "topic": "core",
        "tags": ["核心训练", "腹肌", "稳定性"]
    },
    {
        "id": "exercise_006",
        "content": "渐进式超负荷是肌肉生长的关键原则。逐步增加训练重量、次数或组数，给肌肉持续的刺激。建议每1-2周增加5-10%负荷。",
        "category": "exercise",
        "topic": "progressive_overload",
        "tags": ["渐进超负荷", "增肌", "训练原则"]
    },
    {
        "id": "exercise_007",
        "content": "充足的休息和恢复对训练效果至关重要。建议每个肌群训练后休息48-72小时，保证每晚7-9小时睡眠。",
        "category": "exercise",
        "topic": "recovery",
        "tags": ["恢复", "休息", "睡眠"]
    },
    {
        "id": "exercise_008",
        "content": "复合动作如深蹲、硬拉、卧推、引体向上可以同时训练多个肌群，提高训练效率。建议作为训练计划的核心动作。",
        "category": "exercise",
        "topic": "compound_movements",
        "tags": ["复合动作", "力量训练", "效率"]
    },
    {
        "id": "exercise_009",
        "content": "运动前热身可以提高体温、增加关节活动度、预防受伤。建议进行5-10分钟动态热身，包括关节活动和轻度有氧。",
        "category": "exercise",
        "topic": "warmup",
        "tags": ["热身", "预防受伤", "准备"]
    },
    {
        "id": "exercise_010",
        "content": "训练强度应该根据个人水平调整。初学者从低强度开始，逐步提高。使用RPE（主观疲劳感）量表评估强度，目标7-8/10。",
        "category": "exercise",
        "topic": "intensity",
        "tags": ["训练强度", "个性化", "进阶"]
    },
    {
        "id": "exercise_011",
        "content": "功能性训练模拟日常动作，提高实用力量和协调性。包括深蹲、弓步、推拉动作、旋转动作等多平面运动。",
        "category": "exercise",
        "topic": "functional_training",
        "tags": ["功能性训练", "实用力量", "协调"]
    },
    {
        "id": "exercise_012",
        "content": "有氧运动的心率区间很重要。燃脂区间为最大心率的60-70%，提高心肺功能为70-85%。最大心率约为220减去年龄。",
        "category": "exercise",
        "topic": "heart_rate",
        "tags": ["心率", "有氧", "强度"]
    }
]

# 健康和生活方式知识
LIFESTYLE_KNOWLEDGE = [
    {
        "id": "lifestyle_001",
        "content": "充足的睡眠对减脂和增肌都至关重要。睡眠不足会影响激素分泌、降低代谢、增加食欲。建议每晚7-9小时高质量睡眠。",
        "category": "lifestyle",
        "topic": "sleep",
        "tags": ["睡眠", "恢复", "激素"]
    },
    {
        "id": "lifestyle_002",
        "content": "压力管理对健康和体重管理很重要。慢性压力会导致皮质醇升高，影响脂肪代谢。建议通过冥想、瑜伽、深呼吸等方式减压。",
        "category": "lifestyle",
        "topic": "stress",
        "tags": ["压力", "皮质醇", "心理健康"]
    },
    {
        "id": "lifestyle_003",
        "content": "设定SMART目标（具体、可衡量、可实现、相关、有时限）可以提高成功率。将大目标分解为小目标，定期评估进度。",
        "category": "lifestyle",
        "topic": "goal_setting",
        "tags": ["目标设定", "SMART", "成功"]
    },
    {
        "id": "lifestyle_004",
        "content": "保持一致性比完美更重要。建立可持续的饮食和运动习惯，允许偶尔的灵活性，避免全有或全无的思维。",
        "category": "lifestyle",
        "topic": "consistency",
        "tags": ["一致性", "习惯", "可持续"]
    },
    {
        "id": "lifestyle_005",
        "content": "记录饮食和训练可以提高自我意识和责任感。使用应用或日记追踪进度，识别模式和需要改进的地方。",
        "category": "lifestyle",
        "topic": "tracking",
        "tags": ["记录", "追踪", "自我意识"]
    }
]

# 合并所有知识
ALL_KNOWLEDGE = NUTRITION_KNOWLEDGE + EXERCISE_KNOWLEDGE + LIFESTYLE_KNOWLEDGE


def get_all_knowledge():
    """获取所有知识库数据"""
    return ALL_KNOWLEDGE


def get_knowledge_by_category(category: str):
    """
    按类别获取知识
    
    Args:
        category: 类别（nutrition/exercise/lifestyle）
        
    Returns:
        知识列表
    """
    return [k for k in ALL_KNOWLEDGE if k['category'] == category]


def get_knowledge_by_topic(topic: str):
    """
    按主题获取知识
    
    Args:
        topic: 主题
        
    Returns:
        知识列表
    """
    return [k for k in ALL_KNOWLEDGE if k['topic'] == topic]
