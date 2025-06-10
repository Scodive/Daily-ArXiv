#!/usr/bin/env python3
"""
定时任务设置脚本
用于配置每日自动论文处理的cron任务

使用方法：
python setup_cron.py
"""

import os
import sys
import subprocess
from datetime import datetime

def get_python_path():
    """获取当前Python解释器路径"""
    return sys.executable

def get_script_dir():
    """获取脚本所在目录的绝对路径"""
    return os.path.dirname(os.path.abspath(__file__))

def create_run_script():
    """创建运行脚本"""
    script_dir = get_script_dir()
    python_path = get_python_path()
    
    run_script_content = f"""#!/bin/bash
# 每日ArXiv论文自动处理脚本
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 设置工作目录
cd "{script_dir}"

# 激活环境并运行脚本
export PYTHONPATH="{script_dir}:$PYTHONPATH"
{python_path} daily_auto.py --count 5 --categories cs.AI cs.CV cs.CL cs.LG --fallback-days 3 >> daily_auto.log 2>&1

echo "论文处理完成于: $(date)" >> daily_auto.log
"""
    
    run_script_path = os.path.join(script_dir, "run_daily_auto.sh")
    
    try:
        with open(run_script_path, "w", encoding="utf-8") as f:
            f.write(run_script_content)
        
        # 设置执行权限
        os.chmod(run_script_path, 0o755)
        
        print(f"✅ 运行脚本已创建: {run_script_path}")
        return run_script_path
        
    except Exception as e:
        print(f"❌ 创建运行脚本失败: {e}")
        return None

def show_cron_instructions(run_script_path):
    """显示cron设置说明"""
    print("\n📋 定时任务设置说明:")
    print("=" * 50)
    
    print("\n1. 编辑crontab:")
    print("   crontab -e")
    
    print("\n2. 添加以下行到crontab文件中:")
    
    # 每天上午9点运行
    print(f"   # 每天上午9点自动处理ArXiv论文")
    print(f"   0 9 * * * {run_script_path}")
    
    print("\n3. 保存并退出编辑器")
    
    print("\n4. 验证crontab设置:")
    print("   crontab -l")
    
    print("\n📝 其他常用时间设置:")
    print("   0 6 * * *   # 每天早上6点")
    print("   0 9 * * *   # 每天上午9点")
    print("   0 18 * * *  # 每天下午6点")
    print("   0 9 * * 1-5 # 工作日上午9点")
    
    print("\n📊 日志文件位置:")
    log_path = os.path.join(os.path.dirname(run_script_path), "daily_auto.log")
    print(f"   {log_path}")
    
    print("\n💡 测试运行:")
    print(f"   {run_script_path}")

def setup_log_rotation():
    """设置日志轮转"""
    script_dir = get_script_dir()
    logrotate_content = f"""{script_dir}/daily_auto.log {{
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 {os.getenv('USER', 'user')} {os.getenv('USER', 'user')}
}}"""
    
    logrotate_config_path = os.path.join(script_dir, "daily_auto_logrotate")
    
    try:
        with open(logrotate_config_path, "w", encoding="utf-8") as f:
            f.write(logrotate_content)
        
        print(f"✅ 日志轮转配置已创建: {logrotate_config_path}")
        print("\n📋 设置日志轮转 (可选):")
        print(f"   sudo cp {logrotate_config_path} /etc/logrotate.d/daily_auto")
        
    except Exception as e:
        print(f"⚠️  创建日志轮转配置失败: {e}")

def create_status_script():
    """创建状态检查脚本"""
    script_dir = get_script_dir()
    python_path = get_python_path()
    
    status_script_content = f"""#!/usr/bin/env python3
import os
import sys
sys.path.append('{script_dir}')

from check_db import check_today_articles
from datetime import datetime

print(f"📊 Daily ArXiv 状态检查 - {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
print("=" * 60)

# 检查数据库中今天的论文
check_today_articles()

# 检查日志文件
log_file = os.path.join('{script_dir}', 'daily_auto.log')
if os.path.exists(log_file):
    print(f"\\n📄 最新日志 (最后10行):")
    print("-" * 40)
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(line.rstrip())
    except Exception as e:
        print(f"读取日志失败: {{e}}")
else:
    print("\\n⚠️  未找到日志文件")
"""
    
    status_script_path = os.path.join(script_dir, "check_status.py")
    
    try:
        with open(status_script_path, "w", encoding="utf-8") as f:
            f.write(status_script_content)
        
        os.chmod(status_script_path, 0o755)
        
        print(f"✅ 状态检查脚本已创建: {status_script_path}")
        print(f"💡 运行方式: python {status_script_path}")
        
    except Exception as e:
        print(f"⚠️  创建状态检查脚本失败: {e}")

def main():
    print("🔧 Daily ArXiv 定时任务设置工具")
    print("=" * 50)
    
    script_dir = get_script_dir()
    python_path = get_python_path()
    
    print(f"📂 脚本目录: {script_dir}")
    print(f"🐍 Python路径: {python_path}")
    
    # 检查必要文件
    required_files = ["daily_auto.py", "arxiv.py", "check_db.py"]
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(script_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return
    
    print("✅ 所有必要文件都存在")
    
    # 创建运行脚本
    run_script_path = create_run_script()
    if not run_script_path:
        return
    
    # 创建状态检查脚本
    create_status_script()
    
    # 设置日志轮转
    setup_log_rotation()
    
    # 显示设置说明
    show_cron_instructions(run_script_path)
    
    print("\n🎉 设置完成!")
    print("\n📝 下一步:")
    print("1. 按照上面的说明设置crontab")
    print("2. 等待定时任务执行")
    print("3. 使用 python check_status.py 检查状态")

if __name__ == "__main__":
    main() 