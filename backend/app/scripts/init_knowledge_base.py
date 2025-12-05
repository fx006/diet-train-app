"""
知识库初始化脚本

将营养和运动知识向量化并存储到ChromaDB
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.data.knowledge_base import get_all_knowledge
from app.services.vector_db import get_vector_db


def init_knowledge_base(force_reset: bool = False):
    """
    初始化知识库
    
    Args:
        force_reset: 是否强制重置（清空现有知识）
    """
    print("开始初始化知识库...")
    
    # 获取向量数据库服务
    vector_db = get_vector_db()
    
    # 如果需要，清空现有知识
    if force_reset:
        print("清空现有知识库...")
        try:
            vector_db.client.delete_collection("knowledge")
            vector_db._init_collections()
            print("✓ 已清空现有知识库")
        except Exception as e:
            print(f"清空知识库时出错: {e}")
    
    # 获取所有知识
    all_knowledge = get_all_knowledge()
    print(f"准备向量化 {len(all_knowledge)} 条知识...")
    
    # 批量添加知识
    knowledge_items = []
    for item in all_knowledge:
        knowledge_items.append({
            'id': item['id'],
            'content': item['content'],
            'metadata': {
                'category': item['category'],
                'topic': item['topic'],
                'tags': ','.join(item['tags'])  # ChromaDB metadata 不支持列表，转为字符串
            }
        })
    
    try:
        vector_db.add_knowledge_batch(knowledge_items)
        print(f"✓ 成功向量化并存储 {len(knowledge_items)} 条知识")
    except Exception as e:
        print(f"✗ 向量化知识时出错: {e}")
        return False
    
    # 验证
    stats = vector_db.get_collection_stats()
    print(f"\n知识库统计:")
    print(f"  - 对话: {stats['conversations']} 条")
    print(f"  - 计划: {stats['plans']} 条")
    print(f"  - 知识: {stats['knowledge']} 条")
    
    # 测试搜索
    print("\n测试知识库搜索...")
    test_queries = [
        "如何增肌",
        "减脂饮食",
        "有氧运动"
    ]
    
    for query in test_queries:
        results = vector_db.search_knowledge(query, n_results=2)
        print(f"\n查询: '{query}'")
        if results:
            print(f"  找到 {len(results)} 条相关知识:")
            for i, result in enumerate(results, 1):
                content = result['document'][:50] + "..." if len(result['document']) > 50 else result['document']
                print(f"    {i}. {content}")
        else:
            print("  未找到相关知识")
    
    print("\n✓ 知识库初始化完成！")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化知识库")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="强制重置知识库（清空现有数据）"
    )
    
    args = parser.parse_args()
    
    success = init_knowledge_base(force_reset=args.reset)
    sys.exit(0 if success else 1)
