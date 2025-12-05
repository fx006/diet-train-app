"""
计划管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import date, datetime

from app.database import get_db
from app.repositories.plan_repository import PlanRepository
from app.models.plan import Plan


router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("/history")
async def get_history(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取历史记录日期列表
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选
        db: 数据库会话
        
    Returns:
        包含所有已记录日期的列表
        
    Raises:
        HTTPException: 日期格式错误
        
    验证: 需求 9.1
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 解析日期范围（如果提供）
        start = None
        end = None
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail={
                    "error": "日期格式错误",
                    "message": f"开始日期格式应为 YYYY-MM-DD，收到: {start_date}",
                    "code": "INVALID_DATE_FORMAT"
                })
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail={
                    "error": "日期格式错误",
                    "message": f"结束日期格式应为 YYYY-MM-DD，收到: {end_date}",
                    "code": "INVALID_DATE_FORMAT"
                })
        
        # 验证日期范围
        if start and end and start > end:
            raise HTTPException(status_code=400, detail={
                "error": "日期范围错误",
                "message": "开始日期不能晚于结束日期",
                "code": "INVALID_DATE_RANGE"
            })
        
        # 获取所有计划的日期
        all_plans = plan_repo.get_all()
        
        # 提取唯一日期并过滤
        unique_dates = set()
        for plan in all_plans:
            plan_date = plan.date
            
            # 应用日期范围过滤
            if start and plan_date < start:
                continue
            if end and plan_date > end:
                continue
            
            unique_dates.add(plan_date)
        
        # 转换为字符串列表并排序
        date_list = sorted([d.strftime('%Y-%m-%d') for d in unique_dates])
        
        return {
            'dates': date_list,
            'total_days': len(date_list),
            'start_date': start_date,
            'end_date': end_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.get("/{date}")
async def get_plans_by_date(
    date: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定日期的计划
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
        db: 数据库会话
        
    Returns:
        包含餐食和运动的计划数据
        
    Raises:
        HTTPException: 日期格式错误
    """
    try:
        # 解析日期
        try:
            plan_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail={
                "error": "日期格式错误",
                "message": f"日期格式应为 YYYY-MM-DD，收到: {date}",
                "code": "INVALID_DATE_FORMAT"
            })
        
        # 查询计划
        plan_repo = PlanRepository(db)
        plans = plan_repo.get_by_date(plan_date)
        
        # 分离餐食和运动
        meals = []
        exercises = []
        
        for plan in plans:
            plan_dict = {
                'id': plan.id,
                'date': plan.date.strftime('%Y-%m-%d'),
                'name': plan.name,
                'calories': plan.calories,
                'completed': plan.completed,
                'created_at': plan.created_at.isoformat() if plan.created_at else None,
                'updated_at': plan.updated_at.isoformat() if plan.updated_at else None
            }
            
            if plan.type == 'meal':
                meals.append(plan_dict)
            elif plan.type == 'exercise':
                plan_dict['duration'] = plan.duration
                plan_dict['actual_duration'] = plan.actual_duration
                exercises.append(plan_dict)
        
        return {
            'date': date,
            'meals': meals,
            'exercises': exercises,
            'total_items': len(plans)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.get("/stats/{date}")
async def get_stats_by_date(
    date: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定日期的统计数据
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
        db: 数据库会话
        
    Returns:
        统计数据（总热量摄入、消耗、净值等）
        
    Raises:
        HTTPException: 日期格式错误
    """
    try:
        # 解析日期
        try:
            plan_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail={
                "error": "日期格式错误",
                "message": f"日期格式应为 YYYY-MM-DD，收到: {date}",
                "code": "INVALID_DATE_FORMAT"
            })
        
        # 查询计划
        plan_repo = PlanRepository(db)
        plans = plan_repo.get_by_date(plan_date)
        
        # 计算统计数据
        total_calories_intake = 0.0
        total_calories_burned = 0.0
        total_exercise_duration = 0
        completed_count = 0
        
        for plan in plans:
            if plan.type == 'meal':
                total_calories_intake += plan.calories or 0
            elif plan.type == 'exercise':
                total_calories_burned += plan.calories or 0
                total_exercise_duration += plan.duration or 0
            
            if plan.completed:
                completed_count += 1
        
        # 计算净热量
        net_calories = total_calories_intake - total_calories_burned
        
        # 计算完成率
        total_items = len(plans)
        completion_rate = (completed_count / total_items * 100) if total_items > 0 else 0
        
        return {
            'date': date,
            'total_calories_intake': round(total_calories_intake, 2),
            'total_calories_burned': round(total_calories_burned, 2),
            'net_calories': round(net_calories, 2),
            'total_exercise_duration': total_exercise_duration,
            'total_items': total_items,
            'completed_items': completed_count,
            'completion_rate': round(completion_rate, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.post("")
async def create_plan(
    plan_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建新的计划项目
    
    Args:
        plan_data: 计划数据
        db: 数据库会话
        
    Returns:
        创建的计划项目
        
    Raises:
        HTTPException: 数据验证失败
    """
    try:
        # 验证必需字段
        required_fields = ['date', 'type', 'name', 'calories']
        for field in required_fields:
            if field not in plan_data:
                raise HTTPException(status_code=400, detail={
                    "error": "数据验证失败",
                    "message": f"缺少必需字段: {field}",
                    "code": "MISSING_REQUIRED_FIELD"
                })
        
        # 验证名称不为空
        if not plan_data['name'] or not plan_data['name'].strip():
            raise HTTPException(status_code=400, detail={
                "error": "数据验证失败",
                "message": "名称不能为空",
                "code": "INVALID_NAME"
            })
        
        # 验证热量为非负数
        try:
            calories = float(plan_data['calories'])
            if calories < 0:
                raise HTTPException(status_code=400, detail={
                    "error": "数据验证失败",
                    "message": f"热量不能为负数: {calories}",
                    "code": "INVALID_CALORIES"
                })
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail={
                "error": "数据验证失败",
                "message": f"热量必须是数字: {plan_data['calories']}",
                "code": "INVALID_CALORIES"
            })
        
        # 解析日期
        try:
            plan_date = datetime.strptime(plan_data['date'], '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail={
                "error": "数据验证失败",
                "message": f"日期格式错误: {plan_data['date']}",
                "code": "INVALID_DATE_FORMAT"
            })
        
        # 验证类型
        if plan_data['type'] not in ['meal', 'exercise']:
            raise HTTPException(status_code=400, detail={
                "error": "数据验证失败",
                "message": f"无效的类型: {plan_data['type']}，应为 'meal' 或 'exercise'",
                "code": "INVALID_TYPE"
            })
        
        # 验证运动项目的时长
        duration = plan_data.get('duration')
        if duration is not None:
            try:
                duration = int(duration)
                if duration < 0:
                    raise HTTPException(status_code=400, detail={
                        "error": "数据验证失败",
                        "message": f"时长不能为负数: {duration}",
                        "code": "INVALID_DURATION"
                    })
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail={
                    "error": "数据验证失败",
                    "message": f"时长必须是整数: {plan_data.get('duration')}",
                    "code": "INVALID_DURATION"
                })
        
        # 创建计划
        plan = Plan(
            date=plan_date,
            type=plan_data['type'],
            name=plan_data['name'].strip(),
            calories=calories,
            duration=duration,
            completed=plan_data.get('completed', False),
            actual_duration=plan_data.get('actual_duration')
        )
        
        plan_repo = PlanRepository(db)
        created_plan = plan_repo.create(plan)
        
        return {
            'id': created_plan.id,
            'date': created_plan.date.strftime('%Y-%m-%d'),
            'type': created_plan.type,
            'name': created_plan.name,
            'calories': created_plan.calories,
            'duration': created_plan.duration,
            'completed': created_plan.completed,
            'actual_duration': created_plan.actual_duration,
            'created_at': created_plan.created_at.isoformat() if created_plan.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.put("/{plan_id}")
async def update_plan(
    plan_id: int,
    plan_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新计划项目
    
    Args:
        plan_id: 计划ID
        plan_data: 更新的数据
        db: 数据库会话
        
    Returns:
        更新后的计划项目
        
    Raises:
        HTTPException: 计划不存在或数据验证失败
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 查询计划
        plan = plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail={
                "error": "计划不存在",
                "message": f"未找到ID为 {plan_id} 的计划",
                "code": "PLAN_NOT_FOUND"
            })
        
        # 更新字段并验证
        if 'name' in plan_data:
            if not plan_data['name'] or not plan_data['name'].strip():
                raise HTTPException(status_code=400, detail={
                    "error": "数据验证失败",
                    "message": "名称不能为空",
                    "code": "INVALID_NAME"
                })
            plan.name = plan_data['name'].strip()
        
        if 'calories' in plan_data:
            try:
                calories = float(plan_data['calories'])
                if calories < 0:
                    raise HTTPException(status_code=400, detail={
                        "error": "数据验证失败",
                        "message": f"热量不能为负数: {calories}",
                        "code": "INVALID_CALORIES"
                    })
                plan.calories = calories
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail={
                    "error": "数据验证失败",
                    "message": f"热量必须是数字: {plan_data['calories']}",
                    "code": "INVALID_CALORIES"
                })
        
        if 'duration' in plan_data:
            if plan_data['duration'] is not None:
                try:
                    duration = int(plan_data['duration'])
                    if duration < 0:
                        raise HTTPException(status_code=400, detail={
                            "error": "数据验证失败",
                            "message": f"时长不能为负数: {duration}",
                            "code": "INVALID_DURATION"
                        })
                    plan.duration = duration
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail={
                        "error": "数据验证失败",
                        "message": f"时长必须是整数: {plan_data['duration']}",
                        "code": "INVALID_DURATION"
                    })
            else:
                plan.duration = None
        
        if 'completed' in plan_data:
            plan.completed = plan_data['completed']
        
        if 'actual_duration' in plan_data:
            if plan_data['actual_duration'] is not None:
                try:
                    actual_duration = int(plan_data['actual_duration'])
                    if actual_duration < 0:
                        raise HTTPException(status_code=400, detail={
                            "error": "数据验证失败",
                            "message": f"实际时长不能为负数: {actual_duration}",
                            "code": "INVALID_ACTUAL_DURATION"
                        })
                    plan.actual_duration = actual_duration
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail={
                        "error": "数据验证失败",
                        "message": f"实际时长必须是整数: {plan_data['actual_duration']}",
                        "code": "INVALID_ACTUAL_DURATION"
                    })
            else:
                plan.actual_duration = None
        
        # 保存更新
        updated_plan = plan_repo.update(plan)
        
        return {
            'id': updated_plan.id,
            'date': updated_plan.date.strftime('%Y-%m-%d'),
            'type': updated_plan.type,
            'name': updated_plan.name,
            'calories': updated_plan.calories,
            'duration': updated_plan.duration,
            'completed': updated_plan.completed,
            'actual_duration': updated_plan.actual_duration,
            'updated_at': updated_plan.updated_at.isoformat() if updated_plan.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除计划项目
    
    Args:
        plan_id: 计划ID
        db: 数据库会话
        
    Returns:
        删除确认信息
        
    Raises:
        HTTPException: 计划不存在
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 查询计划
        plan = plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail={
                "error": "计划不存在",
                "message": f"未找到ID为 {plan_id} 的计划",
                "code": "PLAN_NOT_FOUND"
            })
        
        # 保存日期用于返回
        plan_date = plan.date.strftime('%Y-%m-%d')
        
        # 删除计划
        plan_repo.delete(plan_id)
        
        return {
            'success': True,
            'message': f"成功删除计划 {plan_id}",
            'deleted_plan_id': plan_id,
            'date': plan_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.post("/{plan_id}/complete")
async def mark_plan_complete(
    plan_id: int,
    completion_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    标记计划项目为已完成
    
    Args:
        plan_id: 计划ID
        completion_data: 完成数据，包含actual_duration（可选）
        db: 数据库会话
        
    Returns:
        更新后的计划项目
        
    Raises:
        HTTPException: 计划不存在或数据验证失败
        
    验证: 需求 9.3
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 查询计划
        plan = plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail={
                "error": "计划不存在",
                "message": f"未找到ID为 {plan_id} 的计划",
                "code": "PLAN_NOT_FOUND"
            })
        
        # 标记为已完成
        plan.completed = True
        
        # 如果提供了实际用时，更新它
        if 'actual_duration' in completion_data:
            actual_duration = completion_data['actual_duration']
            if actual_duration is not None:
                try:
                    actual_duration = int(actual_duration)
                    if actual_duration < 0:
                        raise HTTPException(status_code=400, detail={
                            "error": "数据验证失败",
                            "message": f"实际时长不能为负数: {actual_duration}",
                            "code": "INVALID_ACTUAL_DURATION"
                        })
                    plan.actual_duration = actual_duration
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail={
                        "error": "数据验证失败",
                        "message": f"实际时长必须是整数: {completion_data['actual_duration']}",
                        "code": "INVALID_ACTUAL_DURATION"
                    })
        
        # 保存更新
        updated_plan = plan_repo.update(plan)
        
        return {
            'id': updated_plan.id,
            'date': updated_plan.date.strftime('%Y-%m-%d'),
            'type': updated_plan.type,
            'name': updated_plan.name,
            'calories': updated_plan.calories,
            'duration': updated_plan.duration,
            'completed': updated_plan.completed,
            'actual_duration': updated_plan.actual_duration,
            'updated_at': updated_plan.updated_at.isoformat() if updated_plan.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.post("/{plan_id}/uncomplete")
async def mark_plan_uncomplete(
    plan_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    取消标记计划项目为已完成
    
    Args:
        plan_id: 计划ID
        db: 数据库会话
        
    Returns:
        更新后的计划项目
        
    Raises:
        HTTPException: 计划不存在
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 查询计划
        plan = plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail={
                "error": "计划不存在",
                "message": f"未找到ID为 {plan_id} 的计划",
                "code": "PLAN_NOT_FOUND"
            })
        
        # 取消完成标记
        plan.completed = False
        
        # 保存更新
        updated_plan = plan_repo.update(plan)
        
        return {
            'id': updated_plan.id,
            'date': updated_plan.date.strftime('%Y-%m-%d'),
            'type': updated_plan.type,
            'name': updated_plan.name,
            'calories': updated_plan.calories,
            'duration': updated_plan.duration,
            'completed': updated_plan.completed,
            'actual_duration': updated_plan.actual_duration,
            'updated_at': updated_plan.updated_at.isoformat() if updated_plan.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


@router.get("/history/stats")
async def get_history_stats(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取历史统计数据
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选
        db: 数据库会话
        
    Returns:
        历史统计数据（总训练天数、总热量消耗、平均完成率等）
        
    Raises:
        HTTPException: 日期格式错误
        
    验证: 需求 9.4
    """
    try:
        plan_repo = PlanRepository(db)
        
        # 解析日期范围（如果提供）
        start = None
        end = None
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail={
                    "error": "日期格式错误",
                    "message": f"开始日期格式应为 YYYY-MM-DD，收到: {start_date}",
                    "code": "INVALID_DATE_FORMAT"
                })
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail={
                    "error": "日期格式错误",
                    "message": f"结束日期格式应为 YYYY-MM-DD，收到: {end_date}",
                    "code": "INVALID_DATE_FORMAT"
                })
        
        # 验证日期范围
        if start and end and start > end:
            raise HTTPException(status_code=400, detail={
                "error": "日期范围错误",
                "message": "开始日期不能晚于结束日期",
                "code": "INVALID_DATE_RANGE"
            })
        
        # 获取所有计划
        all_plans = plan_repo.get_all()
        
        # 过滤日期范围
        filtered_plans = []
        for plan in all_plans:
            if start and plan.date < start:
                continue
            if end and plan.date > end:
                continue
            filtered_plans.append(plan)
        
        # 计算统计数据
        unique_dates = set()
        total_calories_burned = 0.0
        total_exercise_duration = 0
        total_items = len(filtered_plans)
        completed_items = 0
        
        for plan in filtered_plans:
            unique_dates.add(plan.date)
            
            if plan.type == 'exercise':
                total_calories_burned += plan.calories or 0
                total_exercise_duration += plan.duration or 0
            
            if plan.completed:
                completed_items += 1
        
        # 计算总训练天数
        total_training_days = len(unique_dates)
        
        # 计算平均完成率
        average_completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # 计算每日平均热量消耗
        average_daily_calories_burned = (total_calories_burned / total_training_days) if total_training_days > 0 else 0
        
        # 计算每日平均运动时长
        average_daily_exercise_duration = (total_exercise_duration / total_training_days) if total_training_days > 0 else 0
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_training_days': total_training_days,
            'total_calories_burned': round(total_calories_burned, 2),
            'total_exercise_duration': total_exercise_duration,
            'average_daily_calories_burned': round(average_daily_calories_burned, 2),
            'average_daily_exercise_duration': round(average_daily_exercise_duration, 2),
            'total_items': total_items,
            'completed_items': completed_items,
            'average_completion_rate': round(average_completion_rate, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })
