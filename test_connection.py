import psycopg2

def test_connection():
    """测试数据库连接"""
    connection_params = [
        # 原始参数
        {
            "host": "dbprovider.ap-southeast-1.clawcloudrun.com",
            "port": 49674,
            "database": "postgres",
            "user": "postgres",
            "password": "49674"
        },
        # 带SSL的参数
        {
            "host": "dbprovider.ap-southeast-1.clawcloudrun.com",
            "port": 49674,
            "database": "postgres",
            "user": "postgres",
            "password": "49674",
            "sslmode": "require"
        },
        # 不带SSL的参数
        {
            "host": "dbprovider.ap-southeast-1.clawcloudrun.com",
            "port": 49674,
            "database": "postgres",
            "user": "postgres",
            "password": "49674",
            "sslmode": "disable"
        }
    ]
    
    for i, params in enumerate(connection_params, 1):
        print(f"\n尝试连接方式 {i}:")
        print(f"参数: {params}")
        try:
            conn = psycopg2.connect(**params)
            print("✅ 连接成功！")
            
            # 测试一个简单查询
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"数据库版本: {version}")
            
            cursor.close()
            conn.close()
            return params
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            continue
    
    print("\n所有连接方式都失败了，请检查连接信息是否正确。")
    return None

if __name__ == "__main__":
    test_connection() 