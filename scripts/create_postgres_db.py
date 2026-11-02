import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="postgres", password="postgres", database="postgres", host="127.0.0.1", port=5432)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'smart_logistics'")
    if not exists:
        await conn.execute("CREATE DATABASE smart_logistics")
        print("Created database smart_logistics successfully!")
    else:
        print("Database smart_logistics already exists.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
