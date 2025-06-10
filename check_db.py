#!/usr/bin/env python3
import sys
import os

# 尝试导入所需模块
try:
    import psycopg2
    from datetime import datetime, date
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请安装所需模块: pip install psycopg2-binary")
    sys.exit(1)

def connect_to_database():
    """连接到PostgreSQL数据库"""
    try:
        conn = psycopg2.connect(
            host="dbprovider.ap-southeast-1.clawcloudrun.com",
            port=49674,
            database="postgres",
            user="postgres",
            password="sbdx497p",
            sslmode="prefer"
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def check_today_articles():
    """检查今天的论文"""
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 检查今天的日期
    today = date.today()
    print(f"检查日期: {today}")
    
    # 查询今天的论文
    cursor.execute("""
        SELECT id, title, date_processed, tags, arxiv_id
        FROM articles 
        WHERE date_processed = %s
        ORDER BY id DESC;
    """, (today,))
    
    articles = cursor.fetchall()
    
    print(f"找到 {len(articles)} 篇今天的论文:")
    print("-" * 100)
    
    for article in articles:
        id_num, title, date_proc, tags, arxiv_id = article
        print(f"ID: {id_num}")
        print(f"标题: {title}")
        print(f"日期: {date_proc}")
        print(f"标签: {tags}")
        print(f"ArXiv ID: {arxiv_id}")
        print("-" * 100)
    
    # 检查最近几天的论文
    cursor.execute("""
        SELECT date_processed, COUNT(*) 
        FROM articles 
        WHERE date_processed >= %s - INTERVAL '7 days'
        GROUP BY date_processed 
        ORDER BY date_processed DESC;
    """, (today,))
    
    recent_stats = cursor.fetchall()
    print("\n最近7天的论文统计:")
    for date_stat, count in recent_stats:
        print(f"{date_stat}: {count}篇")
    
    # 检查ID为92的论文
    cursor.execute("""
        SELECT id, title, date_processed, tags, arxiv_id, created_at
        FROM articles 
        WHERE id = 92;
    """)
    
    article_92 = cursor.fetchone()
    if article_92:
        print(f"\nID 92的论文详情:")
        print(f"ID: {article_92[0]}")
        print(f"标题: {article_92[1]}")
        print(f"处理日期: {article_92[2]}")
        print(f"标签: {article_92[3]}")
        print(f"ArXiv ID: {article_92[4]}")
        print(f"创建时间: {article_92[5]}")
    else:
        print("\n未找到ID为92的论文")
    
    # 搜索包含MemoryOS的论文
    cursor.execute("""
        SELECT id, title, date_processed, created_at
        FROM articles 
        WHERE title ILIKE '%Memory%' OR title ILIKE '%OS%'
        ORDER BY id DESC
        LIMIT 5;
    """)
    
    memory_articles = cursor.fetchall()
    print(f"\n搜索包含Memory或OS的论文:")
    for article in memory_articles:
        print(f"ID: {article[0]}, 标题: {article[1]}, 处理日期: {article[2]}, 创建时间: {article[3]}")
    
    # 检查最新的几篇论文
    cursor.execute("""
        SELECT id, title, date_processed, created_at
        FROM articles 
        ORDER BY id DESC
        LIMIT 5;
    """)
    
    latest_articles = cursor.fetchall()
    print(f"\n最新的5篇论文:")
    for article in latest_articles:
        print(f"ID: {article[0]}, 标题: {article[1]}, 处理日期: {article[2]}, 创建时间: {article[3]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_today_articles() 