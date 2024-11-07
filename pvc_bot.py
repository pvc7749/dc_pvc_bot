import sys
sys.path.append(r'C:\DC_BOT')  # 添加該目錄到模組搜索路徑
from responses123 import responses, responses2, responses3, responses4

import discord
from discord.ext import tasks, commands
import asyncio  # 確保導入 asyncio
import random
import sqlite3
import time


# 啟用所需的 intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)  # Initialize the bot instance

TOKEN = '123'  # 在這裡放入你的 Bot Token

# 連接到SQLite資料庫
conn = sqlite3.connect("points.db")
c = conn.cursor()

# 建立分數儲存表
c.execute("""
CREATE TABLE IF NOT EXISTS user_points (
    user_id INTEGER PRIMARY KEY,
    points INTEGER
)
""")
conn.commit()

# 建立用戶防B狀態表
# 刪除並重新創建 user_defense 表格
c.execute("DROP TABLE IF EXISTS user_defense")
c.execute("""
CREATE TABLE user_defense (
    user_id INTEGER PRIMARY KEY,
    has_defense INTEGER DEFAULT 0,
    rounds_left INTEGER DEFAULT 0
)
""")
conn.commit()

# 建立卡片儲存表
c.execute("""
CREATE TABLE IF NOT EXISTS user_cards (
    user_id INTEGER,
    card_id INTEGER,
    card_name TEXT,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, card_id)
)
""")
conn.commit()

# 定義10種卡片
# 定義10種卡片，附帶使用說明
cards = [
    {"card_id": 1, "card_name": "點數卡", "description": "使用此卡可以獲得100萬點數。"},
    {"card_id": 2, "card_name": "天使卡", "description": "使用後可免疫一次大搶奪或奴役。"},
    {"card_id": 3, "card_name": "地雷卡", "description": "有人想搶或奴役你時，有機率爆炸，將點數全部給你。"},
    {"card_id": 4, "card_name": "出獄卡", "description": "重置所有冷卻時間，並解除被奴役狀態。"},
    {"card_id": 5, "card_name": "均富卡", "description": "N/A。"},
    {"card_id": 6, "card_name": "光明卡", "description": "N/A。"},
    {"card_id": 7, "card_name": "黑暗卡", "description": "N/A。"},
    {"card_id": 8, "card_name": "怪獸卡", "description": "N/A。"},
    {"card_id": 9, "card_name": "請神卡", "description": "N/A。"},
    {"card_id": 10, "card_name": "復仇卡", "description": "N/A。"}
]

# 定義每張卡片的抽取機率，數量與 cards 列表長度一致
probabilities_card = [0.3, 0.3, 0.1, 0.1, 0.03, 0.07, 0.06, 0.02, 0.01, 0.01]  # 機率總和應為1



# 定義八個裝備部位及其所屬屬性類型
equipment_slots = [
    {"equipment_name": "頭盔"},
    {"equipment_name": "手套"},
    {"equipment_name": "胸甲"},
    {"equipment_name": "腿甲"},
    {"equipment_name": "褲襠甲"},
    {"equipment_name": "鞋子"},
    {"equipment_name": "武器"},
    {"equipment_name": "盾牌"}
]

# 定義裝備部位及其所屬屬性類型
equipment_attributes = {
    "頭盔": ["health", "mana", "stamina"],  # 頭盔屬性：生命、魔力、精力
    "手套": ["mana", "stamina", "speed"],  # 手套屬性：魔力、精力、速度
    "褲襠甲": ["stamina", "speed", "health"],  # 褲襠甲屬性：精力、速度、生命
    "胸甲": ["defense", "health", "mana"],  # 胸甲屬性：防禦、生命、魔力
    "腿甲": ["magic_defense", "defense", "stamina"],  # 腿甲屬性：魔防、防禦、精力
    "鞋子": ["speed", "mana", "health"],  # 鞋子屬性：速度、魔力、生命
    "武器": ["attack", "magic_attack", "speed"],  # 武器屬性：攻擊、魔攻、速度
    "盾牌": ["health", "defense", "magic_defense"]  # 盾牌屬性：生命、防禦、魔防
}

# 定義稀有度等級及其對應的屬性範圍
rarity_levels = [
    {"rarity": "N", "min_attr": 1, "max_attr": 50},
    {"rarity": "H", "min_attr": 11, "max_attr": 50},
    {"rarity": "R", "min_attr": 21, "max_attr": 60},
    {"rarity": "SR", "min_attr": 31, "max_attr": 60},
    {"rarity": "SSR", "min_attr": 41, "max_attr": 70},
    {"rarity": "UR", "min_attr": 41, "max_attr": 80},
    {"rarity": "MR", "min_attr": 51, "max_attr": 90},
    {"rarity": "BR", "min_attr": 51, "max_attr": 100}
]


# 設置每種稀有度的機率
rarity_probabilities = [0.4, 0.2, 0.15, 0.1, 0.08, 0.05, 0.015, 0.005]

# 強化成功機率基礎值 (依稀有度)
enhance_success_rates = {
    "N": 0.8,
    "H": 0.75,
    "R": 0.7,
    "SR": 0.65,
    "SSR": 0.6,
    "UR": 0.55,
    "MR": 0.5,
    "BR": 0.45
}

# 強化點數倍率 (依稀有度)
enhance_cost_rates = {
    "N": 1,
    "H": 1.1,
    "R": 1.15,
    "SR": 1.2,
    "SSR": 1.25,
    "UR": 1.3,
    "MR": 1.35,
    "BR": 1.4
}

# 建立裝備儲存表，包含屬性及唯一的 equipment_id
c.execute("""
CREATE TABLE IF NOT EXISTS user_equipment (
    user_id INTEGER,
    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_name TEXT,
    rarity TEXT,
    upgrade INTEGER DEFAULT 0,
    health INTEGER DEFAULT 0,
    mana INTEGER DEFAULT 0,
    stamina INTEGER DEFAULT 0,
    attack INTEGER DEFAULT 0,
    magic_attack INTEGER DEFAULT 0,
    defense INTEGER DEFAULT 0,
    magic_defense INTEGER DEFAULT 0,
    speed INTEGER DEFAULT 0
)
""")
conn.commit()



# 定義抽卡的機率
probabilities = [75, 10, 8, 3, 3, 1]

# 定義抽卡 responses5 內容
responses5 = [
    ":ding_LUL:1252130402022461521",      
    ":ding_king:1249917816874729503",     
    ":ding_rainbow:1276103293625696336",   
    ":ding_sleep3:1293138547863453787",
    ":goeat:1249905469850386452",      
    ":ding_ugly:1299289119989563465"    
]

# 特定貼圖對應的積分
bonus_points = {
    "ding_LUL": 0,
    "ding_king": 1,
    "ding_rainbow": 2,
    "ding_sleep3": 5,
    "goeat": 8,
    "ding_ugly": 100
}


# 定義抽卡的機率
probabilities2 = [85, 2, 8, 3, 2]

# 定義抽卡 responses5 內容
responses6 = [
    ":ding_cool:1252130666951217193",      
    ":banyou:1249908230927159306",     
    ":ding_eat4:1293129657717100606",   
    ":neck_pinching:1250632821563850814",      
    ":j_ding_huaiyun:1250336845431177337"    
]

# 特定貼圖對應的積分
bonus_points2 = {
    "ding_cool": 0,
    "banyou": -1,
    "ding_eat4": 20,
    "neck_pinching": 80,
    "j_ding_huaiyun": 100
}

# 定義賭博的機率和對應的點數變化
gamble_outcomes = {
    "lose_all": -1,
    "lose_10": -0.1,
    "lose_20": -0.2,
    "lose_90": -0.9,
    "gain_10": 0.1,
    "gain_50": 0.5,
    "gain_100": 1.0,
    "gain_900": 9.0,
}

gamble_probabilities = [1, 30, 15, 6, 35, 8, 3, 2]  # 對應賭博結果的機率（總和應該為100）

# 创建一个字典来存储冷却状态
cooldowns = {}
cooldowns_rob = {}
cooldowns_slave = {}
# 初始化奴隸狀態紀錄
slave_status = {}

# 天使卡狀態
angel_immunity = {}
# 地雷卡狀態
landmine_status = {}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # 防止 bot 自己回應自己的消息

    user_id = message.author.id

    # 檢查冷卻時間
    if user_id in cooldowns and time.time() - cooldowns[user_id] <= 0:
        return

    # 设置冷却时间2秒
    cooldowns[user_id] = time.time() + 1

    # 檢查訊息內容中的關鍵字並累加積分
    if message.author != bot.user:
        user_id = message.author.id
        word_count = len(message.content)
        points_to_add = word_count ** 10

    # 若有新增積分，則更新資料庫
    if points_to_add > 0:

        if points_to_add > 10:
            points_to_add = 10

        c.execute("INSERT OR IGNORE INTO user_points (user_id, points) VALUES (?, ?)", (user_id, 0))
        c.execute("UPDATE user_points SET points = points + ? WHERE user_id = ?", (points_to_add, user_id))
        conn.commit()


    # 檢查是否是奴隸狀態
    if message.content.startswith("!") and user_id in slave_status:
        slave_info = slave_status[user_id]
        
        if time.time() < slave_info['end_time']:  # 若在禁用時間內
            owner_id = slave_info['owner_id']
            owner_user = await bot.fetch_user(owner_id)  # 獲取奴隸主的用戶對象
            
            # 檢查是否使用 "!工作" 指令
            if message.content == "!工作":
                # 縮短60%奴役時間
                remaining_time = slave_info['end_time'] - time.time()
                new_end_time = time.time() + remaining_time * 0.4
                slave_info['end_time'] = new_end_time  # 更新奴役結束時間
                
                # 給奴隸主調整點數
                point_change_percentage = random.uniform(-0.2, 0.3)  # -10%到30%的變動
                c.execute("SELECT points FROM user_points WHERE user_id = ?", (owner_id,))
                owner_points = c.fetchone()[0]
                new_owner_points = int(owner_points * (1 + point_change_percentage))
                
                # 更新奴隸主點數
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_owner_points, owner_id))
                conn.commit()
                
                # 顯示調整結果訊息
                adjustment_text = f"增加了 {int(point_change_percentage * 100)}%" if point_change_percentage >= 0 else f"減少了 {int(abs(point_change_percentage) * 100)}%"
                await message.channel.send(
                    f"{message.author.mention} 你成功減少了60%的奴役時間！\n"
                    f"{owner_user.display_name} 的點數{adjustment_text}。\n"
                    f"剩餘奴役時間：{int((new_end_time - time.time()) // 60)} 分 {int((new_end_time - time.time()) % 60)} 秒。"
                )
                return  # 中止執行其他指令

            else:
                # 顯示剩餘時間，阻止其他指令
                remaining_time = slave_info['end_time'] - time.time()
                minutes, seconds = divmod(int(remaining_time), 60)
                await message.channel.send(
                    f"{message.author.mention} 你是 {owner_user.display_name} 的奴隸，只可以 !工作 減少奴隸時數！\n"
                    f"剩餘時間：{minutes} 分 {seconds} 秒。\n"
                    "https://media1.tenor.com/m/a1ujsEsEDJoAAAAd/bricosplay-missbricosplay.gif"
                )
                return  # 阻止執行其他指令
        else:
            # 奴役時間結束，移除奴隸狀態
            del slave_status[user_id]


    if message.content == "!指令":
        response0 = (
            "` \n!查詢 : 查詢剩餘點數\n"
            "!排行榜 : 查詢點數排名。 !第一 : 可以顯示第一名ID讓手機複製\n"
            "!搶 <user_id> : user_id請用排行榜查詢 (未輸入則是搶第一名)，冷卻1分鐘，可能搶劫成功(搶10%)、失敗(吐10%，歸0則入獄3分鐘)、大成功(搶100%)或關進監獄(失去99%並被600) \n"
            "!奴役 <user_id> : user_id請用排行榜查詢，成功則奴役對方100分鐘，被奴役者無法行動，但可以 !工作 幫奴隸主做事減少時間 \n"
            "!射阿丁 : 消耗5%點數，發牌1~100，開始後輸入 !猜中 <下注金額> 或 !猜不中 <下注金額> 繼續\n"
            "!猜中 <下注金額> : 門越小倍率越高 (x1.5~x5) \n"
            "!猜不中 <下注金額> : 門越大倍率越高 (x1.5~x5) \n"
            "!卡池 : 顯示卡池與點數\n"
            "!抽卡 : 點數大於100萬時，消耗99%可抽得道具卡一張\n"
            "!抽限定 : 抽限定卡池，抽到BAN會-50%點數。 可使用 !五連抽 一次抽五次\n"
            "!防B : 消耗10%點數，5回合內抽到BAN時只會扣10%\n"
            "!乞丐 : 點數不足100時給予200點\n"
            "!賭博 : 點數有機率 -10%, -20%, -90%, -100%, +10%, +50%, +100%, +300%。 可使用 !八堵 一次賭八次\n"
            "!吃啥 : 抽食物\n"
            "!今日 : 今日運勢\n"
            "!PUA, !Labrat, !誰最可愛`"
        )
        await message.channel.send(response0)


    # 處理 !搶 指令
    if message.content.startswith("!搶"):
        parts = message.content.split(" ")

        # 確認用戶輸入了 user_id
        if len(parts) < 2:
            # 查詢擁有最高積分的玩家
            c.execute("SELECT user_id FROM user_points ORDER BY points DESC LIMIT 1")
            highest_user = c.fetchone()

            if highest_user:
                target_user_id = highest_user[0]
            else:
                await message.channel.send("目前沒有玩家的點數紀錄。")
                return
        else:
            target_user_id = parts[1]


        # 檢查冷卻時間
        if user_id in cooldowns_rob:
            elapsed_time = cooldowns_rob[user_id] - time.time()
            if elapsed_time > 0:
                await message.channel.send(f"{message.author.mention} 請稍候 {int(elapsed_time)} 秒後再試。")
                return

        # 設置冷卻時間
        cooldowns_rob[user_id] = time.time() + 60

        # 檢查目標用戶是否為有效的 user_id
        try:
            target_user_id = int(target_user_id)  # 嘗試將 user_id 轉換為整數
        except ValueError:
            await message.channel.send("無效的 user_id，請輸入數字形式的 user_id。")
            return

        # 檢查是否是自我奴役
        if target_user_id == user_id:
            await message.channel.send(f"{message.author.mention} 無法搶自己。")
            return

        target_user = await bot.fetch_user(target_user_id)

        # 檢查使用者和目標的點數
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        user_points = c.fetchone()
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (target_user_id,))
        target_points = c.fetchone()

        if not user_points or not target_points:
            await message.channel.send("無法找到指定使用者的點數記錄。")
            return


        user_points = user_points[0]
        target_points = target_points[0]
        chance = random.randint(1, 100)  # 產生1到100的隨機數決定搶劫結果

        # 檢查目標用戶是否有地雷卡
        if target_user_id in landmine_status:
            # 隨機決定地雷卡是否爆炸
            explosion_chance = random.random()  # 隨機數在 [0, 1)
            if explosion_chance < 0.25:  # 假設有25%的爆炸機率
                # 將搶奪者的所有點數轉移給被搶奪者
                c.execute("UPDATE user_points SET points = points + ? WHERE user_id = ?", (user_points, target_user_id))
                c.execute("UPDATE user_points SET points = 0 WHERE user_id = ?", (user_id,))
                conn.commit()
                    
                # 重置地雷卡狀態
                del landmine_status[target_user_id]
                await message.channel.send(f"{message.author.mention} 嘗試搶奪 {target_user.display_name} 時，地雷卡爆炸了！你的全部 {user_points} 點數被轉移到 {target_user.display_name} 那裡！")
                return

        if chance <= 40:
            # 成功，取得對方10%點數
            stolen_points = int(target_points * 0.1)
            new_user_points = user_points + stolen_points
            new_target_points = target_points - stolen_points
            custom_emoji = discord.utils.get(message.guild.emojis, name='ding_eat4')
            if custom_emoji:
                await message.add_reaction(custom_emoji)  # 添加自定義表情符號
            await message.channel.send(
                f"{message.author.mention} 成功搶劫了 {target_user.display_name}，獲得了 {stolen_points} 點數！"
            )

            # 更新點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
            conn.commit()

        elif chance <= 80:
            # 失敗，將對方10%點數給對方
            lost_points = min(int(target_points * 0.1), user_points)
            new_user_points = user_points - lost_points
            new_target_points = target_points + lost_points
            custom_emoji = discord.utils.get(message.guild.emojis, name='ding_think')
            if custom_emoji:
                await message.add_reaction(custom_emoji)  # 添加自定義表情符號
            if new_user_points <= 0:
                # 玩家點數歸零，進入監獄 3 分鐘
                cooldowns_rob[user_id] = time.time() + 180  # 設置監獄冷卻時間為 3 分鐘
                await message.channel.send(
                    f"{message.author.mention} 搶劫失敗，失去 {lost_points} 點數給 {target_user.display_name}！\n"
                    f"你的點數歸零，被逮捕進入監獄 3 分鐘！"
                )
            else:
                await message.channel.send(
                    f"{message.author.mention} 搶劫失敗，失去 {lost_points} 點數給 {target_user.display_name}！"
                )

            # 更新點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
            conn.commit()

        elif chance <= 90:
            # 被逮捕，10分鐘內無法搶劫

            if user_id in angel_immunity:
                await message.channel.send(f"{message.author.mention} 你消耗天使卡免疫，不會被逮捕！")
                del angel_immunity[user_id]
                return


            cooldowns_rob[user_id] = time.time() + 600  # 設置10分鐘冷卻
            custom_emoji = discord.utils.get(message.guild.emojis, name='banyou')
            if custom_emoji:
                await message.add_reaction(custom_emoji)  # 添加自定義表情符號

            # 被逮捕，失去99%的點數
            stolen_points = int(user_points * 0.99)
            new_user_points = user_points - stolen_points
            new_target_points = target_points + stolen_points // 2

            # 更新用戶的點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
            conn.commit()  # 提交更改

            # 獲取所有用戶的ID
            c.execute("SELECT user_id FROM user_points")
            all_users = c.fetchall()
            num_users = len(all_users)

            # 平分給所有用戶
            if num_users > 0:
                split_points = stolen_points // 2 // num_users
                for user in all_users:
                    member_id = user[0]
                    if member_id != user_id:  # 不給自己
                        # 獲取成員的當前點數
                        c.execute("SELECT points FROM user_points WHERE user_id = ?", (member_id,))
                        member_points = c.fetchone()
                        if member_points:
                            new_member_points = member_points[0] + split_points
                            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_member_points, member_id))


            await message.channel.send(
                f"{message.author.mention} 被逮捕了！失去了 {stolen_points} 點數，並將其平分給所有用戶！ \n 在10分鐘內無法進行搶劫。"
            )

            # 更新點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
            conn.commit()

        else:
            # 大成功，取得對方99%的點數

            if target_user_id in angel_immunity:
                await message.channel.send(f"{message.author.mention} 消耗 {target_user.display_name} 的天使卡免疫，大搶奪失敗！")
                del angel_immunity[target_user_id]
                return


            stolen_points = target_points // 2
            new_user_points = user_points + stolen_points
            new_target_points = 0

            # 獲取所有用戶的ID
            c.execute("SELECT user_id FROM user_points")
            all_users = c.fetchall()
            num_users = len(all_users)

            custom_emoji = discord.utils.get(message.guild.emojis, name='ding_king')
            if custom_emoji:
                await message.add_reaction(custom_emoji)  # 添加自定義表情符號

            # 平分給所有用戶
            if num_users > 0:
                split_points = stolen_points // num_users
                for user in all_users:
                    member_id = user[0]
                    if member_id != target_user_id:  # 不給對方
                        # 獲取成員的當前點數
                        c.execute("SELECT points FROM user_points WHERE user_id = ?", (member_id,))
                        member_points = c.fetchone()
                        if member_points:
                            new_member_points = member_points[0] + split_points
                            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_member_points, member_id))


            await message.channel.send(
                f"{message.author.mention} 大成功！從 {target_user.display_name} 搶得了 {stolen_points} 點數，並將其平分給群組內所有成員！"
            )

            # 更新點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
            conn.commit()


    if message.content == "!查詢":
        user_id = message.author.id
    
        # 查詢積分
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        points_result = c.fetchone()

        if points_result:
            points = points_result[0]
            formatted_points = f"{points:,}"  # 將點數格式化為帶逗號的字符串
            response_message = f"{message.author.mention} 你目前有 {formatted_points} 積分！\n"
        else:
            response_message = f"{message.author.mention} 你目前沒有積分。\n"

        # 查詢卡片種類和數量
        c.execute("SELECT card_name, quantity FROM user_cards WHERE user_id = ?", (user_id,))
        cards_result = c.fetchall()

        if cards_result:
            response_message += "你擁有的卡片種類和數量如下：\n"
            for card_name, quantity in cards_result:
                response_message += f"- {card_name}: {quantity} 張\n"
        else:
            response_message += "你目前沒有卡片。\n"

        # 查詢天使卡保護狀態
        if user_id in angel_immunity:
            response_message += f"\n你目前受到天使卡的保護！"

        # 查詢天使卡保護狀態
        if user_id in landmine_status:
            response_message += f"\n你目前有啟用地雷卡！"

        await message.channel.send(response_message)


    if message.content.startswith("!奴役"):
        try:

            # 解析目標ID
            target_id_str = message.content.split(" ")

            # 確認用戶輸入了user_id
            if len(target_id_str) < 2:
                await message.channel.send("請在指令後提供有效的 user_id，例如：`!搶 <user_id>`。")
                return

            target_user_id = target_id_str[1]
            target_user_id = int(target_user_id)  # 嘗試將 user_id 轉換為整數
            target_user = await bot.fetch_user(target_user_id)

            # 檢查冷卻時間
            if user_id in cooldowns_slave and time.time() - cooldowns_slave[user_id] <= 0:
                remaining_time = int(-(time.time() - cooldowns_slave[user_id]))
                await message.channel.send(f"{message.author.mention} 請稍候 {remaining_time} 秒後再試。")
                return

            # 檢查是否是自我奴役
            if target_user_id == user_id:
                await message.channel.send(f"{message.author.mention} 無法自我奴役。")
                return

            # 獲取玩家和目標的點數
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            user_points = c.fetchone()[0]
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (target_user_id,))
            target_points = c.fetchone()[0]



            if user_points < 10000:
                await message.channel.send(f"{message.author.mention} 你至少需要 10,000 點數才能使用此指令！")
                return


            # 檢查目標用戶是否有地雷卡
            if target_user_id in landmine_status:
                # 隨機決定地雷卡是否爆炸
                explosion_chance = random.random()  # 隨機數在 [0, 1)
                if explosion_chance < 0.25:  # 假設有25%的爆炸機率
                    # 將搶奪者的所有點數轉移給被搶奪者
                    c.execute("UPDATE user_points SET points = points + ? WHERE user_id = ?", (user_points, target_user_id))
                    c.execute("UPDATE user_points SET points = 0 WHERE user_id = ?", (user_id,))
                    conn.commit()
                    
                    # 重置地雷卡狀態
                    del landmine_status[target_user_id]
                    await message.channel.send(f"{message.author.mention} 嘗試奴役 {target_user.display_name} 時，地雷卡爆炸了！你的全部 {user_points} 點數被轉移到 {target_user.display_name} 那裡！")
                    return


            # 奴役機率
            chance = random.randint(1, 100)

            if chance <= 75:
                # 奴役失敗
                cost_points = int(user_points * 0.2)
                new_user_points = user_points - cost_points
                new_target_points = target_points + cost_points
                await message.channel.send(
                    f"{message.author.mention} 奴役失敗，繳納給 {target_user.display_name} {cost_points} 點數。 \n https://media1.tenor.com/m/q2wwTPouNfgAAAAd/depresso-pal.gif"
                )
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
                cooldowns_slave[user_id] = time.time() + 60  # 自己冷卻1分鐘
                conn.commit()

            elif chance <= 86:
                # 成功

                if target_user_id in angel_immunity:
                    await message.channel.send(f"{message.author.mention} 目標用戶 {target_user.display_name} 目前有天使卡免疫，奴役失敗！")
                    del angel_immunity[target_user_id]
                    return

                lost_points = int(target_points * 0.8)
                new_user_points = user_points + lost_points
                new_target_points = 0
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))

                cooldowns_slave[user_id] = time.time() + 600  # 自己冷卻100分鐘
                cooldowns_slave[target_user_id] = time.time() + 600

                slave_status[target_user_id] = {'end_time': time.time() + 6000, 'owner_id': user_id}

                await message.channel.send(
                    f"{message.author.mention} 奴役成功！獲得 {target_user.display_name} 80%的點數 ({lost_points} 點)，並奴役100分鐘。\n https://media1.tenor.com/m/T_ORu73GKNwAAAAd/richard-attenborough-whip.gif"
                )
                conn.commit()

            elif chance <= 98:

                if user_id in angel_immunity:
                    await message.channel.send(f"{message.author.mention} 你目前有天使卡免疫，沒被反奴役！")
                    del angel_immunity[user_id]
                    return

                lost_points = int(user_points * 0.8)
                new_user_points = 0
                new_target_points = target_points + lost_points
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))

                cooldowns_slave[user_id] = time.time() + 600  # 自己冷卻100分鐘
                cooldowns_slave[target_user_id] = time.time() + 600

                slave_status[user_id] = {'end_time': time.time() + 6000, 'owner_id': target_user_id}

                await message.channel.send(
                    f"{message.author.mention} 奴役大失敗！失去所有點數 ({user_points} 點)，並被 {target_user.display_name} 奴役100分鐘。\n https://media1.tenor.com/m/gMNC6hwTe3AAAAAd/kunta-kinte.gif"
                )
                conn.commit()

            else:
                # 雙方點數歸零，對方冷卻10分鐘
                new_user_points = 0
                new_target_points = 0
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_user_id))
                cooldowns_slave[target_user_id] = time.time() + 600  # 目標冷卻10分鐘
                cooldowns_slave[user_id] = time.time() + 600  # 自己冷卻10分鐘
                await message.channel.send(
                    f"{message.author.mention} 和 {target_user.display_name} 阿拉花瓜！雙方的點數歸零，都需要休息10分鐘。\n https://media1.tenor.com/m/2lBjv6adv6wAAAAd/capybara-orange.gif"
                )
                conn.commit()


        except Exception as e:
            await message.channel.send("使用 `!奴役 <user_id>` 時出現錯誤，請確認輸入格式並重試。")
            print(e)


    if message.content.startswith("!PVC"):
        # 解析指令，獲取目標用戶的ID
        target_id = 597075277079773227  # 預設目標ID為固定的指定ID
        user_id = message.author.id

        # 查詢使用者的當前點數
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result and result[0] > 0:
            current_points = result[0]
            contribution_points = int(current_points * 0.1)

            # 檢查是否有足夠的點數進行貢獻
            if contribution_points > 0:
                # 扣除貢獻者的10%點數
                new_user_points = current_points - contribution_points
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_user_points, user_id))

                # 獲取目標使用者的點數並增加貢獻點數
                c.execute("SELECT points FROM user_points WHERE user_id = ?", (target_id,))
                target_result = c.fetchone()
                
                if target_result:
                    new_target_points = target_result[0] + contribution_points
                    c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_target_points, target_id))
                else:
                    # 若目標使用者沒有記錄，則新增記錄
                    c.execute("INSERT INTO user_points (user_id, points) VALUES (?, ?)", (target_id, contribution_points))

                # 提交變更
                conn.commit()

                await message.channel.send(
                    f"{message.author.mention} 貢獻了 {contribution_points} 點數給 <@{target_id}>！"
                )
            else:
                await message.channel.send(f"{message.author.mention} 點數不足，無法貢獻。")
        else:
            await message.channel.send(f"{message.author.mention} 你目前沒有點數。")


    # 處理 !乞丐 指令
    if message.content == "!乞丐":
        user_id = message.author.id
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result and result[0] < 100:
            # 增加20點積分
            new_points = result[0] + 200
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_points, user_id))
            conn.commit()
            await message.channel.send(f"{message.author.mention} 你獲得了200點積分！目前有 {new_points} 積分。")
        else:
            await message.channel.send(f"{message.author.mention} 你的積分已經不少於100點，無法使用此指令。")


    # 抽卡指令
    if message.content == "!抽卡":
        # 檢查用戶的點數是否大於 100 萬
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result and result[0] >= 1000000:
            # 計算扣除點數後的剩餘點數（消耗 90%）
            current_points = result[0]
            points_to_deduct = int(current_points * 0.9)
            updated_points = current_points - points_to_deduct

            # 更新用戶點數
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (updated_points, user_id))
            conn.commit()

            # 使用 probabilities_card 抽取一張卡片
            selected_card = random.choices(cards, weights=probabilities_card, k=1)[0]
            card_id = selected_card["card_id"]
            card_name = selected_card["card_name"]

            # 檢查用戶是否已經擁有該卡片的記錄
            c.execute("SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?", (user_id, card_id))
            card_result = c.fetchone()

            if card_result:
                # 如果已經有該卡片，數量加1
                new_quantity = card_result[0] + 1
                c.execute("UPDATE user_cards SET quantity = ? WHERE user_id = ? AND card_id = ?", (new_quantity, user_id, card_id))
            else:
                # 如果沒有該卡片，新增一筆記錄並將數量設為1
                c.execute("INSERT INTO user_cards (user_id, card_id, card_name, quantity) VALUES (?, ?, ?, 1)", (user_id, card_id, card_name))
            
            conn.commit()

            # 回覆抽卡結果
            await message.channel.send(f"{message.author.mention} 消耗了 90% 的點數，抽到了一張 **{card_name}**！目前剩餘點數：{updated_points}")
        
        else:
            # 點數不足時的回覆
            await message.channel.send(f"{message.author.mention} 你的點數不足 100 萬，無法使用此指令。")


    # 處理 !點數卡 指令
    if message.content.startswith("!點數卡"):
        # 解析用戶輸入的數量
        parts = message.content.split()
        quantity = 1  # 默認使用1張卡
        user_id = message.author.id

        if len(parts) > 1:
            try:
                quantity = int(parts[1])  # 將輸入的數量轉為整數
            except ValueError:
                await message.channel.send(f"{message.author.mention} 請輸入有效的數量！")
                return

        # 確保使用的數量大於0
        if quantity <= 0:
            await message.channel.send(f"{message.author.mention} 請輸入有效的數量！")
            return

        # 查詢用戶擁有的點數卡數量
        c.execute("SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = 1", (user_id,))
        result = c.fetchone()

        if result and result[0] >= quantity:
            # 計算要獲得的點數
            points_gained = quantity * 1000000

            # 更新用戶的點數
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            points_result = c.fetchone()
            current_points = points_result[0] if points_result else 0
            new_points = current_points + points_gained

            # 更新數據庫
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_points, user_id))
            # 更新卡片數量
            c.execute("UPDATE user_cards SET quantity = quantity - ? WHERE user_id = ? AND card_id = 1", (quantity, user_id))
            conn.commit()

            await message.channel.send(f"{message.author.mention} 使用了 {quantity} 張點數卡，獲得 {points_gained} 點，現在擁有 {new_points} 點數！")
        else:
            await message.channel.send(f"{message.author.mention} 你沒有足夠的點數卡！")

    # 處理 !天使卡 指令
    if message.content.startswith("!天使卡"):
        user_id = message.author.id

        # 查詢用戶擁有的卡片數量
        c.execute("SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?", (user_id, 2))  # 假設天使卡的 card_id 是 2
        result = c.fetchone()

        if result and result[0] > 0:
            # 使用天使卡，減少卡片數量
            c.execute("UPDATE user_cards SET quantity = quantity - 1 WHERE user_id = ? AND card_id = ?", (user_id, 2))

            # 設置用戶的免疫狀態
            angel_immunity[user_id] = True  # 假設 angel_immunity 是一個字典，紀錄免疫狀態
            conn.commit()

            await message.channel.send(f"{message.author.mention} 使用了一張天使卡，獲得了免除一次大搶奪或奴役的機會！")
        else:
            await message.channel.send(f"{message.author.mention} 你沒有天使卡，無法使用此指令！")



    if message.content == "!地雷卡":
        user_id = message.author.id
    
        # 查詢用戶是否擁有地雷卡
        c.execute("SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?", (user_id, 3))  # 假設地雷卡的 card_id 是 3
        result = c.fetchone()

        if result and result[0] > 0:
            # 消耗一張地雷卡
            c.execute("UPDATE user_cards SET quantity = quantity - 1 WHERE user_id = ? AND card_id = ?", (user_id, 3))
            conn.commit()

            # 設置地雷卡狀態
            landmine_status[user_id] = True
            await message.channel.send(f"{message.author.mention} 你已經使用了一張地雷卡，隨時準備好應對搶奪或奴役的危機！")
        else:
            await message.channel.send(f"{message.author.mention} 你沒有地雷卡，無法使用此指令！")

    # 處理 !出獄卡 指令
    if message.content.startswith("!出獄卡"):
        user_id = message.author.id

        # 查詢用戶擁有的卡片數量
        c.execute("SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?", (user_id, 4))  # 假設出獄卡的 card_id 是 4
        result = c.fetchone()

        if result and result[0] > 0:
            # 使用出獄卡，減少卡片數量
            c.execute("UPDATE user_cards SET quantity = quantity - 1 WHERE user_id = ? AND card_id = ?", (user_id, 4))
        
            # 更新冷卻時間為現在時間
            current_time = time.time()
            cooldowns_rob[user_id] = current_time
            cooldowns_slave[user_id] = current_time

            # 刪除奴隸狀態
            if user_id in slave_status:
                del slave_status[user_id]

            conn.commit()

            await message.channel.send(f"{message.author.mention} 使用了一張出獄卡，所有冷卻時間已重置，並且你已經不再是奴隸！")
        else:
            await message.channel.send(f"{message.author.mention} 你沒有出獄卡，無法使用此指令！")










    if message.content == "!卡池":

        # 創建一個空的字符串以儲存卡片池消息
        card_pool_message = "以下是所有卡片種類和使用說明：\n"

        # 循環遍歷所有定義的卡片並格式化消息
        for card in cards:
            card_pool_message += f"**{card['card_name']}** (ID: {card['card_id']}): {card['description']}\n"

        card_pool_message += "\n\n限定卡池積分:\n"
        for sticker in responses6:
            sticker_id = sticker.split(":")[2]  # 取得貼圖ID
            sticker_name = sticker.split(":")[1]  # 取得貼圖名稱
            points = bonus_points2.get(sticker_name, 0)  # 獲取對應積分
            card_pool_message += f"<:{sticker_name}:{sticker_id}>: {points} 積分\n"

        await message.channel.send(card_pool_message)

    # 防B指令
    if message.content == "!防B":
        user_id = message.author.id
        try:
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result and result[0] >= 10:  # 確保有至少10點可扣除
                # 扣除10%的積分
                points_to_deduct = result[0] // 10
                c.execute("UPDATE user_points SET points = points - ? WHERE user_id = ?", (points_to_deduct, user_id))
                conn.commit()

                # 檢查用戶是否已有防B狀態
                c.execute("SELECT has_defense, rounds_left FROM user_defense WHERE user_id = ?", (user_id,))
                defense_status = c.fetchone()

                if defense_status and defense_status[0]:  # 若已有防B
                    await message.channel.send(f"{message.author.mention} 防B已啟用，剩餘 {defense_status[1]} 回合。")
                else:
                    # 啟用防B並設定5回合
                    c.execute("INSERT OR REPLACE INTO user_defense (user_id, has_defense, rounds_left) VALUES (?, 1, 5)", (user_id,))
                    conn.commit()
                    await message.channel.send(f"{message.author.mention} 消耗10%點數啟用防B 5回合，抽到banyou時將只扣除10%積分。")
            else:
                await message.channel.send(f"{message.author.mention} 你的積分不足10點，無法啟用防B。")
        except Exception as e:
            await message.channel.send(f"發生錯誤: {str(e)}")


    if message.content == "!抽限定":

        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result and result[0] >= 10:
            # 扣除10點積分
            c.execute("UPDATE user_points SET points = points - 10 WHERE user_id = ?", (user_id,))
            conn.commit()

            # 抽卡邏輯
            results = [random.choices(responses6, weights=probabilities2, k=1)[0] for _ in range(10)]

            # 計算獎勵積分
            total_bonus = sum(bonus_points2.get(result.split(':')[1], 0) for result in results)

            # 檢查是否抽到 banyou
            if any("banyou" in sticker for sticker in results):
                # 檢查防B狀態
                c.execute("SELECT has_defense, rounds_left FROM user_defense WHERE user_id = ?", (user_id,))
                defense_result = c.fetchone()
    
                if defense_result and defense_result[0]:  # 有防B
                    # 抽到 banyou 時移除防B並僅扣10%
                    updated_points = result[0] - (result[0] // 10)
                    c.execute("UPDATE user_defense SET has_defense = 0, rounds_left = 0 WHERE user_id = ?", (user_id,))
                    await message.channel.send(f"{message.author.mention} 你抽到了banyou，但因為有防B所以只扣10%！")
                else:
                    # 沒有防B時，總積分減半
                    updated_points = result[0] - (result[0] // 2)
                    await message.channel.send(f"{message.author.mention} 你抽到了banyou，積分減半！")

                # 更新用戶積分
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (updated_points, user_id))
                conn.commit()

            else:
                # 沒抽到 banyou 時減少 rounds_left
                c.execute("SELECT has_defense, rounds_left FROM user_defense WHERE user_id = ?", (user_id,))
                defense_result = c.fetchone()
    
                if defense_result and defense_result[0]:  # 有防B
                    rounds_left = defense_result[1] - 1
                    if rounds_left <= 0:
                        # 回合數結束，移除防B
                        c.execute("UPDATE user_defense SET has_defense = 0, rounds_left = 0 WHERE user_id = ?", (user_id,))
                        await message.channel.send(f"{message.author.mention} 你的防B已失效。")
                    else:
                        # 更新剩餘回合數
                        c.execute("UPDATE user_defense SET rounds_left = ? WHERE user_id = ?", (rounds_left, user_id))
                conn.commit()


            if total_bonus > 0:
                c.execute("UPDATE user_points SET points = points + ? WHERE user_id = ?", (total_bonus, user_id))
                conn.commit()

            # 查詢最新積分
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            updated_points = c.fetchone()[0]

            # 發送抽卡結果
            response_message = f"{message.author.mention} 抽卡內容:\t" + "\t".join([f"<:{result.split(':')[1]}:{result.split(':')[2]}>" for result in results])
            

            # 如果抽到，顯示額外訊息
            if any("ding_eat4" in sticker for sticker in results):
                response_message += "\n吃了香腸補充了20點！"
                custom_emoji = discord.utils.get(message.guild.emojis, name='ding_eat4')
                if custom_emoji:
                    await message.add_reaction(custom_emoji)  # 添加自定義表情符號
            if any("neck_pinching" in sticker for sticker in results):
                response_message += "\n壁咚景碩吸取了80點！"
                custom_emoji = discord.utils.get(message.guild.emojis, name='neck_pinching')
                if custom_emoji:
                    await message.add_reaction(custom_emoji)  # 添加自定義表情符號
            if any("j_ding_huaiyun" in sticker for sticker in results):
                response_message += "\n榨乾王董吸取了100點！"
                custom_emoji = discord.utils.get(message.guild.emojis, name='j_ding_huaiyun')
                if custom_emoji:
                    await message.add_reaction(custom_emoji)  # 添加自定義表情符號
            if any("banyou" in sticker for sticker in results):
                response_message += "\n你被阿丁BAN了，阿丁吸收你一半的點數！"
                custom_emoji = discord.utils.get(message.guild.emojis, name='banyou')
                if custom_emoji:
                    await message.add_reaction(custom_emoji)  # 添加自定義表情符號

            
            response_message += f"\n你使用了10點積分抽限定！目前剩餘 {updated_points} 積分，並獲得額外 {total_bonus} 積分。"
            await message.channel.send(response_message)

        else:
            await message.channel.send(f"{message.author.mention} 你的積分不足10點，無法抽限定。")


    if message.content == "!五連抽":
        user_id = message.author.id
        response_message = f"{message.author.mention} 的五連抽結果：\n"

        # 查詢用戶積分
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            await message.channel.send(f"{message.author.mention} 你目前沒有積分紀錄。")
            return

        current_points = result[0]
        total_deduction = 0
        total_bonus = 0
        defense_changed = False  # 記錄防B狀態是否改變
        updated_defense_status = None  # 用於存儲更新後的防B狀態

        for _ in range(5):
            if current_points < 10:
                response_message += "\n積分不足無法進行抽卡。"
                break

            # 扣除10點積分
            total_deduction += 10
            current_points -= 10

            # 抽卡邏輯
            results = [random.choices(responses6, weights=probabilities2, k=1)[0] for _ in range(10)]
            response_message += "\n 抽卡內容:\t" + "\t".join([f"<:{result.split(':')[1]}:{result.split(':')[2]}>" for result in results])

            # 計算獎勵積分
            total_bonus += sum(bonus_points2.get(result.split(':')[1], 0) for result in results)

            # 檢查是否抽到 banyou
            if any("banyou" in sticker for sticker in results):
                # 檢查防B狀態
                c.execute("SELECT has_defense, rounds_left FROM user_defense WHERE user_id = ?", (user_id,))
                defense_result = c.fetchone()

                if defense_result and defense_result[0]:  # 有防B
                    current_points -= int(current_points * 0.1)  # 扣除10%
                    updated_defense_status = (0, 0)  # 移除防B
                    response_message += "\n你抽到了banyou，但因為有防B所以只扣10%！"
                    defense_changed = True
                else:
                    current_points //= 2  # 积分减半
                    response_message += "\n你抽到了banyou，積分減半！"
            else:
                # 若沒有抽到 banyou，減少 rounds_left
                c.execute("SELECT has_defense, rounds_left FROM user_defense WHERE user_id = ?", (user_id,))
                defense_result = c.fetchone()

                if defense_result and defense_result[0]:  # 有防B
                    rounds_left = defense_result[1] - 1
                    if rounds_left <= 0:
                        updated_defense_status = (0, 0)
                        response_message += "\n你的防B已失效。"
                        defense_changed = True
                    else:
                        updated_defense_status = (1, rounds_left)
                        defense_changed = True

            if defense_changed and updated_defense_status:
                c.execute("UPDATE user_defense SET has_defense = ?, rounds_left = ? WHERE user_id = ?", (*updated_defense_status, user_id))
            conn.commit()

        # 更新積分和防B狀態
        current_points += total_bonus
        c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (current_points, user_id))


        # 發送最終結果
        response_message += f"\n你使用了五連抽限定！目前剩餘 {current_points} 積分"
        await message.channel.send(response_message)


    # 处理 !排行榜 指令
    elif message.content == "!排行榜":
        c.execute("SELECT user_id, points FROM user_points ORDER BY points DESC LIMIT 8")
        top_users = c.fetchall()

        if top_users:
            leaderboard_message = "🏆 **排行榜** 🏆\n"
            for rank, (user_id, points) in enumerate(top_users, start=1):
                user = await bot.fetch_user(user_id)  # 获取用户对象以便显示用户名
                formatted_points = f"{points:,}"  # 將點數格式化為帶逗號的字符串
                leaderboard_message += f"{rank}. {user.display_name} (ID: {user_id}): {formatted_points} 積分\n"
        else:
            leaderboard_message = "目前沒有任何使用者的積分紀錄。"

        await message.channel.send(leaderboard_message)


    # 处理 !排行榜 指令
    elif message.content == "!第一":
        c.execute("SELECT user_id, points FROM user_points ORDER BY points DESC LIMIT 1")
        top_users = c.fetchall()

        if top_users:
            for rank, (user_id, points) in enumerate(top_users, start=1):
                user = await bot.fetch_user(user_id)  # 获取用户对象以便显示用户名
                formatted_points = f"{points:,}"  # 將點數格式化為帶逗號的字符串
                leaderboard_message = f"{user_id}"
        else:
            leaderboard_message = "目前沒有任何使用者的積分紀錄。"

        await message.channel.send(leaderboard_message)



    if message.content == "!賭博":
        user_id = message.author.id
        
        # 查詢使用者的當前積分
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            current_points = result[0]
            gamble_result = random.choices(list(gamble_outcomes.keys()), weights=gamble_probabilities, k=1)[0]
            point_change = gamble_outcomes[gamble_result]

            # 計算變化後的積分
            updated_points = current_points + int(current_points * point_change)

            # 更新使用者的積分
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (updated_points, user_id))
            conn.commit()

            # 發送賭博結果
            await message.channel.send(f"{message.author.mention} 你賭博的結果是: **{gamble_result}**。\n目前積分: {updated_points} 點。")
        else:
            await message.channel.send(f"{message.author.mention} 你目前沒有積分紀錄。")

    if message.content == "!八堵":
        user_id = message.author.id

        # 查詢使用者的當前積分
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            current_points = result[0]
            response_message = f"{message.author.mention} 你的八次賭博結果如下：\n"

            # 執行八次賭博
            for i in range(8):
                gamble_result = random.choices(list(gamble_outcomes.keys()), weights=gamble_probabilities, k=1)[0]
                point_change = gamble_outcomes[gamble_result]
                change_amount = int(current_points * point_change)
                current_points += change_amount

                response_message += f"第 {i+1} 次: **{gamble_result}**，變動 {change_amount} 點。\n"

            # 計算並更新最終積分
            updated_points = max(current_points,0)
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (updated_points, user_id))
            conn.commit()

            # 發送結果
            response_message += f"目前積分: {updated_points} 點。"
            await message.channel.send(response_message)
        else:
            await message.channel.send(f"{message.author.mention} 你目前沒有積分紀錄。")


    if message.content == "!拉布拉特女裝":
    # 使用官方表情符號
        arrow_emoji = "🐍"  # 這是箭頭符號的Unicode表示
        await message.add_reaction(arrow_emoji)  # 添加官方表情符號
        response0 = " || 請私我  ||"
        await message.channel.send(response0)

    if "走吃飯" in message.content:
        # 使用表情名稱 'goeat' 獲取自定義表情符號對象
        custom_emoji = discord.utils.get(message.guild.emojis, name='goeat')
        if custom_emoji:
            await message.add_reaction(custom_emoji)  # 添加自定義表情符號
        else:
            print("Custom emoji 'goeat' not found")

              # 如果消息中包含 '!吃啥'
    if message.content.startswith("!吃啥"):
        # 使用表情名稱 'ding_eat4' 獲取自定義表情符號對象
        custom_emoji = discord.utils.get(message.guild.emojis, name='ding_eat4')
        if custom_emoji:
            await message.add_reaction(custom_emoji)  # 添加自定義表情符號
        else:
            await message.channel.send("抱歉，我找不到名為 'ding_eat4' 的表情符號！")  # 回覆找不到表情的訊息

    if message.content == "!吃啥":

        # 隨機選擇一個回應
        response = random.choice(responses)
        # 引用輸入指令的人
        user = message.author
        await message.channel.send(f"{user.mention} {response}")

    if message.content == "!誰最可愛":
        # 使用官方表情符號
        arrow_emoji = "↖️"  # 這是箭頭符號的Unicode表示
        await message.add_reaction(arrow_emoji)  # 添加官方表情符號

    if message.content == "!今日":

        # 隨機選擇一個回應
        response2 = random.choice(responses2)
        # 引用輸入指令的人
        user = message.author
        await message.channel.send(f"{user.mention} ||{response2}||")

    if message.content == "!Labrat":

        # 隨機選擇一個回應
        response3 = random.choice(responses3)
        # 引用輸入指令的人
        user = message.author
        await message.channel.send(f"{user.mention} 你說的對，但這就是最可愛的Labrat \n {response3}")


    if message.content == "!PUA":

        # 隨機選擇一個回應
        response4 = random.choice(responses4)
        # 引用輸入指令的人
        user = message.author
        await message.channel.send(f"{user.mention} {response4}")





    if message.content == "!射阿丁":
        user_id = message.author.id

        # 檢查玩家是否有資金記錄
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        # 確認玩家有資金記錄
        if result is None:
            await message.channel.send(f"{message.author.mention} 你還沒有設定資金記錄！請確認你已經建立了遊戲帳戶。")
            return

        current_balance = result[0]

        # 扣除10%的點數
        deduction = current_balance * 0.05
        new_balance = int(current_balance - deduction)
        c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()

        # 生成兩張牌（1-100，代表牌面值）
        first_card = random.randint(1, 90)
        second_card = random.randint(10, 100)

        # 如果兩張牌相同，重新發一對
        while second_card == first_card:
            second_card = random.randint(1, 100)

        # 確保第一張牌小於第二張牌
        lower_card, upper_card = sorted([first_card, second_card])

        await message.channel.send(
            f"{message.author.mention} \n"
            f"你已經扣除了 {int(deduction)} 點，剩餘點數：{new_balance} 點。\n"
            f"你的第一張牌是 {lower_card}，第二張牌是 {upper_card}。\n"
            f"請決定下注金額並選擇猜測結果！輸入 `!猜中 <下注金額>` 或 `!猜不中 <下注金額>`。"
        )

        # 儲存玩家的牌數據
        if not hasattr(bot, "game_data"):
            bot.game_data = {}
        bot.game_data[user_id] = {
            "lower_card": lower_card,
            "upper_card": upper_card,
        }


    # 猜中
    elif message.content.startswith("!猜中"):
        try:
            bet = int(message.content.split(" ")[1])
        except (IndexError, ValueError):
            await message.channel.send(f"{message.author.mention} 請輸入有效的下注金額，例如：`!猜中 100`")
            return

        # 確認是否有進行中的遊戲
        if not hasattr(bot, "game_data") or user_id not in bot.game_data:
            await message.channel.send(f"{message.author.mention} 請先使用 `!射阿丁` 開始遊戲！")
            return

        # 檢查玩家是否有足夠的資金
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if not result or bet > result[0]:
            await message.channel.send(f"{message.author.mention} 抱歉，你的餘額不足！目前餘額：{result[0] if result else 0} 點")
            return

        # 扣除下注金額
        new_balance = result[0] - bet
        c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()

        # 發第三張牌
        third_card = random.randint(1, 100)
        lower_card = bot.game_data[user_id]["lower_card"]
        upper_card = bot.game_data[user_id]["upper_card"]

        await message.channel.send(f"{message.author.mention} 第三張牌是 {third_card}！")

        # 判斷射中還是射失
        if lower_card < third_card < upper_card:
            # 計算差距
            gap = upper_card - lower_card
    
            # 假設最小差距為1，最大差距為99
            if gap == 1:
                multiplier = 5  # 最小差距對應最高倍率
            elif gap == 99:
                multiplier = 1.5  # 最大差距對應最低倍率
            else:
                # 使用線性映射將差距轉換為倍率
                # gap 在 1 到 99 之間進行映射
                multiplier = 5 - (3.5 / 98) * (gap - 1)  # 從 10 到 1.5 之間平滑過渡
    
            winnings = int(bet * multiplier)  # 計算獎金
            new_balance += winnings
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            await message.channel.send(f"{message.author.mention} 恭喜你，射中阿丁！你贏得 {winnings} 點！目前餘額：{new_balance} 點")
        else:
            await message.channel.send(f"{message.author.mention} 抱歉，阿丁閃掉了！失去 {bet} 點。餘額：{new_balance} 點")

        # 清除玩家的遊戲資料
        del bot.game_data[user_id]

    # 猜不中
    elif message.content.startswith("!猜不中"):
        try:
            bet = int(message.content.split(" ")[1])
        except (IndexError, ValueError):
            await message.channel.send(f"{message.author.mention} 請輸入有效的下注金額，例如：`!猜不中 100`")
            return

        # 確認是否有進行中的遊戲
        if not hasattr(bot, "game_data") or user_id not in bot.game_data:
            await message.channel.send(f"{message.author.mention} 請先使用 `!射阿丁` 開始遊戲！")
            return

        # 檢查玩家是否有足夠的資金
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if not result or bet > result[0]:
            await message.channel.send(f"{message.author.mention} 抱歉，你的餘額不足！目前餘額：{result[0] if result else 0} 點")
            return

        # 扣除下注金額
        new_balance = result[0] - bet
        c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()

        # 發第三張牌
        third_card = random.randint(1, 100)
        lower_card = bot.game_data[user_id]["lower_card"]
        upper_card = bot.game_data[user_id]["upper_card"]

        await message.channel.send(f"{message.author.mention} 第三張牌是 {third_card}！")

        # 判斷射中還是射失
        if third_card <= lower_card or third_card >= upper_card:
            # 計算差距
            gap = upper_card - lower_card
    
            # 根據差距決定倍率
            if gap == 1:
                multiplier = 1.5  # 最小差距對應最低倍率
            elif gap == 99:
                multiplier = 5  # 最大差距對應最高倍率
            else:
                # 使用線性映射將差距轉換為倍率
                multiplier = 1.5 + (3.8 / 98) * (gap - 1)  # 從 1.5 到 10 之間平滑過渡

            winnings = int(bet * multiplier)  # 計算獎金
            new_balance += winnings
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            await message.channel.send(f"{message.author.mention} 恭喜你，射不中阿丁！你贏得 {winnings} 點！目前餘額：{new_balance} 點")
        else:
            await message.channel.send(f"{message.author.mention} 抱歉，射中了阿丁！失去 {bet} 點。餘額：{new_balance} 點")

        # 清除玩家的遊戲資料
        del bot.game_data[user_id]


    if message.content == "!裝備指令":
        response = (
            "` \n"
            "!抽裝備 : 消耗10萬點，隨機抽一件裝備\n"
            "!查庫存 : 查看所有擁有的裝備：ID、部位、稀有度、強化等級與屬性\n"
            "!屬性 : 查看自己的屬性，為各部位強化度最高的屬性加總\n"
            "!燒 <ID> : 會將該ID裝備移除，並給予至少5萬點 (根據稀有度)\n"
            "!強化 <ID> : 強化該ID的裝備，基礎為10萬點，根據強化等級、稀有度而有所提升\n\n"
            "稀有度：N, H, R, SR, SSR, UR, MR, BR\n"
            "部位：頭盔、手套、胸甲、腿甲、褲襠甲、鞋子、武器、盾牌`"
        )
        await message.channel.send(response)

    if message.content == "!抽裝備":
        user_id = message.author.id

        # 檢查用戶積分是否足夠
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
        result = c.fetchone()
    
        if result and result[0] >= 100000:
            c.execute("UPDATE user_points SET points = points - 100000 WHERE user_id = ?", (user_id,))
            conn.commit()
        
            # 隨機選擇一個裝備
            slot = random.choice(equipment_slots)
            equipment_name = slot["equipment_name"]
        
            # 隨機選擇稀有度
            rarity = random.choices(
                [level["rarity"] for level in rarity_levels], 
                weights=rarity_probabilities, 
                k=1
            )[0]
        
            # 取得稀有度對應屬性範圍
            rarity_level = next(level for level in rarity_levels if level["rarity"] == rarity)
            min_attr, max_attr = rarity_level["min_attr"], rarity_level["max_attr"]
        
            # 根據屬性類型隨機生成數值
            attributes = equipment_attributes[equipment_name]
            stats = {attr: random.randint(min_attr, max_attr) for attr in attributes}
        
            # 插入新裝備
            c.execute("""
            INSERT INTO user_equipment (user_id, equipment_name, rarity, health, mana, stamina, attack, magic_attack, defense, magic_defense, speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, equipment_name, rarity, 
                  stats.get("health", 0), stats.get("mana", 0), stats.get("stamina", 0), 
                  stats.get("attack", 0), stats.get("magic_attack", 0), 
                  stats.get("defense", 0), stats.get("magic_defense", 0), stats.get("speed", 0)))
            conn.commit()
            equipment_id = c.lastrowid  # 取得自動生成的 equipment_id
        
            await message.channel.send(
                f"{message.author.mention} 你抽到了裝備 {equipment_name}！\n"
                f"裝備 ID: {equipment_id}\n"
                f"稀有度: {rarity}\n"
                f"屬性: {stats}"
            )
        else:
            await message.channel.send(f"{message.author.mention} 你的積分不足，無法抽取裝備！")

    if message.content == "!查庫存":
        user_id = message.author.id

        # 查詢該使用者所有裝備
        c.execute("""
        SELECT equipment_id, equipment_name, rarity, upgrade, health, mana, stamina, attack, magic_attack, defense, magic_defense, speed
        FROM user_equipment
        WHERE user_id = ?
        """, (user_id,))
        equipment_list = c.fetchall()

        if equipment_list:
            # 根據裝備名稱排序
            equipment_list.sort(key=lambda x: x[1])  # 依照 equipment_name 排序

            # 建立回應訊息
            response_message = f"{message.author.mention} 你擁有以下裝備：\n"
            previous_name = None  # 用來跟踪前一個裝備名稱
            for equip in equipment_list:
                equipment_id, equipment_name, rarity, upgrade = equip[:4]
                attributes = equip[4:]
                attr_text = ", ".join([f"{attr} {value}" for attr, value in zip(
                    ["health", "mana", "stamina", "attack", "magic_attack", "defense", "magic_defense", "speed"], attributes) if value > 0])

                # 當前裝備名稱與上一個不一樣時，顯示該裝備名稱
                if equipment_name != previous_name:
                    response_message += f"\n{equipment_name}:\n"
                    previous_name = equipment_name  # 更新前一個名稱
            
                response_message += (
                    f"  裝備ID: {equipment_id} | 稀有度: {rarity} | 強化等級: {upgrade} | 屬性: {attr_text}\n"
                )

            await message.channel.send(response_message)
        else:
            await message.channel.send(f"{message.author.mention} 你目前沒有任何裝備。")

    if message.content == "!屬性":
        user_id = message.author.id

        # 查詢每個 equipment_name 中 upgrade 最高的裝備
        c.execute("""
        SELECT equipment_name, MAX(upgrade) as max_upgrade
        FROM user_equipment
        WHERE user_id = ?
        GROUP BY equipment_name
        """, (user_id,))
        best_equipment = c.fetchall()

        # 如果沒有任何裝備
        if not best_equipment:
            await message.channel.send(f"{message.author.mention} 你目前沒有任何裝備。")
            return

        # 查詢每個最高 upgrade 裝備的屬性
        total_attributes = {
            "health": 0, "mana": 0, "stamina": 0, "attack": 0,
            "magic_attack": 0, "defense": 0, "magic_defense": 0, "speed": 0
        }

        for equip_name, max_upgrade in best_equipment:
            c.execute("""
            SELECT health, mana, stamina, attack, magic_attack, 
                   defense, magic_defense, speed
            FROM user_equipment
            WHERE user_id = ? AND equipment_name = ? AND upgrade = ?
            LIMIT 1
            """, (user_id, equip_name, max_upgrade))
        
            attributes = c.fetchone()
            if attributes:
                for i, key in enumerate(total_attributes.keys()):
                    total_attributes[key] += attributes[i]

        # 建立回應訊息
        response_message = f"{message.author.mention} 你的屬性如下：\n"
        response_message += "\n".join([f"{attr}: {value}" for attr, value in total_attributes.items()])
        await message.channel.send(response_message)

    # 強化指令
    if message.content.startswith("!強化 "):
        try:
            # 解析裝備 ID
            equipment_id = int(message.content.split()[1])
            user_id = message.author.id

            # 檢查裝備是否存在
            c.execute("""
            SELECT equipment_name, rarity, upgrade, health, mana, stamina, attack, magic_attack, defense, magic_defense, speed 
            FROM user_equipment 
            WHERE user_id = ? AND equipment_id = ?
            """, (user_id, equipment_id))
            equipment = c.fetchone()

            if not equipment:
                await message.channel.send(f"{message.author.mention} 找不到指定的裝備，請確認裝備 ID 是否正確。")
                return

            equipment_name, rarity, upgrade, health, mana, stamina, attack, magic_attack, defense, magic_defense, speed = equipment

            # 計算強化所需積分
            upgrade_multiplier = 1.1 ** upgrade
            enhancement_multiplier = enhance_cost_rates[rarity]
            enhancement_cost = int(100000 * upgrade_multiplier * enhancement_multiplier)  # 基本強化費用
        
            # 稀有度的強化成功率，根據 upgrade 值每次減少 5% 成功機率
            success_rate = enhance_success_rates[rarity] - (upgrade * 0.05)
            success_rate = max(success_rate, 0.05)  # 最低成功率為 5%
            success_rate_percent = int(success_rate*100)

            # 檢查是否有足夠的積分
            c.execute("""
            SELECT points FROM user_points WHERE user_id = ?
            """, (user_id,))
            current_points = c.fetchone()

            if current_points is None or current_points[0] < enhancement_cost:
                await message.channel.send(f"{message.author.mention} 你的積分不足，目前需要: {enhancement_cost} 點積分。")
                return
            else:
                # 扣除積分
                c.execute("""
                UPDATE user_points SET points = points - ?
                WHERE user_id = ?
                """, (enhancement_cost, user_id))
                conn.commit()

            # 隨機判斷強化是否成功
            if random.random() <= success_rate:               

                # 增加 upgrade
                new_upgrade = upgrade + 1

                # 強化後，所有屬性 +10%
                new_health = int(health * enhancement_multiplier * 1.1)
                new_mana = int(mana * enhancement_multiplier * 1.1)
                new_stamina = int(stamina * enhancement_multiplier * 1.1)
                new_attack = int(attack * enhancement_multiplier * 1.1)
                new_magic_attack = int(magic_attack * enhancement_multiplier * 1.1)
                new_defense = int(defense * enhancement_multiplier * 1.1)
                new_magic_defense = int(magic_defense * enhancement_multiplier * 1.1)
                new_speed = int(speed * enhancement_multiplier * 1.1)

                # 更新裝備資料
                c.execute("""
                UPDATE user_equipment 
                SET upgrade = ?, health = ?, mana = ?, stamina = ?, attack = ?, magic_attack = ?, 
                    defense = ?, magic_defense = ?, speed = ?
                WHERE user_id = ? AND equipment_id = ?
                """, (new_upgrade, new_health, new_mana, new_stamina, new_attack, new_magic_attack, 
                      new_defense, new_magic_defense, new_speed, user_id, equipment_id))
                conn.commit()

                await message.channel.send(f"{message.author.mention} 機率 {success_rate_percent}% 強化成功！\n裝備 {equipment_name} 強化至 {new_upgrade} 級。屬性已增加 10%。")
            else:
                # 強化失敗
                await message.channel.send(f"{message.author.mention} 機率 {success_rate_percent}% 強化失敗，裝備 {equipment_name} 依然保持原狀。")
    
        except ValueError:
            await message.channel.send(f"{message.author.mention} 請提供正確的裝備 ID。")

    # 燒裝備指令
    if message.content.startswith("!燒 "):
        try:
            # 解析裝備 ID
            equipment_id = int(message.content.split()[1])
            user_id = message.author.id

            # 檢查裝備是否存在
            c.execute("""
            SELECT equipment_name, rarity FROM user_equipment 
            WHERE user_id = ? AND equipment_id = ?
            """, (user_id, equipment_id))
            equipment = c.fetchone()

            if not equipment:
                await message.channel.send(f"{message.author.mention} 找不到指定的裝備，請確認裝備 ID 是否正確。")
                return

            equipment_name, rarity = equipment

            # 根據稀有度計算給予的點數
            enhancement_multiplier = enhance_cost_rates.get(rarity, 1)  # 默認為 1（防止不存在的稀有度）
            points_to_add = int(50000 * enhancement_multiplier)

            # 更新用戶積分
            c.execute("""
            UPDATE user_points 
            SET points = points + ? 
            WHERE user_id = ?
            """, (points_to_add, user_id))
            conn.commit()

            # 移除裝備
            c.execute("""
            DELETE FROM user_equipment 
            WHERE user_id = ? AND equipment_id = ?
            """, (user_id, equipment_id))
            conn.commit()

            # 回應訊息
            await message.channel.send(f"{message.author.mention} 裝備 {equipment_name} 已被燒毀，你獲得 {points_to_add} 點積分。")
    
        except ValueError:
            await message.channel.send(f"{message.author.mention} 請提供正確的裝備 ID。")




    if message.content.startswith("!kill"):
        # 檢查是否為指定用戶
        if user_id != 597075277079773227:
            await message.channel.send(f"{message.author.mention} 你沒有權限使用此指令。")
            return

        # 解析目標 ID
        try:
            target_id = int(message.content.split(" ")[1])
        except (IndexError, ValueError):
            await message.channel.send("請指定有效的目標 ID。")
            return

        # 確認目標用戶的存在
        c.execute("SELECT points FROM user_points WHERE user_id = ?", (target_id,))
        target_points_result = c.fetchone()
    
        if target_points_result:
            # 刪除目標用戶的資料
            c.execute("DELETE FROM user_points WHERE user_id = ?", (target_id,))
            c.execute("DELETE FROM user_defense WHERE user_id = ?", (target_id,))
            c.execute("DELETE FROM user_cards WHERE user_id = ?", (target_id,))
            c.execute("DELETE FROM user_equipment WHERE user_id = ?", (target_id,))
            conn.commit()
        
            await message.channel.send(f"{message.author.mention} 已成功刪除 {target_id} 的點數資料。")
        else:
            await message.channel.send("找不到指定的用戶。")

    # 檢查是否使用 !money 指令
    if message.content == "!money":
        # 確認只有特定 user_id 可以使用此指令
        if user_id == 597075277079773227:
            # 增加 100 萬點數
            c.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            # 如果有查到此用戶的點數資料，更新點數
            if result:
                new_points = result[0] + 100000000
                c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", (new_points, user_id))
            else:
                # 若無此用戶資料，則插入新資料
                new_points = 100000000
                c.execute("INSERT INTO user_points (user_id, points) VALUES (?, ?)", (user_id, new_points))
            
            conn.commit()
            await message.channel.send(f"{message.author.mention} 你獲得了 100 萬點數！目前總點數為：{new_points} 點。")
        
        else:
            await message.channel.send(f"{message.author.mention} 你無權使用此指令。")

    # 檢查 !card 指令
    if message.content.startswith("!card"):
        parts = message.content.split(" ")
        
        # 確認用戶是特定用戶
        if message.author.id != 597075277079773227:
            await message.channel.send(f"{message.author.mention} 你沒有權限使用此指令！")
            return

        # 確認用戶輸入了 card_id
        if len(parts) < 2:
            await message.channel.send("請提供有效的 card_id，例如：`!card <card_id>`。")
            return

        try:
            card_id = int(parts[1])
        except ValueError:
            await message.channel.send("請提供有效的數字作為 card_id。")
            return

        # 將卡片數量增加到用戶的卡片庫
        c.execute("INSERT INTO user_cards (user_id, card_id, card_name, quantity) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = quantity + ?",
                  (message.author.id, card_id, f"卡片名稱-{card_id}", 10, 10))  # 替換 "卡片名稱-{card_id}" 為實際的卡片名稱
        conn.commit()

        await message.channel.send(f"{message.author.mention} 成功給予 {card_id} 10 張卡片！")


    await bot.process_commands(message)  # 確保其他指令仍然能夠正常工作

@bot.command()
async def 誰最可愛(ctx):
    user = ctx.author
    await ctx.send(f"{user.mention} 和Labrat都是最可愛的！")


bot.run(TOKEN)

# 保持視窗開啟
input("按 Enter 鍵退出...")
sys.exit(0)  # 確保錯誤後繼續執行，但不會終止整個程序