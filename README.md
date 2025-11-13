# 抗生素数据查询系统

这是一个基于Flask的抗生素数据查询系统，提供API接口用于查询抗生素相关信息。

## 项目功能

- 提供抗生素数据查询API
- 支持数据导入和导出功能
- 简单易用的Web界面
- 支持CORS跨域访问

## 本地开发环境设置

### 前提条件

- Python 3.10 或更高版本
- pip 包管理工具

### 安装步骤

1. 克隆仓库
   ```bash
   git clone [仓库URL]
   cd [项目目录]
   ```

2. 创建虚拟环境
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量
   ```bash
   cp .env.example .env
   # 根据需要编辑.env文件
   ```

5. 运行应用
   ```bash
   python app.py
   ```

6. 访问应用
   打开浏览器，访问 http://localhost:5000

## 部署到Heroku

### 准备工作

1. 确保已安装并登录Heroku CLI
   ```bash
   heroku login
   ```

2. 创建Heroku应用
   ```bash
   heroku create [应用名称]
   ```

3. 设置环境变量
   ```bash
   heroku config:set DEBUG=False
   heroku config:set PRODUCTION=True
   # 设置其他必要的环境变量
   ```

### 部署方法

#### 手动部署

```bash
heroku git:remote -a [应用名称]
git push heroku main
```

#### 使用GitHub Actions自动部署

1. 在GitHub仓库中设置以下Secrets：
   - `HEROKU_API_KEY`: 从Heroku账户设置中获取
   - `HEROKU_APP_NAME`: 您的Heroku应用名称

2. 将代码推送到GitHub仓库的main分支，GitHub Actions会自动构建和部署应用。

## 部署到GitHub Pages (静态文件)

如果只需要部署前端界面，可以使用GitHub Pages：

1. 将静态文件（HTML、CSS、JavaScript等）放入`docs`目录
2. 在GitHub仓库设置中启用GitHub Pages，并选择`docs`目录

## API文档

### 抗生素数据查询

**GET /api/antibiotics**

获取所有抗生素数据

**GET /api/antibiotics/search?keyword=xxx**

根据关键词搜索抗生素

## 环境变量配置

请参考`.env.example`文件设置以下环境变量：

- `DEBUG`: 是否启用调试模式
- `PRODUCTION`: 是否为生产环境
- `PORT`: 应用端口
- `ALLOWED_ORIGINS`: 允许的CORS来源
- `ANTIBIOTIC_DATA_PATH`: 抗生素数据文件路径

## 项目结构

```
├── app.py              # 应用主入口
├── Procfile            # Heroku部署配置
├── runtime.txt         # Python版本配置
├── requirements.txt    # 项目依赖
├── antibiotic_data.json # 抗生素数据
├── templates/          # HTML模板
│   └── index.html      # 首页模板
└── .github/workflows/  # GitHub Actions配置
    └── ci_cd.yml       # CI/CD工作流
```

## 许可证

[MIT](LICENSE)