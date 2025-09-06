### 关键点说明
```bazaar
关键点说明：
数据库配置：
    PostgreSQL服务自动创建
    数据通过volume持久化
    环境变量注入连接字符串
启动流程：
    先执行数据库迁移（alembic upgrade head）
    然后启动FastAPI应用
网络配置：
    web服务通过db主机名访问数据库
    本地8000端口映射到容器8000端口
依赖管理：
    所有Python依赖需在requirements.txt中声明
    构建时自动安装

自定义调整：
调整数据库类型：
    修改db服务的image（如mysql:8.0）
    更新DATABASE_URL格式
生产环境增强：
    添加Gunicorn作为进程管理器
    设置TLS/SSL加密
配置健康检查
使用.env文件管理敏感信息
```
```bazaar
# from . import crud, models, schemas
# from .database import engine, get_db
# import crud, models, schemas
from app import crud, models, schemas
from app.database import engine, get_db
导入方式要使用绝对导入，即from app import xxx
且app路径下需有空的__init__.py文件
因为启动时需要找到app路径下的main.py文件， 是在app之外执行的，所以需要使用绝对导入
从项目根目录启动应用（而不是在 app 目录内）：
uvicorn app.main:app --reload

为什么需要这样修改？
1. __init__.py 文件：
    将 app 目录标记为 Python 包
    允许 Python 识别 app 作为可导入的模块

2. 绝对导入：
    使用 from app import ... 明确指定模块位置
    确保无论从哪里运行脚本，导入路径都正确

3. 从根目录运行：
    Python 会自动将当前目录添加到模块搜索路径
    这样就能正确找到 app 包

```

```
docker-compose down --volumes 和docker-compose down -v一样的， 这是一个完整清理 Docker Compose 环境 的命令，它会停止并彻底删除所有与当前项目相关的容器、网络、以及关键的数据卷。

docker-compose up --build

# 停止并删除所有容器（包括运行的）
docker-compose down --rmi all --volumes --remove-orphans
# 强制删除镜像
docker rmi -f fastapi_project-web:latest
# 清理未使用的容器、网络、镜像和构建缓存
docker system prune -a --volumes

docker-compose down --rmi all：停止并删除容器、网络，同时删除所有相关镜像
--volumes：删除所有命名卷
--remove-orphans：删除未在 compose 文件中定义的容器

# 3. 查看日志
docker-compose logs -f web
```
```bazaar
这个配置方案提供了生产环境所需的所有关键组件，包括：
HTTPS加密通信
静态文件高效服务
负载均衡和反向代理
数据库持久化存储
容器自动恢复
优化的性能配置
```
```bazaar
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app

-k uvicorn.workers.UvicornWorker	
    必选,使用 Uvicorn 作为 Worker 处理 ASGI 应用（FastAPI）
    
--workers CPU核心数*2+1	进程数（如 4核CPU → 9 workers）
--threads 2	每个 Worker 的线程数（适合 I/O 密集型应用）
--limit-request-line	8190	防止超大请求头攻击
```

```bazaar
特别注意：
location /static/ {
    alias /app/static/;  # 必须与 Docker 卷挂载路径一致
}
```
```bazaar

在 Windows 宿主机上为 Nginx 生成 SSL 证书（自签名或正式证书）的步骤如下：
在 PowerShell 中执行：
# 创建证书目录（对应 docker-compose 中的 ./nginx/ssl）
mkdir -p nginx/ssl
cd nginx/ssl

# 生成私钥（无密码）
openssl genrsa -out privkey.pem 2048

# 生成自签名证书（有效期365天）
openssl req -new -x509 -key privkey.pem -out fullchain.pem -days 365 -subj "/CN=localhost"
# 使用 PowerShell 命令安装
# 管理员身份运行 PowerShell
Import-Certificate -FilePath "C:\path\to\fullchain.pem" -CertStoreLocation Cert:\LocalMachine\Root

如果 Docker 报权限错误，执行：
# 重置证书目录权限
icacls nginx\ssl /reset
icacls nginx\ssl /grant "Everyone:(R)"

# 重置静态文件权限
icacls .\app\static /grant "Everyone:(R)"
```
```bazaar
1.检查容器网络
docker network inspect yourproject_app-network

2.在 Nginx 容器内测试连通性
docker exec -it nginx_container sh
ping web       # 应能解析IP
nc -zv web 8000  # 应显示连接成功
```



































