"""
日志配置模块 - 使用 loguru
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_dir: str = "logs",
    log_level: str = "INFO",
    log_rotation: str = "10 MB",
    log_retention: str = "7 days"
) -> None:
    """配置 loguru 日志
    
    Args:
        log_dir: 日志文件目录
        log_level: 日志级别
        log_rotation: 日志轮转大小，如 "10 MB", "1 day"
        log_retention: 日志保留时间，如 "7 days", "1 month"
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 移除默认的控制台处理器
    logger.remove()
    
    # 添加控制台处理器（带颜色）
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 添加文件处理器 - 普通日志
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=log_rotation,
        retention=log_retention,
        encoding="utf-8",
        enqueue=True,  # 线程安全
    )
    
    # 添加文件处理器 - 错误日志（单独记录）
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=log_rotation,
        retention=log_retention,
        encoding="utf-8",
        enqueue=True,
    )
    
    logger.info(f"日志系统已初始化 - 日志目录: {log_path.absolute()}, 级别: {log_level}")


# 导出 logger 供其他模块使用
__all__ = ["logger", "setup_logger"]

