"""
数据库初始化脚本
创建所有表并进行基本设置
"""
import asyncio
from database import init_db


async def main():
    """主函数：初始化数据库"""
    print("开始初始化数据库...")
    await init_db()
    print("数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())

