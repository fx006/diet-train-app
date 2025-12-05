"""
文件上传和处理 API 路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import tempfile
import os
from datetime import date

from app.database import get_db
from app.services.file_validator import validate_file, FileValidationError
from app.services.excel_parser import ExcelParser, ExcelParseError, convert_to_plan_items
from app.services.pdf_parser import PDFParser, PDFParseError, HAS_PDFPLUMBER
from app.services.data_validator import DataValidator, validate_data
from app.repositories.plan_repository import PlanRepository
from app.models.plan import Plan


router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传并解析文件（Excel 或 PDF）
    
    Args:
        file: 上传的文件
        db: 数据库会话
        
    Returns:
        解析结果和保存的数据统计
        
    Raises:
        HTTPException: 文件验证失败、解析失败或保存失败
    """
    temp_file_path = None
    
    try:
        # 1. 基本验证
        if not file.filename:
            raise HTTPException(status_code=400, detail={
                "error": "文件验证失败",
                "message": "文件名不能为空",
                "code": "FILE_VALIDATION_ERROR"
            })
        
        # 获取文件扩展名
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # 检查扩展名
        supported_extensions = ['.xlsx', '.xls', '.pdf']
        if file_extension not in supported_extensions:
            raise HTTPException(status_code=400, detail={
                "error": "文件验证失败",
                "message": f"不支持的文件类型: {file_extension}",
                "code": "FILE_VALIDATION_ERROR"
            })
        
        # 2. 保存临时文件
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as tmp:
            content = await file.read()
            
            # 检查文件大小
            file_size = len(content)
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                raise HTTPException(status_code=400, detail={
                    "error": "文件验证失败",
                    "message": f"文件大小超过限制 ({file_size} > {max_size})",
                    "code": "FILE_VALIDATION_ERROR"
                })
            
            tmp.write(content)
            temp_file_path = tmp.name
        
        # 3. 验证文件
        try:
            is_valid, file_type, error_msg = validate_file(temp_file_path)
            if not is_valid:
                raise FileValidationError(error_msg)
            
            file_info = {
                'file_type': file_type,
                'extension': file_extension,
                'size': file_size
            }
        except FileValidationError as e:
            raise HTTPException(status_code=400, detail={
                "error": "文件验证失败",
                "message": str(e),
                "code": "FILE_VALIDATION_ERROR"
            })
        
        # 4. 解析文件
        try:
            parsed_data = _parse_file(temp_file_path, file_info['file_type'])
        except (ExcelParseError, PDFParseError) as e:
            raise HTTPException(status_code=400, detail={
                "error": "文件解析失败",
                "message": str(e),
                "code": "FILE_PARSE_ERROR"
            })
        
        # 5. 验证解析后的数据
        validator = DataValidator()
        validation_result = validator.validate_parsed_data(parsed_data)
        
        if not validation_result.is_valid():
            raise HTTPException(status_code=400, detail={
                "error": "数据验证失败",
                "message": validation_result.get_error_summary(),
                "errors": [error.to_dict() for error in validation_result.errors],
                "code": "DATA_VALIDATION_ERROR"
            })
        
        # 6. 转换为计划项目格式
        plan_items = convert_to_plan_items(parsed_data)
        
        # 7. 保存到数据库
        plan_repo = PlanRepository(db)
        saved_stats = _save_plan_items(plan_repo, plan_items)
        
        # 8. 返回结果
        return {
            "success": True,
            "message": "文件上传和解析成功",
            "file_info": {
                "filename": file.filename,
                "file_type": file_info['file_type'],
                "size": file_info['size']
            },
            "parsed_data": {
                "total_items": len(parsed_data),
                "meals_count": len(plan_items.get('meals', [])),
                "exercises_count": len(plan_items.get('exercises', []))
            },
            "saved_data": saved_stats,
            "validation": {
                "warnings": validation_result.warnings
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass


def _parse_file(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    """
    根据文件类型解析文件
    
    Args:
        file_path: 文件路径
        file_type: 文件类型 ('excel' 或 'pdf')
        
    Returns:
        解析后的数据列表
        
    Raises:
        ExcelParseError: Excel 解析失败
        PDFParseError: PDF 解析失败
    """
    if file_type == 'excel':
        parser = ExcelParser()
        return parser.parse_file(file_path)
    elif file_type == 'pdf':
        if not HAS_PDFPLUMBER:
            raise PDFParseError("PDF 解析功能不可用，请安装 pdfplumber 库")
        parser = PDFParser()
        return parser.parse_file(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


def _save_plan_items(
    plan_repo: PlanRepository,
    plan_items: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    保存计划项目到数据库
    
    Args:
        plan_repo: 计划仓储
        plan_items: 计划项目（包含 meals 和 exercises）
        
    Returns:
        保存统计信息
    """
    from datetime import datetime
    
    saved_meals = 0
    saved_exercises = 0
    dates_affected = set()
    
    # 保存餐食
    for meal in plan_items.get('meals', []):
        if not meal.get('date'):
            continue
        
        # 转换日期字符串为 date 对象
        meal_date = meal['date']
        if isinstance(meal_date, str):
            meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
        
        plan = Plan(
            date=meal_date,
            type='meal',
            name=meal.get('food', '未命名餐食'),
            calories=meal.get('calories', 0),
            duration=None
        )
        
        plan_repo.create(plan)
        saved_meals += 1
        dates_affected.add(str(meal_date))
    
    # 保存运动
    for exercise in plan_items.get('exercises', []):
        if not exercise.get('date'):
            continue
        
        # 转换日期字符串为 date 对象
        exercise_date = exercise['date']
        if isinstance(exercise_date, str):
            exercise_date = datetime.strptime(exercise_date, '%Y-%m-%d').date()
        
        plan = Plan(
            date=exercise_date,
            type='exercise',
            name=exercise.get('name', '未命名运动'),
            calories=exercise.get('calories_burned', 0),
            duration=exercise.get('duration', 0)
        )
        
        plan_repo.create(plan)
        saved_exercises += 1
        dates_affected.add(str(exercise_date))
    
    return {
        "meals_saved": saved_meals,
        "exercises_saved": saved_exercises,
        "total_saved": saved_meals + saved_exercises,
        "dates_affected": sorted(list(dates_affected))
    }


@router.get("/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """
    获取支持的文件格式
    
    Returns:
        支持的文件格式信息
    """
    return {
        "supported_formats": [
            {
                "type": "excel",
                "extensions": [".xlsx", ".xls"],
                "mime_types": [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel"
                ],
                "description": "Excel 文件"
            },
            {
                "type": "pdf",
                "extensions": [".pdf"],
                "mime_types": ["application/pdf"],
                "description": "PDF 文件",
                "available": HAS_PDFPLUMBER
            }
        ],
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "max_file_size_human": "10MB"
    }


from fastapi.responses import StreamingResponse
import io
import csv
from openpyxl import Workbook


@router.get("/export/{format}")
async def export_data(
    format: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """
    导出计划数据
    
    Args:
        format: 导出格式（excel 或 csv）
        start_date: 开始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选
        db: 数据库会话
        
    Returns:
        导出的文件
        
    Raises:
        HTTPException: 格式不支持或日期格式错误
        
    验证: 需求 9.5
    """
    try:
        # 验证格式
        if format not in ['excel', 'csv']:
            raise HTTPException(status_code=400, detail={
                "error": "格式不支持",
                "message": f"不支持的导出格式: {format}，支持的格式: excel, csv",
                "code": "UNSUPPORTED_FORMAT"
            })
        
        # 解析日期范围
        from datetime import datetime
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
        
        # 获取数据
        plan_repo = PlanRepository(db)
        all_plans = plan_repo.get_all()
        
        # 过滤日期范围
        filtered_plans = []
        for plan in all_plans:
            if start and plan.date < start:
                continue
            if end and plan.date > end:
                continue
            filtered_plans.append(plan)
        
        # 按日期排序
        filtered_plans.sort(key=lambda p: p.date)
        
        if format == 'excel':
            return export_to_excel(filtered_plans)
        else:  # csv
            return export_to_csv(filtered_plans)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "服务器内部错误",
            "message": str(e),
            "code": "INTERNAL_SERVER_ERROR"
        })


def export_to_excel(plans: List[Plan]) -> StreamingResponse:
    """导出为Excel格式"""
    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "计划数据"
    
    # 写入表头
    headers = [
        "日期", "类型", "名称", "热量(卡路里)", 
        "计划时长(分钟)", "实际时长(分钟)", "是否完成"
    ]
    ws.append(headers)
    
    # 写入数据
    for plan in plans:
        row = [
            plan.date.strftime('%Y-%m-%d'),
            "餐食" if plan.type == 'meal' else "运动",
            plan.name,
            plan.calories,
            plan.duration if plan.duration else "",
            plan.actual_duration if plan.actual_duration else "",
            "是" if plan.completed else "否"
        ]
        ws.append(row)
    
    # 调整列宽
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # 保存到内存
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # 返回文件
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=plans_export.xlsx"
        }
    )


def export_to_csv(plans: List[Plan]) -> StreamingResponse:
    """导出为CSV格式"""
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    headers = [
        "日期", "类型", "名称", "热量(卡路里)", 
        "计划时长(分钟)", "实际时长(分钟)", "是否完成"
    ]
    writer.writerow(headers)
    
    # 写入数据
    for plan in plans:
        row = [
            plan.date.strftime('%Y-%m-%d'),
            "餐食" if plan.type == 'meal' else "运动",
            plan.name,
            plan.calories,
            plan.duration if plan.duration else "",
            plan.actual_duration if plan.actual_duration else "",
            "是" if plan.completed else "否"
        ]
        writer.writerow(row)
    
    # 转换为字节流
    output.seek(0)
    
    # 返回文件
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=plans_export.csv"
        }
    )
