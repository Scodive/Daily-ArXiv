#!/usr/bin/env python3
"""
简单的数据库连接测试脚本
"""

import psycopg2

def test_database_connection():
    """测试数据库连接"""
    try:
        conn = psycopg2.connect(
            host="dbprovider.ap-southeast-1.clawcloudrun.com",
            port=49674,
            database="postgres",
            user="postgres",
            password="sbdx497p",
            sslmode="prefer"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles;")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ 数据库连接成功！当前有 {count} 篇文章")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    test_database_connection() 