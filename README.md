# Docker GUI 操作工具

一个基于Python/Tkinter开发的Docker图形化操作工具，支持GUI和命令行两种操作模式。

## 作者
[@Quietpeng](https://github.com/Quietpeng)

## 功能特性

1. 双模式支持
   - 图形界面操作
   - 命令行操作

2. Docker基础操作
   - 构建镜像
   - 运行容器
   - 推送镜像
   - 停止容器
   - 删除镜像
   - 从容器创建镜像

3. Dockerfile管理
   - 可视化编辑Dockerfile
   - 支持从模板创建
   - 推荐使用 [docker-compose-files](https://github.com/expoli/docker-compose-files) 模板

4. 监控功能
   - 容器状态实时监控
   - 镜像状态实时监控
   - 操作日志记录
   - 任务进度显示

5. 界面特性
   - 莫兰迪蓝色系界面设计
   - 实时状态更新
   - 操作进度显示
   - 详细的错误提示

## 使用方法

### 环境要求
- Python 3.6+
- Docker已安装并运行
- 必要的Python包（标准库）

### GUI模式
```bash
python app.py
```

### 命令行模式
```bash
# 构建镜像
python app.py --cli --action build --image myimage --tag v1

# 运行容器
python app.py --cli --action run --container mycontainer --ports 8080:80

# 推送镜像
python app.py --cli --action push --image myimage --tag v1

# 停止容器
python app.py --cli --action stop --container mycontainer
```app.py

## 配置说明

配置文件 `config.json` 包含以下设置：
- python_version: Python基础镜像版本
- image_name: 默认镜像名称
- tag_name: 默认标签
- container_name: 默认容器名称
- port_mapping: 默认端口映射
- registry: Docker镜像仓库地址

## 注意事项

- 使用前确保Docker已安装并启动
- 推送镜像前需要先登录Docker Hub
- 所有操作日志保存在 docker_gui_YYYYMMDD.log 文件中
- 任务执行超过1分钟将自动标记为失败


## 致谢

- Dockerfile模板来源：[docker-compose-files](https://github.com/expoli/docker-compose-files)


