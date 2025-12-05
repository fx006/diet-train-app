"""
PDF 文件解析器

使用 pdfplumber 提取文本和表格，解析饮食训练计划数据
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import re


class PDFParseError(Exception):
    """PDF 解析错误"""
    pass


# 检查 pdfplumber 是否可用
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class PDFParser:
    """
    PDF 解析器
    
    功能：
    - 使用 pdfplumber 提取文本
    - 使用正则表达式识别数据字段
    - 处理表格和结构化数据
    - 提取日期、餐食、运动、热量、时长等信息
    """
    
    # 正则表达式模式
    PATTERNS = {
        'date': [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2024-12-02
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 12/02/2024
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',     # 2024年12月02日
        ],
        'meal_time': [
            r'(早餐|午餐|晚餐|加餐)',
            r'(breakfast|lunch|dinner|snack)',
        ],
        'calories': [
            r'(\d+(?:\.\d+)?)\s*(?:卡|卡路里|kcal|cal)',
        ],
        'exercise': [
            r'(运动|锻炼|训练)[:：]\s*(.+)',
            r'(跑步|游泳|瑜伽|力量训练|有氧运动)',
        ],
        'duration': [
            r'(\d+(?:\.\d+)?)\s*(?:分钟|小时|min|hour)',
        ]
    }
    
    # 列标题关键词（用于表格识别）
    COLUMN_KEYWORDS = {
        'date': ['日期', 'date', '时间'],
        'meal_time': ['餐次', 'meal', '用餐'],
        'food': ['食物', 'food', '菜品'],
        'calories': ['热量', 'calories', 'kcal'],
        'exercise': ['运动', 'exercise', '锻炼'],
        'duration': ['时长', 'duration', '分钟'],
        'notes': ['备注', 'notes', '说明']
    }
    
    def __init__(self):
        """初始化解析器"""
        if not HAS_PDFPLUMBER:
            raise PDFParseError("需要安装 pdfplumber 库: pip install pdfplumber")
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析 PDF 文件
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            解析后的数据列表
            
        Raises:
            PDFParseError: 解析失败
        """
        try:
            data = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # 尝试提取表格
                    tables = page.extract_tables()
                    
                    if tables:
                        # 处理表格数据
                        for table in tables:
                            table_data = self._process_table(table)
                            data.extend(table_data)
                    
                    # 提取文本并解析
                    text = page.extract_text()
                    if text:
                        text_data = self._parse_text(text)
                        data.extend(text_data)
            
            return data
            
        except Exception as e:
            raise PDFParseError(f"解析 PDF 文件失败: {str(e)}")
    
    def _process_table(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        """
        处理表格数据
        
        Args:
            table: 表格数据（二维列表）
            
        Returns:
            处理后的数据列表
        """
        if not table or len(table) < 2:
            return []
        
        # 假设第一行是标题
        headers = table[0]
        
        # 识别列的含义
        column_mapping = self._map_table_columns(headers)
        
        # 处理数据行
        data = []
        for row in table[1:]:
            if not row or all(not cell for cell in row):
                continue  # 跳过空行
            
            row_data = self._extract_table_row(row, column_mapping)
            if row_data and any(row_data.values()):
                data.append(row_data)
        
        return data
    
    def _map_table_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        映射表格列到字段
        
        Args:
            headers: 表格标题行
            
        Returns:
            列映射字典
        """
        mapping = {}
        
        for i, header in enumerate(headers):
            if not header:
                continue
            
            header_lower = str(header).lower()
            
            # 匹配字段类型
            for field, keywords in self.COLUMN_KEYWORDS.items():
                if any(keyword in header_lower for keyword in keywords):
                    mapping[field] = i
                    break
        
        return mapping
    
    def _extract_table_row(self, row: List[str], column_mapping: Dict[str, int]) -> Dict[str, Any]:
        """
        提取表格行数据
        
        Args:
            row: 表格行
            column_mapping: 列映射
            
        Returns:
            行数据字典
        """
        row_data = {}
        
        for field, col_idx in column_mapping.items():
            if col_idx < len(row):
                cell_value = row[col_idx]
                
                if field == 'date':
                    row_data[field] = self._parse_date(cell_value)
                elif field in ['calories', 'duration']:
                    row_data[field] = self._parse_number(cell_value)
                else:
                    row_data[field] = self._clean_text(cell_value)
        
        return row_data
    
    def _parse_text(self, text: str) -> List[Dict[str, Any]]:
        """
        解析文本内容
        
        Args:
            text: PDF 文本内容
            
        Returns:
            解析后的数据列表
        """
        data = []
        lines = text.split('\n')
        
        current_item = {}
        current_date = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试提取日期
            date_value = self._extract_date(line)
            if date_value:
                # 保存之前的项目
                if current_item and any(current_item.values()):
                    data.append(current_item)
                
                current_date = date_value
                current_item = {'date': current_date}
                continue
            
            # 如果有当前日期，尝试提取其他信息
            if current_date:
                # 提取餐次和食物
                meal_info = self._extract_meal_info(line)
                if meal_info:
                    if current_item and any(k != 'date' for k in current_item.keys()):
                        data.append(current_item)
                        current_item = {'date': current_date}
                    current_item.update(meal_info)
                    continue
                
                # 提取运动信息
                exercise_info = self._extract_exercise_info(line)
                if exercise_info:
                    if current_item and any(k != 'date' for k in current_item.keys()):
                        data.append(current_item)
                        current_item = {'date': current_date}
                    current_item.update(exercise_info)
                    continue
                
                # 提取热量
                calories = self._extract_calories(line)
                if calories and 'calories' not in current_item:
                    current_item['calories'] = calories
        
        # 添加最后一个项目
        if current_item and any(current_item.values()):
            data.append(current_item)
        
        return data
    
    def _extract_date(self, text: str) -> Optional[str]:
        """
        从文本中提取日期
        
        Args:
            text: 文本
            
        Returns:
            日期字符串或 None
        """
        for pattern in self.PATTERNS['date']:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                
                # 判断日期格式
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year, month, day = groups
                else:  # MM-DD-YYYY
                    month, day, year = groups
                
                try:
                    parsed_date = date(int(year), int(month), int(day))
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _extract_meal_info(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取餐食信息
        
        Args:
            text: 文本
            
        Returns:
            餐食信息字典或 None
        """
        for pattern in self.PATTERNS['meal_time']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                meal_time = match.group(1)
                
                # 提取食物（餐次后面的内容）
                food_text = text[match.end():].strip()
                
                # 移除热量信息
                food_text = re.sub(r'\d+(?:\.\d+)?\s*(?:卡|卡路里|kcal|cal)', '', food_text).strip()
                
                # 清理分隔符
                food_text = re.sub(r'^[:：\s]+', '', food_text).strip()
                
                if food_text:
                    return {
                        'meal_time': meal_time,
                        'food': food_text
                    }
        
        return None
    
    def _extract_exercise_info(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取运动信息
        
        Args:
            text: 文本
            
        Returns:
            运动信息字典或 None
        """
        for pattern in self.PATTERNS['exercise']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # 格式：运动: 跑步
                    exercise_name = match.group(2).strip()
                else:
                    # 格式：跑步
                    exercise_name = match.group(1).strip()
                
                # 提取时长
                duration = self._extract_duration(text)
                
                result = {'exercise': exercise_name}
                if duration:
                    result['duration'] = duration
                
                return result
        
        return None
    
    def _extract_calories(self, text: str) -> Optional[float]:
        """
        从文本中提取热量
        
        Args:
            text: 文本
            
        Returns:
            热量值或 None
        """
        for pattern in self.PATTERNS['calories']:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_duration(self, text: str) -> Optional[float]:
        """
        从文本中提取时长
        
        Args:
            text: 文本
            
        Returns:
            时长（分钟）或 None
        """
        for pattern in self.PATTERNS['duration']:
            match = re.search(pattern, text)
            if match:
                try:
                    duration = float(match.group(1))
                    
                    # 检查单位
                    unit = match.group(0)
                    if '小时' in unit or 'hour' in unit:
                        duration *= 60  # 转换为分钟
                    
                    return duration
                except ValueError:
                    continue
        
        return None
    
    def _parse_date(self, value: str) -> Optional[str]:
        """
        解析日期
        
        Args:
            value: 日期字符串
            
        Returns:
            标准化的日期字符串（YYYY-MM-DD）或 None
        """
        if not value:
            return None
        
        return self._extract_date(str(value))
    
    def _parse_number(self, value: str) -> Optional[float]:
        """
        解析数字
        
        Args:
            value: 数字字符串
            
        Returns:
            数字或 None
        """
        if not value:
            return None
        
        # 提取数字
        numbers = re.findall(r'\d+(?:\.\d+)?', str(value))
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def _clean_text(self, value: str) -> Optional[str]:
        """
        清理文本
        
        Args:
            value: 文本值
            
        Returns:
            清理后的文本或 None
        """
        if not value:
            return None
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', str(value)).strip()
        return cleaned if cleaned else None
    
    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        """
        解析 PDF 文件（便捷函数）
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            解析后的数据列表
        """
        parser = PDFParser()
        return parser.parse_file(file_path)


# ============================================================================
# 数据转换函数（与 Excel 解析器兼容）
# ============================================================================

def convert_to_plan_items(parsed_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    将 PDF 解析后的数据转换为计划项目格式
    
    Args:
        parsed_data: 解析后的原始数据
        
    Returns:
        包含 meals 和 exercises 的字典
    """
    meals = []
    exercises = []
    
    for row in parsed_data:
        # 如果有食物信息，添加到餐食列表
        if row.get('food') or row.get('meal_time'):
            meal = {
                'date': row.get('date'),
                'meal_time': row.get('meal_time', '未指定'),
                'food': row.get('food'),
                'calories': row.get('calories', 0),
                'notes': row.get('notes')
            }
            meals.append(meal)
        
        # 如果有运动信息，添加到运动列表
        if row.get('exercise'):
            exercise = {
                'date': row.get('date'),
                'name': row.get('exercise'),
                'duration': row.get('duration', 0),
                'calories_burned': row.get('calories', 0),
                'notes': row.get('notes')
            }
            exercises.append(exercise)
    
    return {
        'meals': meals,
        'exercises': exercises
    }
