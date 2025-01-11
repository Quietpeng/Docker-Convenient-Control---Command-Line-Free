"""
Docker GUI 操作工具
作者: @Quietpeng (https://github.com/Quietpeng)
版本: 1.0.0
描述: 一个基于Python/Tkinter开发的Docker图形化操作工具，支持GUI和命令行两种操作模式。
"""

import subprocess
import logging
import os
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
import webbrowser
from config import load_config, save_config
import argparse

# 日志配置
logging.basicConfig(
    filename=f'docker_gui_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_command(command, status_bar=None, task_name=None):
    """执行 shell 命令并返回输出或错误信息"""
    try:
        logging.info(f"执行命令: {command}")
        if status_bar and task_name:
            status_bar.set_status(task_name, is_task=True)
        
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout
        logging.info(f"命令执行成功: {output}")
        
        if status_bar and task_name:
            status_bar.task_complete(task_name, success=True)
        return output
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        logging.error(error_msg)
        if status_bar and task_name:
            status_bar.task_complete(task_name, success=False)
        return error_msg

def create_dockerfile(root):
    """生成 Dockerfile"""
    try:
        config = load_config()
        python_version = simpledialog.askstring(
            "Python版本",
            "请输入Python版本:",
            initialvalue=config["python_version"]
        )
        
        if not python_version:
            return
            
        dockerfile_content = f"""\
# 使用官方 Python 基础镜像
FROM {config['registry']}/python:{python_version}

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]
"""
        editor = TextEditor(root, "编辑 Dockerfile", dockerfile_content, 
                          lambda content: save_dockerfile(content))
        
    except Exception as e:
        logging.error(f"生成Dockerfile失败: {str(e)}")
        messagebox.showerror("错误", f"生成Dockerfile失败: {str(e)}")

def parse_args():
    """命令行参数解析"""
    parser = argparse.ArgumentParser(description='Docker GUI工具')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--action', choices=['build', 'run', 'push', 'stop'], help='执行的操作')
    parser.add_argument('--image', help='镜像名称')
    parser.add_argument('--tag', help='标签名称')
    parser.add_argument('--container', help='容器名称')
    parser.add_argument('--ports', help='端口映射，例如 8080:80')
    return parser.parse_args()

def list_images():
    """列出所有镜像"""
    try:
        output = run_command('docker images')
        return output if output else "暂无镜像"
    except Exception as e:
        return f"错误: 无法获取镜像列表 - {str(e)}"

def list_containers():
    """列出所有容器"""
    try:
        output = run_command('docker ps -a')
        return output if output else "暂无容器"
    except Exception as e:
        return f"错误: 无法获取容器列表 - {str(e)}"

def stop_container(container_name):
    """停止指定容器"""
    try:
        output = run_command(f"docker stop {container_name}")
        logging.info(f"容器 {container_name} 已停止")
        return output
    except Exception as e:
        logging.error(f"停止容器失败: {str(e)}")
        return str(e)

def show_container_logs(container_name):
    """显示容器日志"""
    return run_command(f"docker logs {container_name}")

def cli_mode(args):
    """命令行模式"""
    config = load_config()
    
    if args.action == 'build':
        image_name = args.image or config['image_name']
        tag_name = args.tag or config['tag_name']
        print(build_image(image_name, tag_name))
    
    elif args.action == 'run':
        image_name = args.image or config['image_name']
        tag_name = args.tag or config['tag_name']
        container_name = args.container or config['container_name']
        ports = args.ports or config['port_mapping']
        print(run_container(image_name, tag_name, container_name, ports))
    
    elif args.action == 'push':
        image_name = args.image or config['image_name']
        tag_name = args.tag or config['tag_name']
        print(push_image(image_name, tag_name))
    
    elif args.action == 'stop':
        container_name = args.container or config['container_name']
        print(stop_container(container_name))

def create_gui():
    """创建图形用户界面"""
    global image_tree, container_tree, root
    
    if not check_docker_installed():
        show_docker_error()
        return
        
    root = tk.Tk()
    root.title("Docker 操作工具")
    
    # 修改窗口大小
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 添加状态栏
    status_bar = StatusBar(root)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # 定义按钮样式
    button_style = {
        'font': ('Arial', 12),
        'width': 20,
        'height': 2,
        'bg': "#A4C3D2",  # 莫兰迪蓝色系
        'fg': "#2C3E50",
        'relief': tk.RAISED
    }
    
    try:
        config = load_config()
    except FileNotFoundError as e:
        messagebox.showerror("错误", str(e))
        return
    
    # 主框架
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 状态显示区域
    status_notebook = ttk.Notebook(main_frame)
    status_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    # 镜像状态页
    image_frame = ttk.Frame(status_notebook)
    status_notebook.add(image_frame, text="镜像状态")
    
    # 创建镜像列表
    image_tree = ttk.Treeview(image_frame, columns=('镜像名称', '标签', 'ID', '大小'), show='headings')
    for col in ('镜像名称', '标签', 'ID', '大小'):
        image_tree.heading(col, text=col)
    image_tree.column('镜像名称', width=300)
    image_tree.column('标签', width=100)
    image_tree.column('ID', width=200)
    image_tree.column('大小', width=100)
    
    image_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=image_tree.yview)
    image_tree.configure(yscrollcommand=image_scrollbar.set)
    
    image_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    image_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 镜像操作按钮
    image_button_frame = tk.Frame(image_frame, bg="#E8F4F8")
    image_button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
    
    tk.Button(image_button_frame, text="生成Dockerfile",
              command=lambda: create_dockerfile(root),
              **button_style).pack(pady=5)
              
    tk.Button(image_button_frame, text="构建镜像",
              command=lambda: build_from_dockerfile(root, status_bar),
              **button_style).pack(pady=5)
              
    tk.Button(image_button_frame, text="删除镜像",
              command=lambda: delete_selected_image(image_tree, status_bar),
              **button_style).pack(pady=5)
              
    tk.Button(image_button_frame, text="推送镜像",
              command=lambda: push_selected_image(image_tree, status_bar),
              **button_style).pack(pady=5)
              
    tk.Button(image_button_frame, text="查看远程镜像",
              command=lambda: show_registry_images(root),
              **button_style).pack(pady=5)
    
    # 容器状态页
    container_frame = ttk.Frame(status_notebook)
    status_notebook.add(container_frame, text="容器状态")
    
    # 创建容器列表
    container_tree = ttk.Treeview(container_frame, 
                                 columns=('容器ID', '名称', '镜像', '状态', '端口'),
                                 show='headings')
    for col in ('容器ID', '名称', '镜像', '状态', '端口'):
        container_tree.heading(col, text=col)
    container_tree.column('容器ID', width=100)
    container_tree.column('名称', width=200)
    container_tree.column('镜像', width=200)
    container_tree.column('状态', width=150)
    container_tree.column('端口', width=150)
    
    container_scrollbar = ttk.Scrollbar(container_frame, orient=tk.VERTICAL, command=container_tree.yview)
    container_tree.configure(yscrollcommand=container_scrollbar.set)
    
    container_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    container_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 容器操作按钮
    container_button_frame = tk.Frame(container_frame, bg="#E8F4F8")
    container_button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
    
    tk.Button(container_button_frame, text="创建镜像",
              command=lambda: create_image_from_selected_container(container_tree, status_bar),
              **button_style).pack(pady=5)
              
    tk.Button(container_button_frame, text="停止容器",
              command=lambda: stop_selected_container(container_tree),
              **button_style).pack(pady=5)
    
    def update_status():
        try:
            # 更新容器列表
            for item in container_tree.get_children():
                container_tree.delete(item)
            
            containers = run_command('docker ps -a --format "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"').split('\n')
            for container in containers:
                if container.strip():
                    try:
                        id_, name, image, status, ports = container.split('\t')
                        container_tree.insert('', tk.END, values=(id_, name, image, status, ports))
                    except ValueError:
                        continue
            
            # 更新镜像列表
            for item in image_tree.get_children():
                image_tree.delete(item)
            
            images = run_command('docker images --format "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"').split('\n')
            for image in images:
                if image.strip():
                    try:
                        repo, tag, id_, size = image.split('\t')
                        image_tree.insert('', tk.END, values=(repo, tag, id_, size))
                    except ValueError:
                        continue
            
            root.after(5000, update_status)  # 每5秒更新一次
        except Exception as e:
            logging.error(f"更新状态时出错: {str(e)}")
            messagebox.showerror("错误", f"更新状态时出错: {str(e)}")
    
    # 启动状态更新
    update_status()
    root.mainloop()

def show_container_logs_gui(root):
    """显示容器日志的GUI函数"""
    container_name = simpledialog.askstring("查看日志", "请输入容器名称:")
    if container_name:
        progress = ProgressWindow(root, "获取日志")
        progress.update_status(f"正在获取容器 {container_name} 的日志...")
        try:
            logs = show_container_logs(container_name)
            progress.finish()
            
            log_window = tk.Toplevel(root)
            log_window.title(f"容器日志 - {container_name}")
            log_window.geometry("1000x600")
            
            log_text = tk.Text(log_window, height=30, width=100, font=('Courier', 12))
            log_scrollbar = ttk.Scrollbar(log_window, orient=tk.VERTICAL, command=log_text.yview)
            log_text.configure(yscrollcommand=log_scrollbar.set)
            
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            log_text.insert(tk.END, logs)
        except Exception as e:
            progress.finish()
            messagebox.showerror("错误", f"获取日志失败: {str(e)}")

def create_image_from_container_gui(root):
    """从容器创建镜像的GUI函数"""
    container_name = simpledialog.askstring("创建镜像", "请输入容器名称:")
    if container_name:
        new_image_name = simpledialog.askstring("创建镜像", "请输入新镜像名称:")
        if new_image_name:
            tag = simpledialog.askstring("创建镜像", "请输入标签(默认latest):", initialvalue="latest")
            if tag:
                progress = ProgressWindow(root, "创建镜像")
                progress.update_status(f"正在从容器 {container_name} 创建镜像...")
                try:
                    output = commit_container(container_name, new_image_name, tag)
                    progress.finish()
                    if "错误" not in output:
                        messagebox.showinfo("成功", f"已从容器 {container_name} 创建镜像 {new_image_name}:{tag}")
                    else:
                        messagebox.showerror("错误", output)
                except Exception as e:
                    progress.finish()
                    messagebox.showerror("错误", f"创建镜像失败: {str(e)}")

def build_image(image_name, tag_name):
    """构建Docker镜像"""
    try:
        command = f"docker build -t {image_name}:{tag_name} ."
        output = run_command(command)
        logging.info(f"镜像构建成功: {image_name}:{tag_name}")
        return output
    except Exception as e:
        logging.error(f"镜像构建失败: {str(e)}")
        return str(e)

def run_container(image_name, tag_name, container_name, port_mapping):
    """运行Docker容器"""
    try:
        command = f"docker run -d -p {port_mapping} --name {container_name} {image_name}:{tag_name}"
        output = run_command(command)
        logging.info(f"容器启动成功: {container_name}")
        return output
    except Exception as e:
        logging.error(f"容器启动失败: {str(e)}")
        return str(e)

def push_image(image_name, tag_name):
    """推送Docker镜像"""
    try:
        command = f"docker push {image_name}:{tag_name}"
        output = run_command(command)
        logging.info(f"镜像推送成功: {image_name}:{tag_name}")
        return output
    except Exception as e:
        logging.error(f"镜像推送失败: {str(e)}")
        return str(e)

def check_registry_images(parent_window, image_name):
    """检查Docker Hub上的镜像"""
    try:
        progress = ProgressWindow(parent_window, "检查远程镜像")
        progress.update_status("正在查询Docker Hub...")
        output = run_command(f'docker search {image_name}')
        progress.finish()
        return output
    except Exception as e:
        return f"错误: 无法获取远程镜像信息 - {str(e)}"

def commit_container(container_id, new_image_name, tag="latest", status_bar=None):
    """从容器创建新镜像"""
    try:
        task_name = "创建镜像"
        command = f'docker commit {container_id} {new_image_name}:{tag}'
        output = run_command(command, status_bar, task_name)
        
        if "错误" not in output:
            logging.info(f"成功从容器 {container_id} 创建镜像 {new_image_name}:{tag}")
            messagebox.showinfo("成功", f"已从容器 {container_id} 创建镜像 {new_image_name}:{tag}")
            return True
        else:
            logging.error(f"创建镜像失败: {output}")
            messagebox.showerror("错误", output)
            return False
    except Exception as e:
        error_msg = f"创建镜像失败: {str(e)}"
        logging.error(error_msg)
        messagebox.showerror("错误", error_msg)
        return False

def create_image_from_selected_container(tree, status_bar):
    """从选中的容器创建镜像"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择一个容器")
        return
    
    container_id = tree.item(selection[0])['values'][0]
    new_image_name = simpledialog.askstring("创建镜像", "请输入新镜像名称:")
    if new_image_name:
        tag = simpledialog.askstring("创建镜像", "请输入标签(默认latest):", initialvalue="latest")
        if tag:
            if commit_container(container_id, new_image_name, tag, status_bar):
                # 获取主窗口中的树形控件
                main_window = tree.winfo_toplevel()
                for child in main_window.winfo_children():
                    if isinstance(child, ttk.Treeview):
                        if 'ID' in child['columns']:  # 镜像树
                            image_tree = child
                        elif '容器ID' in child['columns']:  # 容器树
                            container_tree = child
                update_lists(image_tree, container_tree)

class TextEditor(tk.Toplevel):
    def __init__(self, parent, title, initial_text="", callback=None):
        super().__init__(parent)
        self.title(title)
        self.callback = callback
        
        # 设置窗口大小
        self.geometry("800x600")
        
        # 创建文本编辑区
        self.text_area = tk.Text(self, wrap=tk.WORD, font=('Courier', 12),
                               bg="#E8F4F8", fg="#2C3E50")  # 莫兰迪蓝色系
        self.text_area.pack(expand=True, fill='both', padx=10, pady=5)
        self.text_area.insert('1.0', initial_text)
        
        # 添加推荐链接
        recommend_label = tk.Label(
            self,
            text="推荐在 https://github.com/expoli/docker-compose-files 获取Dockerfile模板",
            fg="#2C3E50",
            cursor="hand2"
        )
        recommend_label.pack(pady=5)
        recommend_label.bind("<Button-1>", 
                           lambda e: webbrowser.open("https://github.com/expoli/docker-compose-files"))
        
        # 创建按钮框
        button_frame = tk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # 保存按钮
        tk.Button(button_frame, text="保存并构建",
                 command=self.save_and_build,
                 bg="#A4C3D2", fg="#2C3E50").pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="仅保存",
                 command=self.save_and_close,
                 bg="#A4C3D2", fg="#2C3E50").pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="取消",
                 command=self.destroy,
                 bg="#A4C3D2", fg="#2C3E50").pack(side=tk.RIGHT, padx=5)
    
    def save_and_build(self):
        if self.callback:
            self.callback(self.text_area.get('1.0', tk.END))
        self.destroy()
        build_from_dockerfile(self.master, self.master.status_bar)

    def save_and_close(self):
        if self.callback:
            self.callback(self.text_area.get('1.0', tk.END))
        self.destroy()

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        
        # 设置窗口大小和位置
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()
        
        # 进度条
        self.progress = ttk.Progressbar(self, mode='indeterminate', length=300)
        self.progress.pack(pady=20)
        
        # 状态标签
        self.status_label = tk.Label(self, text="处理中...", font=('Arial', 10))
        self.status_label.pack(pady=10)
        
        self.progress.start(10)
    
    def update_status(self, text):
        self.status_label.config(text=text)
    
    def finish(self):
        self.progress.stop()
        self.destroy()

def create_image_list(image_frame):
    """创建镜像列表"""
    # 创建表格
    columns = ('镜像名称', '标签', 'ID', '大小')
    tree = ttk.Treeview(image_frame, columns=columns, show='headings', selectmode='browse')
    
    # 设置列标题和宽度
    tree.heading('镜像名称', text='镜像名称', anchor='w')
    tree.heading('标签', text='标签', anchor='w')
    tree.heading('ID', text='ID', anchor='w')
    tree.heading('大小', text='大小', anchor='w')
    
    tree.column('镜像名称', width=300)
    tree.column('标签', width=100)
    tree.column('ID', width=200)
    tree.column('大小', width=100)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # 放置控件
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    return tree

def update_image_list(tree):
    """更新镜像列表"""
    # 记住当前选中项
    selected = None
    selection = tree.selection()
    if selection:
        current = tree.item(selection[0])
        if current and 'values' in current:
            selected = current['values'][2]  # 保存 ID
    
    # 清空现有项目
    for item in tree.get_children():
        tree.delete(item)
    
    # 获取镜像列表
    images = run_command('docker images --format "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"').split('\n')
    
    # 添加到表格
    for image in images:
        if image.strip():
            repo, tag, id_, size = image.split('\t')
            item = tree.insert('', tk.END, values=(repo, tag, id_, size))
            # 恢复选中状态
            if selected and id_ == selected:
                tree.selection_set(item)

def delete_selected_image(tree, status_bar):
    """删除选中的镜像"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要删除的镜像")
        return
    
    item = selection[0]
    values = tree.item(item)['values']
    image_id = values[2]  # ID 在第三列
    
    if messagebox.askyesno("确认", f"确定要删除选中的镜像吗？\n这将强制删除镜像及其所有标签。"):
        status_bar.set_status("删除镜像", is_task=True)
        try:
            output = run_command(f"docker rmi -f {image_id}")
            if "错误" not in output:
                messagebox.showinfo("成功", "镜像已删除")
                status_bar.task_complete("删除镜像", success=True)
                update_lists(image_tree, container_tree)
            else:
                messagebox.showerror("错误", output)
                status_bar.task_complete("删除镜像", success=False)
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
            status_bar.task_complete("删除镜像", success=False)

def create_container_from_image(tree):
    """从选中的镜像创建并运行容器"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择一个镜像")
        return
    
    item = selection[0]
    values = tree.item(item)['values']
    repo, tag = values[0], values[1]
    
    # 获取容器配置
    container_name = simpledialog.askstring("容器名称", "请输入容器名称:")
    if not container_name:
        return
    
    port_mapping = simpledialog.askstring("端口映射", "请输入端口映射 (例如: 8080:80):")
    if not port_mapping:
        return
    
    progress = ProgressWindow(root, "创建容器")
    progress.update_status("正在创建并启动容器...")
    
    try:
        output = run_container(repo, tag, container_name, port_mapping)
        progress.finish()
        if "错误" in output:
            messagebox.showerror("错误", output)
        else:
            messagebox.showinfo("成功", f"容器 {container_name} 已创建并启动")
    except Exception as e:
        progress.finish()
        messagebox.showerror("错误", str(e))

def check_registry_images_gui(root):
    """检查远程镜像的GUI函数"""
    image_name = simpledialog.askstring("检查远程镜像", "请输入要查询的镜像名称:")
    if image_name:
        progress = ProgressWindow(root, "检查远程镜像")
        progress.update_status("正在查询Docker Hub...")
        try:
            output = run_command(f'docker search {image_name}')
            progress.finish()
            
            result_window = tk.Toplevel(root)
            result_window.title(f"远程镜像查询结果 - {image_name}")
            result_window.geometry("1000x600")
            
            result_text = tk.Text(result_window, height=30, width=100, font=('Courier', 12))
            result_scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=result_text.yview)
            result_text.configure(yscrollcommand=result_scrollbar.set)
            
            result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            result_text.insert(tk.END, output)
        except Exception as e:
            progress.finish()
            messagebox.showerror("错误", f"查询失败: {str(e)}")

def save_dockerfile(content):
    """保存 Dockerfile 内容"""
    try:
        with open("Dockerfile", "w", encoding='utf-8') as f:
            f.write(content)
        logging.info("Dockerfile生成成功")
        messagebox.showinfo("成功", "Dockerfile 已生成在当前目录下。")
    except Exception as e:
        logging.error(f"保存Dockerfile失败: {str(e)}")
        messagebox.showerror("错误", f"保存Dockerfile失败: {str(e)}")

def update_lists(image_tree, container_tree):
    """更新镜像和容器列表"""
    # 更新镜像列表
    for item in image_tree.get_children():
        image_tree.delete(item)
    
    images = run_command('docker images --format "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"').split('\n')
    for image in images:
        if image.strip():
            repo, tag, id_, size = image.split('\t')
            image_tree.insert('', tk.END, values=(repo, tag, id_, size))
    
    # 更新容器列表
    for item in container_tree.get_children():
        container_tree.delete(item)
    
    containers = run_command('docker ps -a --format "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"').split('\n')
    for container in containers:
        if container.strip():
            id_, name, image, status, ports = container.split('\t')
            container_tree.insert('', tk.END, values=(id_, name, image, status, ports))

def show_registry_images(root):
    """显示远程镜像列表"""
    result_window = tk.Toplevel(root)
    result_window.title("Docker Hub 镜像")
    result_window.geometry("1000x600")
    
    # 创建搜索框
    search_frame = tk.Frame(result_window)
    search_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
    search_entry = tk.Entry(search_frame, width=50)
    search_entry.pack(side=tk.LEFT, padx=5)
    
    # 创建结果列表
    tree = ttk.Treeview(result_window, columns=('名称', '描述', '星标数', '官方'), show='headings')
    for col in ('名称', '描述', '星标数', '官方'):
        tree.heading(col, text=col)
    tree.column('名称', width=200)
    tree.column('描述', width=500)
    tree.column('星标数', width=100)
    tree.column('官方', width=100)
    
    scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    def search():
        progress = ProgressWindow(result_window, "搜索镜像")
        progress.update_status("正在搜索...")
        try:
            output = run_command(f'docker search {search_entry.get()} --format "{{{{.Name}}}}\t{{{{.Description}}}}\t{{{{.StarCount}}}}\t{{{{.IsOfficial}}}}"')
            for item in tree.get_children():
                tree.delete(item)
            
            for line in output.split('\n'):
                if line.strip():
                    name, desc, stars, official = line.split('\t')
                    tree.insert('', tk.END, values=(name, desc, stars, official))
            
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {str(e)}")
        finally:
            progress.finish()
    
    tk.Button(search_frame, text="搜索", command=search).pack(side=tk.LEFT, padx=5)
    
    def pull_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个镜像")
            return
        
        image_name = tree.item(selection[0])['values'][0]
        progress = ProgressWindow(result_window, "拉取镜像")
        progress.update_status(f"正在拉取 {image_name}...")
        try:
            output = run_command(f'docker pull {image_name}')
            progress.finish()
            if "错误" not in output:
                messagebox.showinfo("成功", f"镜像 {image_name} 已拉取")
                update_lists(image_tree, container_tree)
            else:
                messagebox.showerror("错误", output)
        except Exception as e:
            progress.finish()
            messagebox.showerror("错误", f"拉取失败: {str(e)}")
    
    tk.Button(result_window, text="拉取选中镜像", command=pull_selected).pack(pady=5)

def show_selected_container_logs(tree):
    """显示选中容器的日志"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择一个容器")
        return
    
    container_id = tree.item(selection[0])['values'][0]
    show_container_logs_gui(root, container_id)

def stop_selected_container(tree):
    """停止选中的容器"""
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择一个容器")
        return
    
    container_id = tree.item(selection[0])['values'][0]
    if messagebox.askyesno("确认", "确定要停止选中的容器吗？"):
        progress = ProgressWindow(root, "停止容器")
        progress.update_status(f"正在停止容器 {container_id}...")
        try:
            output = stop_container(container_id)
            progress.finish()
            if "错误" not in output:
                messagebox.showinfo("成功", "容器已停止")
                update_lists(image_tree, container_tree)
            else:
                messagebox.showerror("错误", output)
        except Exception as e:
            progress.finish()
            messagebox.showerror("错误", f"停止失败: {str(e)}")

class StatusBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.CENTER,
                            bg="#A4C3D2", fg="#2C3E50",
                            font=('Arial', 10))
        self.label.pack(fill=tk.X)
        self.task_start_time = None
        
    def set_status(self, text, is_task=False):
        if is_task:
            self.task_start_time = datetime.now()
            self.label.config(text=f"{text}任务正在进行中.....")
            self.check_timeout(text)
        else:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.label.config(text=f"{text} - {current_time}")
    
    def check_timeout(self, task_name):
        if self.task_start_time:
            elapsed = (datetime.now() - self.task_start_time).total_seconds()
            if elapsed >= 60:  # 1分钟超时
                self.task_complete(task_name, success=False, message="任务超时")
            else:
                self.after(1000, lambda: self.check_timeout(task_name))
    
    def task_complete(self, task_name, success=True, message=None):
        self.task_start_time = None
        current_time = datetime.now().strftime("%H:%M:%S")
        status = "成功" if success else "失败"
        status_text = f"{task_name}任务{status}"
        if message:
            status_text += f": {message}"
        status_text += f" - {current_time}"
        self.label.config(text=status_text)

def show_program_logs():
    """显示程序日志"""
    log_window = tk.Toplevel(root)
    log_window.title("程序日志")
    log_window.geometry("1000x600")
    
    log_text = tk.Text(log_window, height=30, width=100, font=('Courier', 12),
                      bg="#E8F4F8", fg="#2C3E50")  # 莫兰迪蓝色系
    log_scrollbar = ttk.Scrollbar(log_window, orient=tk.VERTICAL, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)
    
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    try:
        with open(f'docker_gui_{datetime.now().strftime("%Y%m%d")}.log', 'r', encoding='utf-8') as f:
            log_text.insert(tk.END, f.read())
    except Exception as e:
        log_text.insert(tk.END, f"无法读取日志文件: {str(e)}")

def build_from_dockerfile(root, status_bar):
    """从Dockerfile构建镜像"""
    if not os.path.exists("Dockerfile"):
        messagebox.showerror("错误", "当前目录下不存在Dockerfile")
        return
        
    image_name = simpledialog.askstring("构建镜像", "请输入镜像名称:")
    if image_name:
        tag = simpledialog.askstring("构建镜像", "请输入标签(默认latest):", initialvalue="latest")
        if tag:
            status_bar.set_status("构建镜像", is_task=True)
            try:
                output = run_command(f"docker build -t {image_name}:{tag} .")
                if "错误" not in output:
                    messagebox.showinfo("成功", f"镜像 {image_name}:{tag} 构建成功")
                    status_bar.task_complete("构建镜像", success=True)
                else:
                    messagebox.showerror("错误", output)
                    status_bar.task_complete("构建镜像", success=False)
            except Exception as e:
                messagebox.showerror("错误", f"构建失败: {str(e)}")
                status_bar.task_complete("构建镜像", success=False)

def check_docker_installed():
    """检查是否安装了Docker"""
    try:
        output = subprocess.run(['docker', '--version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              encoding='utf-8')
        return output.returncode == 0
    except FileNotFoundError:
        return False

def show_docker_error():
    """显示Docker未安装错误"""
    messagebox.showerror(
        "错误",
        "未检测到Docker，请先安装Docker！\n" +
        "Windows安装教程：https://docs.docker.com/desktop/install/windows-install/\n" +
        "Linux安装教程：https://docs.docker.com/engine/install/"
    )

def push_selected_image(tree, status_bar):
    """推送选中的镜像"""
    if not check_docker_installed():
        show_docker_error()
        return
        
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要推送的镜像")
        return
    
    try:
        config = load_config()
        image_name = config['image_name']  # 从配置文件获取镜像名称
        
        # 获取标签
        tag = simpledialog.askstring("推送镜像", "请输入标签名称:", 
                                   initialvalue="latest")
        if not tag:
            return
            
        # 确认信息
        confirm_msg = f"""
请确认以下推送信息：

镜像名称: {image_name}
标签: {tag}
完整名称: {image_name}:{tag}

是否继续？
"""
        if not messagebox.askyesno("确认推送", confirm_msg):
            return
        
        # 执行推送
        status_bar.set_status("推送镜像", is_task=True)
        try:
            # 先尝试登录
            login_output = run_command("docker login")
            if "错误" in login_output:
                status_bar.task_complete("推送镜像", success=False)
                messagebox.showerror("错误", "Docker登录失败，请先登录")
                return
                
            output = run_command(f"docker push {image_name}:{tag}")
            if "错误" not in output:
                messagebox.showinfo("成功", f"镜像 {image_name}:{tag} 推送成功")
                status_bar.task_complete("推送镜像", success=True)
            else:
                messagebox.showerror("错误", output)
                status_bar.task_complete("推送镜像", success=False)
        except Exception as e:
            messagebox.showerror("错误", f"推送失败: {str(e)}")
            status_bar.task_complete("推送镜像", success=False)
            
    except Exception as e:
        messagebox.showerror("错误", f"操作失败: {str(e)}")

if __name__ == "__main__":
    args = parse_args()
    if args.cli:
        cli_mode(args)
    else:
        create_gui() 