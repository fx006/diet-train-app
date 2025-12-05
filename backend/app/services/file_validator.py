"""
文件格式验证服务

实现文件类型检测、大小限制检查和安全验证
"""
import os
from typing import Tuple, Optional
from pathlib import Path

# python-magic 是可选依赖
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class FileValidationError(Exception):
    """文件验证错误"""
    pass


class FileValidator:
    """
    文件验证器
    
    功能：
    - 文件类型检测（基于 magic number）
    - 文件大小限制检查
    - 文件扩展名验证
    - 安全性检查
    """
    
    # 支持的文件类型
    SUPPORTED_TYPES = {
        'excel': {
            'extensions': ['.xlsx', '.xls'],
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ],
            'magic_numbers': [
                b'PK\x03\x04',  # XLSX (ZIP format)
                b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # XLS (OLE format)
            ]
        },
        'pdf': {
            'extensions': ['.pdf'],
            'mime_types': ['application/pdf'],
            'magic_numbers': [b'%PDF']
        }
    }
    
    # 文件大小限制（字节）
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    MIN_FILE_SIZE = 100  # 100 bytes
    
    def __init__(self, max_size: Optional[int] = None):
        """
        初始化验证器
        
        Args:
            max_size: 最大文件大小（字节），None 使用默认值
        """
        self.max_size = max_size or self.MAX_FILE_SIZE
    
    def validate_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            (is_valid, file_type, error_message)
            - is_valid: 是否有效
            - file_type: 文件类型（'excel' 或 'pdf'）
            - error_message: 错误信息（如果有）
        """
        try:
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                return False, None, f"文件不存在: {file_path}"
            
            # 2. 检查是否是文件（不是目录）
            if not os.path.isfile(file_path):
                return False, None, f"不是有效的文件: {file_path}"
            
            # 3. 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size < self.MIN_FILE_SIZE:
                return False, None, f"文件太小: {file_size} bytes (最小 {self.MIN_FILE_SIZE} bytes)"
            
            if file_size > self.max_size:
                return False, None, f"文件太大: {file_size} bytes (最大 {self.max_size} bytes)"
            
            # 4. 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            detected_type = self._detect_type_by_extension(file_ext)
            
            if not detected_type:
                return False, None, f"不支持的文件扩展名: {file_ext}"
            
            # 5. 检查 magic number（文件头）
            if not self._validate_magic_number(file_path, detected_type):
                return False, None, f"文件内容与扩展名不匹配: {file_ext}"
            
            # 6. 检查 MIME 类型（如果 python-magic 可用）
            if HAS_MAGIC:
                try:
                    mime_type = magic.from_file(file_path, mime=True)
                    if not self._validate_mime_type(mime_type, detected_type):
                        return False, None, f"MIME 类型不匹配: {mime_type}"
                except Exception:
                    # MIME 检查失败，跳过
                    pass
            
            # 7. 安全性检查
            security_check, security_error = self._security_check(file_path)
            if not security_check:
                return False, None, security_error
            
            return True, detected_type, None
            
        except Exception as e:
            return False, None, f"验证过程出错: {str(e)}"
    
    def _detect_type_by_extension(self, extension: str) -> Optional[str]:
        """
        根据扩展名检测文件类型
        
        Args:
            extension: 文件扩展名（如 '.xlsx'）
            
        Returns:
            文件类型（'excel' 或 'pdf'）或 None
        """
        for file_type, config in self.SUPPORTED_TYPES.items():
            if extension in config['extensions']:
                return file_type
        return None
    
    def _validate_magic_number(self, file_path: str, expected_type: str) -> bool:
        """
        验证文件的 magic number（文件头）
        
        Args:
            file_path: 文件路径
            expected_type: 期望的文件类型
            
        Returns:
            是否匹配
        """
        try:
            with open(file_path, 'rb') as f:
                # 读取文件头（前 8 字节足够识别大多数格式）
                header = f.read(8)
                
                # 获取期望类型的 magic numbers
                magic_numbers = self.SUPPORTED_TYPES[expected_type]['magic_numbers']
                
                # 检查是否匹配任一 magic number
                for magic_num in magic_numbers:
                    if header.startswith(magic_num):
                        return True
                
                return False
                
        except Exception:
            return False
    
    def _validate_mime_type(self, mime_type: str, expected_type: str) -> bool:
        """
        验证 MIME 类型
        
        Args:
            mime_type: 检测到的 MIME 类型
            expected_type: 期望的文件类型
            
        Returns:
            是否匹配
        """
        expected_mimes = self.SUPPORTED_TYPES[expected_type]['mime_types']
        return mime_type in expected_mimes
    
    def _security_check(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        安全性检查
        
        Args:
            file_path: 文件路径
            
        Returns:
            (is_safe, error_message)
        """
        try:
            # 1. 检查文件路径是否包含危险字符
            dangerous_chars = ['..', '~', '$', '`', '|', ';', '&']
            for char in dangerous_chars:
                if char in file_path:
                    return False, f"文件路径包含危险字符: {char}"
            
            # 2. 检查文件是否可读
            if not os.access(file_path, os.R_OK):
                return False, "文件不可读"
            
            # 3. 检查文件权限（不应该是可执行文件）
            if os.access(file_path, os.X_OK):
                return False, "文件具有可执行权限，可能不安全"
            
            return True, None
            
        except Exception as e:
            return False, f"安全检查失败: {str(e)}"
    
    @staticmethod
    def get_supported_extensions() -> list:
        """
        获取支持的文件扩展名列表
        
        Returns:
            扩展名列表
        """
        extensions = []
        for config in FileValidator.SUPPORTED_TYPES.values():
            extensions.extend(config['extensions'])
        return extensions
    
    @staticmethod
    def get_supported_types() -> list:
        """
        获取支持的文件类型列表
        
        Returns:
            类型列表
        """
        return list(FileValidator.SUPPORTED_TYPES.keys())


# ============================================================================
# 便捷函数
# ============================================================================

def validate_file(file_path: str, max_size: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
    """
    验证文件（便捷函数）
    
    Args:
        file_path: 文件路径
        max_size: 最大文件大小（字节）
        
    Returns:
        (is_valid, file_type, error_message)
    """
    validator = FileValidator(max_size=max_size)
    return validator.validate_file(file_path)


def is_valid_file(file_path: str) -> bool:
    """
    检查文件是否有效（便捷函数）
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否有效
    """
    is_valid, _, _ = validate_file(file_path)
    return is_valid


def get_file_type(file_path: str) -> Optional[str]:
    """
    获取文件类型（便捷函数）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件类型或 None
    """
    is_valid, file_type, _ = validate_file(file_path)
    return file_type if is_valid else None
