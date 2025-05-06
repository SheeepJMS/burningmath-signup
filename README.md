# 数学课程咨询管理系统

这是一个基于Flask的数学课程咨询管理系统，用于管理学生咨询信息和课程信息。

## 功能特点

- 客户信息收集
  - 孩子姓名
  - 微信名字
  - 年级
  - 上课时间偏好
  - 竞赛成绩
  - 学习需求

- 智能班级推荐
  - 根据学生信息自动推荐合适的班级
  - 显示班级详细介绍和图片

- 试课安排
  - 支持立即试课
  - 支持稍后试课
  - 试课时间管理

- 后台管理
  - 客户信息管理
  - 班级信息管理
  - 数据筛选和导出
  - 信息编辑和删除

## 安装说明

1. 克隆项目到本地
2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 初始化数据库：
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
5. 运行应用：
   ```bash
   python app.py
   ```

## 使用说明

1. 访问首页：`http://localhost:5000`
2. 访问管理后台：`http://localhost:5000/admin`
3. 访问班级管理：`http://localhost:5000/admin/classes`

## 技术栈

- 后端：Flask
- 数据库：SQLite
- 前端：Bootstrap 5
- 数据表格：DataTables
- 表单处理：Flask-WTF

## 注意事项

- 请确保在生产环境中修改 `SECRET_KEY`
- 建议定期备份数据库
- 图片上传功能需要配置适当的存储路径 