from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
# import os
# from dotenv import load_dotenv
from .config import settings

# load_dotenv()

# if "sqlite" in settings.DATABASE_URL:
#     engine = create_engine(
#         settings.DATABASE_URL, connect_args={"check_same_thread": False}
#     )
# else:
#     engine = create_engine(settings.DATABASE_URL)
# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL)
# 将会话工厂绑定到数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建ORM模型的声明式基类
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 在应用启动时创建表的逻辑(重要！)
def create_db_and_tables():
    # 这里的models需要被导入，SQLAlchemy才能知道有哪些表要创建
    from . import models
    Base.metadata.create_all(bind=engine, checkfirst=True)


"""
db = SessionLocal()
new_user = User(name="Alice")
db.add(new_user)
db.commit()
db.close()

"""

"""
如果你想直接使用 sqlite3 命令：

Windows 系统
下载 SQLite 工具：
    访问 SQLite 官网下载页面
    找到 Precompiled Binaries for Windows 部分
    下载 sqlite-tools-win32-*.zip（32位）或 sqlite-tools-win64-*.zip（64位）
    解压下载的 ZIP 文件，你会得到：
    sqlite3.exe（命令行工具）
使用方式：
    将 sqlite3.exe 放到你的项目目录（如 c:\\Users\\sunya\\Desktop\\python_2025\\fastapi_project\\）
    然后在当前目录打开 PowerShell 运行：

bash
.\sqlite3.exe  sql_app.db
或将其所在目录添加到系统环境变量 PATH 中
"""

"""
sqlite3.exe sql_app.db
.tables        # 查看所有表
SELECT * FROM users;  # 查询数据
"""
































