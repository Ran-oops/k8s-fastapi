# FastAPI 商品评价系统

使用 Docker Compose 和 Kubernetes 部署的 FastAPI + PostgreSQL + Redis + Kafka + Elasticsearch 项目，提供完整的商品管理和评价处理 API。
集成的所有组件（FastAPI, PostgreSQL, Redis, Kafka, Prometheus, ELK Stack for logging, Elasticsearch for search）

## 功能特性

- 创建和管理商品信息
- 提交商品评价（异步处理）
- 缓存优化（Redis）
- 消息队列处理（Kafka）
- 全文搜索支持（Elasticsearch）
- 监控和指标收集（Prometheus + Grafana）
- 容器化部署（Docker Compose & Kubernetes）
- 结构化日志记录（ELK Stack）
- 健康检查和错误处理

## 技术栈

- **后端**: FastAPI (Python)
- **数据库**: PostgreSQL
- **缓存**: Redis
- **消息队列**: Kafka
- **搜索引擎**: Elasticsearch
- **Web服务器**: Nginx
- **容器化**: Docker & Docker Compose
- **编排**: Kubernetes
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (Elasticsearch, Logstash, Filebeat, Kibana)

## 项目架构

本项目采用微服务架构，通过异步消息队列实现评价处理的解耦。主要组件包括：

1. **FastAPI 应用** - 提供 RESTful API 接口
2. **PostgreSQL** - 主数据库，存储商品和评价数据
3. **Redis** - 缓存层，提高数据访问速度
4. **Kafka** - 消息队列，异步处理评价数据
5. **Elasticsearch** - 搜索引擎，提供商品搜索功能
6. **Prometheus + Grafana** - 监控系统，收集和可视化指标
7. **ELK Stack** - 日志收集和分析系统

## 安装指南

### 开发环境

1. 克隆项目:
   ```
   git clone <项目地址>
   cd fastapi_project
   ```

2. 确保已安装 Docker 和 Docker Compose

3. 构建并启动开发环境:
   ```
   docker-compose up --build
   ```

4. 访问应用: http://localhost:8000 和 http://localhost:8000/docs#

### 生产环境

1. 构建并启动生产环境:
   ```
   docker-compose -f docker-compose.prod.yml up --build
   # 自动构建镜像并启动所有容器服务，特别适合在修改代码或配置后使用
   -d: 后台运行 (detach)
   -remove-orphans: 清理不再使用的容器
   --build： 强制重新构建服务镜像
   ```
   ```bazaar
    # 一些命令说明
    # docker-compose build; 仅构建镜像，不启动容器; 需要提前构建好镜像
    # docker-compose up; 启动所有容器服务,使用现有镜像; 没有代码/配置变更时
    # docker-compose up -d; 构建+启动完整流程; 开发调试中最常见
   ```

2. 应用将通过 Nginx 提供服务，访问端口为 80

## API 接口文档

- 交互式 API 文档: http://localhost:80/docs
- 替代 API 文档: http://localhost:80/redoc

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/products/` | 创建新商品 |
| GET | `/products/{product_id}` | 获取特定商品信息 |
| POST | `/reviews/` | 提交商品评价（异步处理） |
| GET | `/health` | 健康检查端点 |

## Kubernetes 部署

项目支持 Kubernetes 部署，包含以下组件：

- FastAPI 应用服务
- PostgreSQL 数据库
- Redis 缓存
- Kafka 消息队列
- Elasticsearch 搜索引擎
- Prometheus 监控
- Grafana 可视化

### 部署步骤

1. 构建并推送 Docker 镜像:
   ```bash
   # 构建 FastAPI 应用镜像
   docker build -t your-registry/fastapi-app:latest -f Dockerfile.prod .
   
   # 构建评价消费者镜像
   docker build -t your-registry/review-consumer:latest -f Dockerfile.consumer .
   
   # 推送镜像到镜像仓库
   docker push your-registry/fastapi-app:latest
   docker push your-registry/review-consumer:latest
   ```

2. 部署到 Kubernetes 集群:
   ```bash
   # 应用所有 Kubernetes 配置
   kubectl apply -f k8s/
   ```

3. 验证部署:
   ```bash
   # 检查 Pod 状态
   kubectl get pods -n my-fastapi-stack
   
   # 检查服务状态
   kubectl get services -n my-fastapi-stack
   ```

### 注意事项

1. 需要先安装配置 Helm 和相应的依赖服务（Kafka、Elasticsearch）
2. 需要替换 Kubernetes 配置文件中的镜像地址为实际地址
3. 需要创建必要的 Secret 来存储敏感信息（数据库密码等）

## 项目结构

```
fastapi_project/
├── app/                      # FastAPI 应用代码
│   ├── __init__.py
│   ├── main.py               # 主应用入口
│   ├── models.py             # 数据库模型
│   ├── schemas.py            # Pydantic 模型
│   ├── crud.py               # 数据库操作
│   ├── database.py           # 数据库连接
│   ├── config.py             # 配置管理
│   ├── services/             # 服务层（Redis、Kafka等）
│   ├── consumers/            # Kafka消费者
│   └── static/               # 静态文件（CSS/JS等）
│
├── nginx/
│   ├── nginx.conf            # Nginx 主配置文件
│   └── ssl/                  # SSL 证书目录
│       ├── fullchain.pem     # 证书链
│       └── privkey.pem       # 私钥
│
├── prometheus/
│   └── prometheus.yml        # Prometheus 监控配置
│
├── grafana/
│   └── provisioning/         # Grafana 预配置
│       ├── dashboards/       # 仪表盘JSON文件
│       └── datasources/      # 数据源配置
│
├── k8s/                      # Kubernetes 部署配置
│   ├── 00-namespace.yml      # 命名空间
│   ├── 01-fastapi-configmap.yml  # ConfigMap配置
│   ├── 02-postgres.yml       # PostgreSQL部署
│   ├── 03-redis.yml          # Redis部署
│   ├── 04-fastapi.yml        # FastAPI应用部署
│   ├── 05-ingress.yml        # Ingress配置
│   └── 06-consumer.yml       # 评价消费者部署
│
├── docker-compose.yml        # 开发环境部署文件
├── docker-compose.prod.yml   # 生产环境部署文件
├── Dockerfile.prod           # FastAPI 生产镜像构建文件
├── Dockerfile.consumer       # 评价消费者镜像构建文件
├── requirements.txt          # Python 依赖
└── .env                      # 环境变量（可选）
```

## 目录结构特点

1. 分层清晰
   - 服务配置（Nginx/Prometheus）与应用代码分离
   - 监控系统配置集中管理

2. 安全性
   - SSL 证书独立目录，方便权限控制
   - 敏感配置（如数据库密码）通过 .env 或 Kubernetes Secrets 管理

3. 可扩展性
   - 添加新服务只需在 docker-compose.yml 或 k8s/ 目录下扩展
   - 监控仪表盘通过 Grafana 目录动态加载

4. 生产就绪
   - 包含从应用服务到监控的全套配置
   - 支持 HTTPS、性能监控、数据持久化
   - 支持 Docker Compose 和 Kubernetes 两种部署方式

## 开发说明

开发模式下启用了热重载功能，修改代码后会自动重启服务。

运行开发服务器的命令:
```
uvicorn app.main:app --reload
```

运行生产服务器的命令:
```
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
```

## 监控

项目集成了 Prometheus 和 Grafana 用于监控:

- Prometheus: http://localhost:9090/targets
- Grafana: http://localhost:3000 (默认账号admin/admin)
- FastAPI内置指标: http://localhost:8000/metrics

## 日志查看

### Docker Compose 环境

检查fastapi日志：
```
docker-compose -f docker-compose.prod.yml logs web
```

进入Nginx容器测试连通性：
```
docker exec -it fastapi_project-nginx-1 sh
wget -O- http://web:8000
```

### Kubernetes 环境

查看应用日志：
```
kubectl logs -f deployment/fastapi-deployment -n my-fastapi-stack
```

查看消费者日志：
```
kubectl logs -f deployment/review-consumer-deployment -n my-fastapi-stack
```

## 数据库

项目使用 PostgreSQL 作为主数据库:

- Docker Compose 环境: 通过 docker-compose.yml 配置
- Kubernetes 环境: 通过 k8s/02-postgres.yml 配置

数据库文件持久化存储在 `pg_data` 卷中。

## 备份方案： 定期备份关键卷
```
docker run --rm -v pg_data:/volume -v /backup:/backup alpine tar cvf /backup/pg_backup.tar /volume
```

## 项目重启
```
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 常见问题

### 1. 权限问题
在 Windows 系统上，可能会遇到 SSL 证书权限问题。可以使用以下命令解决：
```powershell
# 重置证书目录权限
icacls nginx\ssl /reset
icacls nginx\ssl /grant "Everyone:(R)"

# 重置静态文件权限
icacls .\app\static /grant "Everyone:(R)"
```

### 2. 网络连接问题
如果容器间无法通信，可以检查网络连接：
```bash
# 检查容器网络
docker network inspect yourproject_app-network

# 在 Nginx 容器内测试连通性
docker exec -it nginx_container sh
ping web       # 应能解析IP
nc -zv web 8000  # 应显示连接成功
```

### 3. 清理环境
如果需要完全清理环境，可以使用以下命令：
```bash
# 停止并删除所有容器（包括运行的）
docker-compose down --rmi all --volumes --remove-orphans

# 强制删除镜像
docker rmi -f fastapi_project-web:latest

# 清理未使用的容器、网络、镜像和构建缓存
docker system prune -a --volumes
```

## 安全建议

1. 不要将敏感信息（如数据库密码）硬编码在代码中
2. 使用环境变量或 Kubernetes Secrets 管理敏感信息
3. 定期更新依赖包以修复安全漏洞
4. 使用 HTTPS 加密通信
5. 限制对管理接口的访问

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request