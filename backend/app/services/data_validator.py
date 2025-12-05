"""
数据验证和错误处理模块

提供统一的数据验证、错误检测和错误信息生成功能
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum


class ValidationErrorType(Enum):
    """验证错误类型"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    INVALID_VALUE = "invalid_value"
    OUT_OF_RANGE = "out_of_range"
    EMPTY_DATA = "empty_data"


class ValidationError:
    """验证错误"""
    
    def __init__(
        self,
        error_type: ValidationErrorType,
        field: str,
        message: str,
        row_index: Optional[int] = None,
        value: Any = None
    ):
        self.error_type = error_type
        self.field = field
        self.message = message
        self.row_index = row_index
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'error_type': self.error_type.value,
            'field': self.field,
            'message': self.message
        }
        
        if self.row_index is not None:
            result['row_index'] = self.row_index
        
        if self.value is not None:
            result['value'] = str(self.value)
        
        return result
    
    def __str__(self) -> str:
        """字符串表示"""
        parts = [self.message]
        
        if self.row_index is not None:
            parts.append(f"(行 {self.row_index})")
        
        if self.field:
            parts.append(f"[字段: {self.field}]")
        
        return " ".join(parts)


class ValidationResult:
    """验证结果"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def add_error(
        self,
        error_type: ValidationErrorType,
        field: str,
        message: str,
        row_index: Optional[int] = None,
        value: Any = None
    ):
        """添加错误"""
        error = ValidationError(error_type, field, message, row_index, value)
        self.errors.append(error)
    
    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
    
    def is_valid(self) -> bool:
        """是否验证通过"""
        return len(self.errors) == 0
    
    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if self.is_valid():
            return "验证通过"
        
        summary_parts = [f"发现 {len(self.errors)} 个错误"]
        
        if self.warnings:
            summary_parts.append(f"{len(self.warnings)} 个警告")
        
        return "，".join(summary_parts)
    
    def get_detailed_errors(self) -> List[str]:
        """获取详细错误列表"""
        return [str(error) for error in self.errors]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_valid': self.is_valid(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': [error.to_dict() for error in self.errors],
            'warnings': self.warnings,
            'summary': self.get_error_summary()
        }


class DataValidator:
    """
    数据验证器
    
    功能：
    - 验证解析后的数据完整性
    - 检测数据缺失
    - 验证数据格式和范围
    - 生成具体的错误信息
    """
    
    # 必需字段
    REQUIRED_FIELDS = {
        'meal': ['date'],  # 餐食至少需要日期
        'exercise': ['date']  # 运动至少需要日期
    }
    
    # 可选但推荐的字段
    RECOMMENDED_FIELDS = {
        'meal': ['meal_time', 'food', 'calories'],
        'exercise': ['name', 'duration']
    }
    
    def validate_parsed_data(
        self,
        data: List[Dict[str, Any]],
        data_type: str = 'general'
    ) -> ValidationResult:
        """
        验证解析后的数据
        
        Args:
            data: 解析后的数据列表
            data_type: 数据类型 ('meal', 'exercise', 'general')
            
        Returns:
            验证结果
        """
        result = ValidationResult()
        
        # 检查是否为空
        if not data:
            result.add_error(
                ValidationErrorType.EMPTY_DATA,
                'data',
                '解析结果为空，未找到任何有效数据'
            )
            return result
        
        # 验证每一行数据
        for idx, row in enumerate(data, start=1):
            self._validate_row(row, idx, data_type, result)
        
        # 添加统计信息
        if result.is_valid():
            result.add_warning(f"成功验证 {len(data)} 条数据")
        
        return result
    
    def _validate_row(
        self,
        row: Dict[str, Any],
        row_index: int,
        data_type: str,
        result: ValidationResult
    ):
        """
        验证单行数据
        
        Args:
            row: 行数据
            row_index: 行索引
            data_type: 数据类型
            result: 验证结果对象
        """
        # 检查必需字段
        if data_type in self.REQUIRED_FIELDS:
            for field in self.REQUIRED_FIELDS[data_type]:
                if not row.get(field):
                    result.add_error(
                        ValidationErrorType.MISSING_REQUIRED_FIELD,
                        field,
                        f"缺少必需字段: {field}",
                        row_index
                    )
        
        # 检查推荐字段
        if data_type in self.RECOMMENDED_FIELDS:
            missing_recommended = []
            for field in self.RECOMMENDED_FIELDS[data_type]:
                if not row.get(field):
                    missing_recommended.append(field)
            
            if missing_recommended:
                result.add_warning(
                    f"行 {row_index} 缺少推荐字段: {', '.join(missing_recommended)}"
                )
        
        # 验证日期格式
        if 'date' in row and row['date']:
            if not self._is_valid_date(row['date']):
                result.add_error(
                    ValidationErrorType.INVALID_FORMAT,
                    'date',
                    f"日期格式无效: {row['date']}",
                    row_index,
                    row['date']
                )
        
        # 验证数值字段
        if 'calories' in row and row['calories'] is not None:
            if not self._is_valid_number(row['calories'], min_value=0, max_value=10000):
                result.add_error(
                    ValidationErrorType.INVALID_VALUE,
                    'calories',
                    f"热量值无效或超出范围 (0-10000): {row['calories']}",
                    row_index,
                    row['calories']
                )
        
        if 'duration' in row and row['duration'] is not None:
            if not self._is_valid_number(row['duration'], min_value=0, max_value=1440):
                result.add_error(
                    ValidationErrorType.INVALID_VALUE,
                    'duration',
                    f"时长值无效或超出范围 (0-1440分钟): {row['duration']}",
                    row_index,
                    row['duration']
                )
        
        # 验证文本字段长度
        text_fields = ['food', 'meal_time', 'exercise', 'name', 'notes']
        for field in text_fields:
            if field in row and row[field]:
                if not self._is_valid_text(row[field], max_length=500):
                    result.add_error(
                        ValidationErrorType.INVALID_VALUE,
                        field,
                        f"文本字段过长 (最大500字符): {field}",
                        row_index
                    )
    
    def _is_valid_date(self, value: Any) -> bool:
        """
        验证日期是否有效
        
        Args:
            value: 日期值
            
        Returns:
            是否有效
        """
        if isinstance(value, (date, datetime)):
            return True
        
        if isinstance(value, str):
            # 尝试解析常见日期格式
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
        
        return False
    
    def _is_valid_number(
        self,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> bool:
        """
        验证数字是否有效
        
        Args:
            value: 数字值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            是否有效
        """
        try:
            num = float(value)
            
            if min_value is not None and num < min_value:
                return False
            
            if max_value is not None and num > max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_valid_text(self, value: Any, max_length: int = 500) -> bool:
        """
        验证文本是否有效
        
        Args:
            value: 文本值
            max_length: 最大长度
            
        Returns:
            是否有效
        """
        if not isinstance(value, str):
            return False
        
        return len(value) <= max_length
    
    def validate_meal_data(self, meals: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证餐食数据
        
        Args:
            meals: 餐食数据列表
            
        Returns:
            验证结果
        """
        return self.validate_parsed_data(meals, data_type='meal')
    
    def validate_exercise_data(self, exercises: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证运动数据
        
        Args:
            exercises: 运动数据列表
            
        Returns:
            验证结果
        """
        return self.validate_parsed_data(exercises, data_type='exercise')
    
    def validate_plan_items(
        self,
        plan_items: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[ValidationResult, ValidationResult]:
        """
        验证计划项目（餐食和运动）
        
        Args:
            plan_items: 包含 meals 和 exercises 的字典
            
        Returns:
            (餐食验证结果, 运动验证结果)
        """
        meal_result = self.validate_meal_data(plan_items.get('meals', []))
        exercise_result = self.validate_exercise_data(plan_items.get('exercises', []))
        
        return meal_result, exercise_result


# ============================================================================
# 便捷函数
# ============================================================================

def validate_data(
    data: List[Dict[str, Any]],
    data_type: str = 'general'
) -> ValidationResult:
    """
    验证数据（便捷函数）
    
    Args:
        data: 数据列表
        data_type: 数据类型
        
    Returns:
        验证结果
    """
    validator = DataValidator()
    return validator.validate_parsed_data(data, data_type)


def check_data_completeness(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检查数据完整性
    
    Args:
        data: 数据列表
        
    Returns:
        完整性报告
    """
    if not data:
        return {
            'total_rows': 0,
            'complete_rows': 0,
            'incomplete_rows': 0,
            'completeness_rate': 0.0,
            'missing_fields': {}
        }
    
    total_rows = len(data)
    complete_rows = 0
    missing_fields_count = {}
    
    # 收集所有可能的字段
    all_fields = set()
    for row in data:
        all_fields.update(row.keys())
    
    # 检查每一行
    for row in data:
        is_complete = True
        
        for field in all_fields:
            if field not in row or row[field] is None or row[field] == '':
                is_complete = False
                missing_fields_count[field] = missing_fields_count.get(field, 0) + 1
        
        if is_complete:
            complete_rows += 1
    
    incomplete_rows = total_rows - complete_rows
    completeness_rate = (complete_rows / total_rows * 100) if total_rows > 0 else 0
    
    return {
        'total_rows': total_rows,
        'complete_rows': complete_rows,
        'incomplete_rows': incomplete_rows,
        'completeness_rate': round(completeness_rate, 2),
        'missing_fields': missing_fields_count
    }
