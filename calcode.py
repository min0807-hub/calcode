import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
import os

# 데이터베이스 연결 및 테이블 생성
conn = sqlite3.connect('sales.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        item TEXT,
        price_in_won INTEGER,
        price_in_usd REAL
    )
''')
conn.commit()

# 봇 초기화
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def 원화판매(ctx, date: str, *items_and_price: str):
    """원화 판매 내역 추가 (물건 목록과 총 판매액)"""
    if len(items_and_price) < 2:
        await ctx.send("물건 목록과 총 판매액을 입력해야 합니다.")
        return

    try:
        datetime.strptime(date, '%Y-%m-%d')  # 날짜 형식 검증
        total_price = int(items_and_price[-1])  # 마지막 요소를 총 판매액으로 설정

        if total_price <= 0:
            await ctx.send("총 판매액은 0보다 커야 합니다.")
            return
    except ValueError:
        await ctx.send("날짜 형식은 YYYY-MM-DD여야 하며, 총 판매액은 숫자여야 합니다.")
        return

    items = " ".join(items_and_price[:-1])  # 모든 물건 이름을 하나의 문자열로 합침

    # 원화 가격 저장
    c.execute('INSERT INTO sales (date, item, price_in_won, price_in_usd) VALUES (?, ?, ?, ?)', 
              (date, items.strip(), total_price, None))  # 총 가격 저장
    conn.commit()
    await ctx.send(f"{date}에 {items} - 총 {total_price}원으로 추가되었습니다.")

@bot.command()
async def 달러판매(ctx, date: str, *items_and_price: str):
    """달러 판매 내역 추가 (물건 목록과 총 판매액)"""
    if len(items_and_price) < 2:
        await ctx.send("물건 목록과 총 판매액을 입력해야 합니다.")
        return

    try:
        datetime.strptime(date, '%Y-%m-%d')  # 날짜 형식 검증
        total_price = float(items_and_price[-1])  # 마지막 요소를 총 판매액으로 설정

        if total_price <= 0:
            await ctx.send("총 판매액은 0보다 커야 합니다.")
            return
    except ValueError:
        await ctx.send("날짜 형식은 YYYY-MM-DD여야 하며, 총 판매액은 숫자여야 합니다.")
        return

    items = " ".join(items_and_price[:-1])  # 모든 물건 이름을 하나의 문자열로 합침

    # 달러 가격 저장
    c.execute('INSERT INTO sales (date, item, price_in_won, price_in_usd) VALUES (?, ?, ?, ?)', 
              (date, items.strip(), None, total_price))  # 총 가격 저장
    conn.commit()
    await ctx.send(f"{date}에 {items} - 총 {total_price:.2f}달러로 추가되었습니다.")
    
@bot.command()
async def 총매출(ctx):
    """총 매출 및 판매 내역 출력"""
    # 원화 매출 합계
    c.execute('SELECT SUM(price_in_won) FROM sales WHERE price_in_won IS NOT NULL')
    total_sales_won = c.fetchone()[0]
    total_sales_won = total_sales_won if total_sales_won is not None else 0

    # 달러 매출 합계
    c.execute('SELECT SUM(price_in_usd) FROM sales WHERE price_in_usd IS NOT NULL')
    total_sales_usd = c.fetchone()[0]
    total_sales_usd = total_sales_usd if total_sales_usd is not None else 0

    await ctx.send(f"총 매출: {total_sales_won}원, {total_sales_usd:.2f}달러")
    
@bot.command()
async def 삭제(ctx, date: str, *items_and_price: str):
    """특정 날짜의 판매 내역 삭제"""
    if len(items_and_price) < 2:
        await ctx.send("삭제할 물건 목록과 가격을 입력해야 합니다. 사용법: !삭제 <날짜> <물건1> <물건2> ... <가격>")
        return

    total_price = items_and_price[-1]  # 마지막 요소를 총 판매액으로 설정
    items = items_and_price[:-1]  # 나머지 요소를 물건 목록으로 설정

    # 입력된 가격이 숫자인지 확인
    try:
        total_price = float(total_price)  # 가격을 실수로 변환 (정수와 실수 모두 처리)
    except ValueError:
        await ctx.send("가격은 숫자로 입력해야 합니다.")
        return

    # 해당 조건에 맞는 레코드가 존재하는지 확인
    item_placeholders = ', '.join('?' for _ in items)
    c.execute(f'SELECT * FROM sales WHERE date = ? AND item = ? AND price_in_won = ?', (date, ' '.join(items), total_price))
    record = c.fetchone()

    if record is None:
        await ctx.send("삭제할 판매 내역이 없습니다. 날짜 또는 물건 이름이 일치하지 않습니다.")
        return

    # 모든 조건이 일치하는 경우 삭제
    c.execute(f'DELETE FROM sales WHERE date = ? AND item = ? AND price_in_won = ?', (date, ' '.join(items), total_price))
    conn.commit()
    await ctx.send(f"{date}에 있는 {', '.join(items)} - 총 {total_price}원이 삭제되었습니다.")
    
@bot.command()
async def 초기화(ctx):
    """모든 판매 내역 초기화"""
    c.execute('DELETE FROM sales')  # 모든 판매 내역 삭제
    conn.commit()
    await ctx.send("모든 판매 내역이 초기화되었습니다.")

@bot.command()
async def 데이터(ctx):
    """저장된 모든 판매 내역 출력"""
    c.execute('SELECT * FROM sales')
    sales_records = c.fetchall()
    
    if sales_records:
        sales_summary = []
        for record in sales_records:
            sales_summary.append(f"날짜: {record[1]}, 물건: {record[2]}, 원화: {record[3]}, 달러: {record[4]}")
        
        await ctx.send("\n".join(sales_summary))
    else:
        await ctx.send("저장된 판매 내역이 없습니다.")

@bot.command()
async def 월별매출(ctx, year: int, month: int):
    """특정 월의 총 매출 출력"""
    if month < 1 or month > 12:
        await ctx.send("월은 1부터 12 사이여야 합니다.")
        return

    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"  # 다음 해 1월 1일
    else:
        end_date = f"{year}-{month + 1:02d}-01"  # 다음 월의 1일

    # 원화 매출 합계
    c.execute('SELECT SUM(price_in_won) FROM sales WHERE date >= ? AND date < ? AND price_in_won IS NOT NULL', (start_date, end_date))
    total_sales_won = c.fetchone()[0]
    total_sales_won = total_sales_won if total_sales_won is not None else 0

    # 달러 매출 합계
    c.execute('SELECT SUM(price_in_usd) FROM sales WHERE date >= ? AND date < ? AND price_in_usd IS NOT NULL', (start_date, end_date))
    total_sales_usd = c.fetchone()[0]
    total_sales_usd = total_sales_usd if total_sales_usd is not None else 0

    await ctx.send(f"{year}년 {month}월 총 매출: {total_sales_won}원, {total_sales_usd:.2f}달러")

# 봇 실행
@bot.event
async def on_ready():
    print(f'{bot.user.name}이(가) 준비되었습니다.')
    
access_token = os.environ["BOT_TOKEN"]
bot.run(access_token)

