"""
为英雄档案添加别名/昵称字段
包含：英文原名、音译名、社区常用昵称
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "champions.json")
OUT  = os.path.join(ROOT, "pipeline", "output")

# ─── 别名映射：CN名 → [别名列表] ───
ALIASES = {
    "吉格斯":       ["Ziggs", "炸弹人"],
    "布兰德":       ["Brand", "火男"],
    "卡莎":         ["Kaisa", "Kai'Sa", "凯莎"],
    "提莫":         ["Teemo"],
    "卡尔萨斯":     ["Karthus", "死歌"],
    "维克托":       ["Viktor", "三只手"],
    "韦鲁斯":       ["Varus", "维鲁斯"],
    "婕拉":         ["Zyra"],
    "泽拉斯":       ["Xerath", "棺材板", "棺材"],
    "阿狸":         ["Ahri", "狐狸"],
    "莫甘娜":       ["Morgana", "莫妈"],
    "凯南":         ["Kennen", "电耗子"],
    "伊泽瑞尔":     ["Ezreal", "EZ", "ez"],
    "亚索":         ["Yasuo", "托儿索"],
    "塞拉斯":       ["Sylas"],
    "薇恩":         ["Vayne", "VN", "vn"],
    "暗裔剑魔":     ["Aatrox", "剑魔"],
    "离群之刺":     ["Akali", "阿卡丽"],
    "影哨":         ["Akshan", "阿克尚"],
    "牛头酋长":     ["Alistar", "牛头", "阿利斯塔"],
    "铁血狼母":     ["Ambessa", "安蓓萨", "狼母"],
    "殇之木乃伊":   ["Amumu", "阿木木", "木乃伊"],
    "冰晶凤凰":     ["Anivia", "冰鸟", "凤凰"],
    "黑暗之女":     ["Annie", "安妮", "火女"],
    "残月之肃":     ["Aphelios", "厄斐琉斯"],
    "寒冰射手":     ["Ashe", "艾希", "寒冰"],
    "铸星龙王":     ["AurelionSol", "Aurelion Sol", "龙王", "奥瑞利安索尔"],
    "双界灵兔":     ["Aurora", "极光", "兔子", "奥萝拉"],
    "沙漠皇帝":     ["Azir", "沙皇", "黄鸡"],
    "星界游神":     ["Bard", "巴德"],
    "虚空女皇":     ["Belveth", "Bel'Veth", "贝蕾亚"],
    "蒸汽机器人":   ["Blitzcrank", "机器人", "布里茨"],
    "弗雷尔卓德之心": ["Braum", "布隆"],
    "狂厄蔷薇":     ["Briar", "布里亚", "蔷薇"],
    "皮城女警":     ["Caitlyn", "女警", "凯特琳"],
    "青钢影":       ["Camille", "卡蜜尔"],
    "魔蛇之拥":     ["Cassiopeia", "蛇女", "卡西奥佩娅"],
    "虚空恐惧":     ["Chogath", "Cho'Gath", "大虫子", "虫子", "科加斯"],
    "英勇投弹手":   ["Corki", "飞机", "库奇"],
    "诺克萨斯之手": ["Darius", "诺手", "德莱厄斯"],
    "皎月女神":     ["Diana", "皎月", "戴安娜"],
    "荣耀行刑官":   ["Draven", "德莱文"],
    "祖安狂人":     ["DrMundo", "Dr.Mundo", "蒙多"],
    "时间刺客":     ["Ekko", "艾克"],
    "蜘蛛女皇":     ["Elise", "蜘蛛", "伊莉丝"],
    "痛苦之拥":     ["Evelynn", "寡妇", "伊芙琳"],
    "远古恐惧":     ["Fiddlesticks", "稻草人", "费德提克"],
    "无双剑姬":     ["Fiora", "剑姬", "菲奥娜"],
    "潮汐海灵":     ["Fizz", "小鱼人", "菲兹"],
    "正义巨像":     ["Galio", "加里奥", "石像鬼"],
    "海洋之灾":     ["Gangplank", "船长", "普朗克"],
    "德玛西亚之力": ["Garen", "盖伦"],
    "迷失之牙":     ["Gnar", "纳尔"],
    "酒桶":         ["Gragas", "古拉加斯", "胖子"],
    "法外狂徒":     ["Graves", "男枪", "格雷福斯"],
    "灵罗娃娃":     ["Gwen", "格温"],
    "战争之影":     ["Hecarim", "人马", "赫卡里姆"],
    "大发明家":     ["Heimerdinger", "大头", "黑默丁格"],
    "异画师":       ["Hwei", "慧"],
    "海兽祭司":     ["Illaoi", "俄洛伊", "触手妈"],
    "刀锋舞者":     ["Irelia", "刀妹", "艾瑞莉娅"],
    "翠神":         ["Ivern", "艾翁", "树人"],
    "风暴之怒":     ["Janna", "风女", "迦娜"],
    "德玛西亚皇子": ["JarvanIV", "Jarvan IV", "皇子", "嘉文"],
    "武器大师":     ["Jax", "贾克斯"],
    "未来守护者":   ["Jayce", "杰斯"],
    "戏命师":       ["Jhin", "烬"],
    "暴走萝莉":     ["Jinx", "金克丝"],
    "复仇之矛":     ["Kalista", "卡莉斯塔"],
    "天启者":       ["Karma", "卡尔玛"],
    "虚空行者":     ["Kassadin", "卡萨丁"],
    "不祥之刃":     ["Katarina", "卡特", "卡特琳娜"],
    "正义天使":     ["Kayle", "凯尔"],
    "影流之镰":     ["Kayn", "凯隐"],
    "虚空掠夺者":   ["Khazix", "Kha'Zix", "螳螂"],
    "永猎双子":     ["Kindred", "千珏"],
    "暴怒骑士":     ["Kled", "克烈"],
    "深渊巨口":     ["KogMaw", "Kog'Maw", "大嘴"],
    "纳祖芒荣耀":   ["KSante", "K'Sante", "奎桑提"],
    "诡术妖姬":     ["Leblanc", "LeBlanc", "妖姬", "乐芙兰"],
    "盲僧":         ["LeeSin", "Lee Sin", "瞎子", "李青"],
    "曙光女神":     ["Leona", "蕾欧娜", "日女"],
    "含羞蓓蕾":     ["Lillia", "莉莉娅", "小鹿"],
    "冰霜女巫":     ["Lissandra", "丽桑卓", "冰女"],
    "圣枪游侠":     ["Lucian", "卢锡安", "奥巴马"],
    "仙灵女巫":     ["Lulu", "璐璐"],
    "光辉女郎":     ["Lux", "拉克丝"],
    "熔岩巨兽":     ["Malphite", "石头人", "墨菲特"],
    "虚空先知":     ["Malzahar", "蚂蚱", "玛尔扎哈"],
    "扭曲树精":     ["Maokai", "大树", "茂凯"],
    "无极剑圣":     ["MasterYi", "Master Yi", "剑圣", "易大师", "易"],
    "流光镜影":     ["Mel", "梅尔"],
    "明烛":         ["Milio", "米利欧"],
    "赏金猎人":     ["MissFortune", "Miss Fortune", "女枪", "好运姐", "MF"],
    "齐天大圣":     ["MonkeyKing", "Wukong", "猴子", "悟空"],
    "铁铠冥魂":     ["Mordekaiser", "铁男", "莫德凯撒"],
    "百裂冥犬":     ["Naafiri", "纳亚菲利", "狗子"],
    "唤潮鲛姬":     ["Nami", "娜美"],
    "沙漠死神":     ["Nasus", "狗头", "内瑟斯"],
    "深海泰坦":     ["Nautilus", "泰坦", "诺提勒斯"],
    "万花通灵":     ["Neeko", "妮蔻"],
    "狂野女猎手":   ["Nidalee", "豹女", "奈德丽"],
    "不羁之悦":     ["Nilah", "尼菈"],
    "永恒梦魇":     ["Nocturne", "梦魇", "魔腾"],
    "雪原双子":     ["Nunu", "努努", "雪人"],
    "狂战士":       ["Olaf", "奥拉夫"],
    "发条魔灵":     ["Orianna", "发条", "奥莉安娜"],
    "山隐之焰":     ["Ornn", "奥恩", "山羊"],
    "不屈之枪":     ["Pantheon", "潘森"],
    "圣锤之毅":     ["Poppy", "波比"],
    "血港鬼影":     ["Pyke", "派克"],
    "元素女皇":     ["Qiyana", "奇亚娜"],
    "德玛西亚之翼": ["Quinn", "奎因", "鸟人"],
    "幻翎":         ["Rakan", "洛"],
    "披甲龙龟":     ["Rammus", "龙龟", "拉莫斯"],
    "虚空遁地兽":   ["RekSai", "Rek'Sai", "雷克塞", "挖掘机"],
    "镕铁少女":     ["Rell", "芮尔"],
    "炼金男爵":     ["Renata", "Renata Glasc", "烈娜塔"],
    "荒漠屠夫":     ["Renekton", "鳄鱼", "雷克顿"],
    "傲之追猎者":   ["Rengar", "狮子狗", "雷恩加尔"],
    "放逐之刃":     ["Riven", "锐雯", "瑞文"],
    "机械公敌":     ["Rumble", "兰博"],
    "符文法师":     ["Ryze", "瑞兹", "流浪"],
    "沙漠玫瑰":     ["Samira", "莎弥拉"],
    "北地之怒":     ["Sejuani", "猪女", "瑟庄妮"],
    "涤魂圣枪":     ["Senna", "赛娜"],
    "星籁歌姬":     ["Seraphine", "萨勒芬妮"],
    "腕豪":         ["Sett", "瑟提"],
    "恶魔小丑":     ["Shaco", "小丑", "萨科"],
    "暮光之眼":     ["Shen", "慎"],
    "龙血武姬":     ["Shyvana", "龙女", "希瓦娜"],
    "炼金术士":     ["Singed", "辛吉德"],
    "亡灵战神":     ["Sion", "塞恩"],
    "战争女神":     ["Sivir", "轮子妈", "希维尔"],
    "上古领主":     ["Skarner", "斯卡纳", "蝎子"],
    "炽炎雏龙":     ["Smolder", "斯莫德", "小龙"],
    "琴瑟仙女":     ["Sona", "琴女", "娑娜"],
    "众星之子":     ["Soraka", "奶妈", "索拉卡"],
    "诺克萨斯统领": ["Swain", "乌鸦", "斯维因"],
    "暗黑元首":     ["Syndra", "辛德拉"],
    "河流之王":     ["TahmKench", "Tahm Kench", "蛤蟆", "塔姆"],
    "岩雀":         ["Taliyah", "塔莉垭"],
    "刀锋之影":     ["Talon", "泰隆", "男刀"],
    "瓦洛兰之盾":   ["Taric", "塔里克", "宝石"],
    "魂锁典狱长":   ["Thresh", "锤石"],
    "麦林炮手":     ["Tristana", "小炮", "崔丝塔娜"],
    "巨魔之王":     ["Trundle", "巨魔", "特朗德尔"],
    "蛮族之王":     ["Tryndamere", "蛮王", "泰达米尔"],
    "卡牌大师":     ["TwistedFate", "Twisted Fate", "卡牌", "崔斯特", "TF", "tf"],
    "瘟疫之源":     ["Twitch", "老鼠", "图奇"],
    "兽灵行者":     ["Udyr", "乌迪尔"],
    "无畏战车":     ["Urgot", "厄加特", "螃蟹"],
    "邪恶小法师":   ["Veigar", "小法", "维迦"],
    "虚空之眼":     ["Velkoz", "Vel'Koz", "大眼", "维克兹"],
    "愁云使者":     ["Vex", "薇古丝"],
    "皮城执法官":   ["Vi", "蔚"],
    "破败之王":     ["Viego", "佛耶戈"],
    "猩红收割者":   ["Vladimir", "吸血鬼", "弗拉基米尔"],
    "不灭狂雷":     ["Volibear", "狗熊", "沃利贝尔"],
    "祖安怒兽":     ["Warwick", "狼人", "沃里克"],
    "逆羽":         ["Xayah", "霞"],
    "德邦总管":     ["XinZhao", "Xin Zhao", "赵信"],
    "封魔剑魂":     ["Yone", "永恩"],
    "牧魂人":       ["Yorick", "约里克", "掘墓"],
    "不破之誓":     ["Yunara", "芸阿娜"],
    "魔法猫咪":     ["Yuumi", "悠米", "猫"],
    "不落魔锋":     ["Zaahen", "扎亨"],
    "生化魔人":     ["Zac", "扎克", "果冻人"],
    "影流之主":     ["Zed", "劫"],
    "祖安花火":     ["Zeri", "泽丽"],
    "时光守护者":   ["Zilean", "基兰", "时光老头"],
    "暮光星灵":     ["Zoe", "佐伊"],
}


def main():
    # 1. 备份
    os.makedirs(OUT, exist_ok=True)
    bak = os.path.join(OUT, "champions_backup_aliases.json")
    shutil.copy2(DATA, bak)
    print(f"[backup] {DATA} → {bak}")

    # 2. 加载
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 3. 写入别名
    added = 0
    missing = []
    for c in data["champions"]:
        name = c["name"]
        aliases = ALIASES.get(name)
        if aliases:
            c["aliases"] = aliases
            added += 1
        else:
            missing.append(name)

    # 4. 保存
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[done] 已为 {added}/{len(data['champions'])} 位英雄添加别名")
    if missing:
        print(f"[warn] 缺少别名的英雄 ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
