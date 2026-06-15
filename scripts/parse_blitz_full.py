#!/usr/bin/env python3
"""
Parse blitz.gg ARAM Mayhem augment data from two text files and update
the candidates JSON file.

- File 1 (1.txt): patch update page - new augments + removed augments
- File 2 (2.txt): tier list - prismatic/gold/silver augments with full
  Chinese descriptions

Usage:
    python scripts/parse_blitz_full.py
"""

import json
import sys
import os
import io
import shutil
import re
from collections import OrderedDict
from datetime import datetime

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# =============================================================================
# Configuration
# =============================================================================
PROJECT_ROOT = r"D:\CODE\project\aram-insight"
FILE1_PATH = r"C:\Users\Shmily\OneDrive\Desktop\Temp\1.txt"
FILE2_PATH = r"C:\Users\Shmily\OneDrive\Desktop\Temp\2.txt"
CANDIDATES_PATH = os.path.join(PROJECT_ROOT, "pipeline", "output",
                               "augment_import_candidates.json")
BACKUP_PATH = CANDIDATES_PATH + ".bak"

TIER_ORDER = {"prismatic": 0, "gold": 1, "silver": 2}
BLITZ_URL = "https://blitz.gg/zh-CN/lol/aram-mayhem-augments"

# ---------------------------------------------------------------------------
# Known Chinese-name -> existing-candidate-ID mappings.
# Used when the Chinese name does NOT already appear in the candidates file.
# ---------------------------------------------------------------------------
KNOWN_NAME_TO_ID = {
    # Prismatic
    "飞身踢": "dropkick",
    "你摸不到": "can_t_touch_this",
    "全凭身法": "dashing",
    "回归基本功": "back_to_basics",
    "史上最大雪球": "biggest_snowball_ever",
    "连拨击锤": "fan_the_hammer",
    "歌利亚巨人": "goliath",
    "艾卡西亚的陷落": "icathian_fall",
    "超负荷": "overload",
    "死亡之环": "circle_of_death",
    "三重射击": "triple_shot",
    # Gold
    "星界躯体": "celestial_body",
    "罪恶快感": "get_excited",
    "超强大脑": "big_brain",
    "面包和黄油": "bread_and_butter",
    "不动如山": "impassable",
    "有始有终": "from_beginning_to_end",
    "火上浇油": "firebrand",
    "狂徒豪气": "outlaws_grit",
    "神圣干预": "divine_intervention",
    "心灵净化": "spiritual_purification",
    "回力OK镖": "ok_boomerang",
    "尖端发明家": "apex_inventor",
    "弹球": "pinball",
    "炽烈黎明": "searing_dawn",
    "缩小射线": "shrink_ray",
    "仆从大师": "minionmancer",
    "贪欲束缚": "greedy_grasp",
    "仁慈打击": "merciful_strike",
    "生机迸发": "burst_of_vitality",
    "钢铁之心": "heart_of_steel",
    "藏身草丛": "bush_hide",
    "轻拍背部": "pat_on_the_back",
    "邦！": "bang",
    "冰雪爆裂": "ice_burst",
    "哎哟我的硬币": "ouch_my_coins",
    "喂呜喂呜": "wee_oo_wee_oo",
    "地形专家": "terrain_expert",
    "惊惧": "terror",
    "我们的治疗": "our_healing",
    "无尽大杀四方": "endless_rampage",
    "牙仙子": "tooth_fairy",
    "自然即是治愈": "nature_heals",
    "装填": "reloading",
    "豪猪": "porcupine",
    "鲨鱼暴风": "shark_storm",
    "鲨鱼诱饵": "shark_bait",
    "闪现向前": "flash_forward",
    "会心治疗": "critical_heal",
    "关键暴击": "critical_strike",
    "升级雪球": "upgrade_snowball",
    "双发快射": "double_tap",
    "吸血习性": "vampiric_habit",
    "坚韧": "tenacity_aug",
    "易损": "vulnerable",
    "暴击律动": "critical_rhythm",
    "暴击飞弹": "critical_missile",
    "最终都市列车": "last_city_train",
    "灵魂虹吸": "soul_siphon_new",
    "全心全意": "all_for_you",
    "活力焕发": "vitality_burst",
    "升级耀光": "upgrade_sheen",
    "炽燃利息": "combusting_interest",
    "钢化你心": "quest_steel_your_heart",
    # Silver
    "大力": "blunt_force",
    "灵巧": "deft",
    "渴血": "goredrink",
    "侵蚀": "erosion",
    "家园卫士": "homeguard",
    "急救用具": "first_aid_kit",
    "俯冲轰炸": "dive_bomber",
    "唯快不破": "don_t_blink",
    "碰不到我": "untouchable",
    "双生火焰": "twin_fire",
    "台风": "typhoon",
    "叠角龙": "stackasaurus",
    "快中求稳": "swift_and_safe",
    "山脉龙魂": "mountain_soul",
    "旋转至胜": "spin_to_win",
    "防护面纱": "veil_of_protection",
    "下雪天": "snow_day",
    "主玩辅助": "support_main",
    "别停止引导": "don_t_stop_channeling",
    "加固护盾": "reinforced_shield",
    "双重打击": "double_strike",
    "可靠武器": "reliable_weapon",
    "大师铸就": "master_crafted",
    "自适应防护": "adaptive_defense",
    "保持坚定": "stay_firm",
    "前进时间到": "time_to_advance",
    "坚若磐石": "solid_as_rock",
    "狂热者": "zealot",
    "由暴生急": "haste_from_crit",
    "升级收集者": "upgrade_collector",
    "升级中娅": "upgrade_zhonyas",
    "升级献祭": "upgrade_immolate",
    # Additional mappings for entries with bad auto-generated pinyin IDs
    "邦！": "bang",
    "复位": "reset_position",
    "过量延伸者": "overextender",
    "海牛阿福的勇士": "quest_urfs_champion",
    "会心防御": "critical_defense",
    "沃格勒特的巫师帽": "quest_wooglets_witchcap",
    "全心为你": "all_for_you",
    "终极刷新": "ultimate_revolution",
    "质变黄金阶": "transmute_gold",
}

# ---------------------------------------------------------------------------
# Aliases: alternate Chinese names that should match existing candidates.
# Used when the blitz.gg name differs slightly from the stored name.
# ---------------------------------------------------------------------------
ALIASES = {
    # Tier list uses shorter name without "任务：" prefix
    "沃格勒特的巫师帽": "任务：沃格勒特的巫师帽",
    # Slightly different character(s)
    "终极刷新": "终极刷",
    "海牛阿福的勇士": "任务：海牛阿福的勇士",
    "钢化你心": "任务：钢化你心",
    # blitz.gg uses different Chinese translation
    "炽燃利息": "燃烧利息",
    # Prefix variant
    "升级雪球": "升级：雪球",
}

# ---------------------------------------------------------------------------
# Minimal pinyin lookup table (covers chars found in augment names)
# ---------------------------------------------------------------------------
PINYIN_MAP = {}

_PINYIN_RAW = """
a 阿啊
ai 哎爱矮哀
an 安暗按案岸
ang 昂
ao 奥熬傲
ba 八把吧拔霸
bai 百白败拜
ban 半办般搬板版扮
bang 邦帮绑棒傍磅
bao 宝报暴抱爆剥堡饱
bei 北被背悲备碑辈
ben 本奔笨
beng 蹦崩绷
bi 比必笔避壁鼻碧闭秘臂蔽
bian 变边便遍辨编鞭
biao 表标
bie 别
bin 宾滨
bing 兵冰病并丙
bo 波博播伯拨薄
bu 不步布部补捕
ca 擦
cai 才菜财猜裁采彩
can 参残灿惨餐
cang 藏仓苍
cao 操草曹
ce 册策测侧
ceng 层曾
cha 查差插叉茶察
chai 拆
chan 产缠铲颤
chang 长常场唱尝畅昌
chao 超朝潮吵抄炒
che 车彻撤
chen 陈沉晨臣称趁
cheng 成城程承诚盛乘撑
chi 吃持尺迟池翅齿耻斥
chong 冲充虫崇宠
chou 抽仇筹愁稠丑
chu 出处初除楚础畜触储矗
chua
chuai 揣
chuan 传穿船喘串
chuang 窗床创闯
chui 吹垂炊锤
chun 春纯唇蠢
chuo 戳绰
ci 此次刺词瓷辞慈
cong 从聪丛匆
cou 凑
cu 粗促醋簇
cuan 窜攒
cui 催脆翠摧萃
cun 村存寸
cuo 错措挫搓
da 大打达答搭
dai 大带代待袋戴呆逮
dan 但单担弹淡蛋胆旦诞
dang 当挡党档荡
dao 到道倒刀导岛蹈盗稻悼
de 的得德
dei 得
deng 等灯登邓瞪
di 地的底低敌迪抵帝滴堤涤
dian 点电店典垫殿淀碘
diao 掉调吊钓雕
die 跌叠碟蝶爹
ding 定顶丁盯钉订鼎
diu 丢
dong 东动冬洞懂冻栋侗
dou 都斗抖陡豆逗兜
du 度读独毒堵杜肚渡妒督
duan 段短断锻缎端
dui 对队堆兑
dun 顿盾蹲敦墩炖
duo 多夺朵躲剁舵堕惰
e 恶额鹅饿恩俄扼鄂
en 恩嗯
er 二而耳儿饵尔
fa 发法罚伐阀筏
fan 反翻犯饭番凡繁范贩
fang 方放房防仿访纺芳
fei 非飞费肥废沸肺
fen 分份粉奋愤纷坟焚 fen
feng 风封丰疯峰锋蜂逢缝冯讽奉凤
fo 佛
fou 否
fu 服夫附负富副福府俯斧浮腐抚辅赋复覆伏俘佛拂敷肤孵缚
ga 嘎咖
gai 该改盖概溉
gan 干感赶敢甘肝杆柑竿
gang 刚钢港岗纲杠
gao 高告搞糕稿膏
ge 个各歌哥割革隔格阁葛搁鸽疙
gei 给
gen 根跟
geng 更耕梗
gong 工公功共攻供宫弓恭巩贡
gou 够狗沟构勾钩购苟
gu 古骨鼓固故顾估姑孤菇辜 gou
gua 瓜刮挂寡卦
guai 怪乖拐
guan 关管馆惯灌贯冠观官棺
guang 光广逛
gui 贵归规鬼桂跪柜瑰硅龟
gun 滚棍
guo 国过果裹锅郭
ha 哈蛤
hai 还海孩害嗨骸
han 汉寒含喊旱韩汗罕悍捍焊憾
hang 行航杭巷
hao 好号豪毫耗浩壕
he 和河合何荷核贺赫喝鹤盒
hei 黑嘿
hen 很狠恨痕
heng 横衡恒哼亨
hong 红宏洪鸿轰虹哄弘
hou 后厚侯候猴吼喉
hu 湖护户呼胡虎互忽壶糊蝴狐弧唬
hua 花话化华划画哗滑猾
huai 坏怀淮槐
huan 还换欢环幻患唤焕涣宦
huang 黄皇荒慌煌晃恍幌谎惶
hui 会回灰汇挥辉毁慧恢惠贿晦讳
hun 混魂昏婚浑荤
huo 活火货或获惑霍祸伙
ji 机几及急级极即既记技际季纪击积基绩激吉集疾棘急己济继寂计寄迹际祭绩羁肌饥讥鸡畸稽
jia 家加价假甲嫁佳架驾稼歼夹颊
jian 见间件建坚检简箭健减渐剑肩舰荐贱践煎监兼茧拣捡俭碱硷
jiang 将江奖讲降酱疆姜僵强匠浆蒋
jiao 叫教较角脚觉浇骄焦胶搅郊绞矫剿酵窖椒礁焦
jie 接街结截解姐介借届戒揭杰竭洁劫捷睫桔拮
jin 进近今金紧尽仅禁锦筋劲晋浸巾斤筋靳
jing 经精京惊景警静净竞敬竟镜径痉茎靖晶鲸
jiong 窘炯
jiu 就九久旧酒救纠揪究韭灸玖
ju 举具句巨聚拒距剧据惧拘矩驹菊局咀沮咀
juan 卷捐圈倦绢眷
jue 决绝觉掘崛爵抉诀
jun 军均君俊骏峻竣浚
ka 卡咖喀咯
kai 开凯慨楷揩
kan 看砍刊堪勘坎坎坎
kang 抗扛炕亢康慷糠
kao 考靠烤拷
ke 可克课科壳渴客刻棵颗咳柯苛珂恪
ken 肯啃垦恳坑
keng 坑吭铿
kong 空孔控恐倥
kou 口扣寇抠叩
ku 苦哭库酷裤窟
kua 夸跨垮挎胯
kuai 快块会筷侩
kuan 宽款
kuang 况矿狂框筐眶旷诓
kui 亏愧溃馈窥葵魁盔傀
kun 困昆捆坤
kuo 扩括阔廓
la 拉啦辣蜡腊喇垃
lai 来赖莱睐
lan 蓝兰拦栏懒烂滥岚
lang 浪朗狼廊郎琅榔
lao 老劳牢捞烙佬姥潦酪落
le 了乐勒肋
lei 类雷累泪擂蕾肋垒磊儡
leng 冷愣棱楞
li 里力理利立离历例丽厉励李礼隶梨栗粒沥雳莉俐莉篱
lia 俩
lian 连联练脸恋炼链帘敛莲涟镰
liang 两亮量凉粮梁梁晾谅辆靓
liao 了料聊辽疗燎潦寥廖镣撩
lie 列烈裂猎劣
lin 林临邻淋磷凛吝赁鳞拎
ling 令零领灵岭铃龄凌陵陵凌溜菱棱
liu 六流留刘柳溜硫瘤琉榴
long 龙隆笼聋垄拢陇弄
lou 楼漏露陋搂篓
lu 路陆露录鹿炉碌禄绿虏鲁卤鲁碌赂潞麓
lv 绿律率旅虑铝侣屡缕滤氯驴
luan 乱卵峦滦
lue 略掠
lun 论轮伦沦纶仑
luo 落罗裸络洛骆螺锣萝螺骆
ma 妈吗马骂嘛麻码玛蚂吗么
mai 买卖迈麦埋脉
man 满慢漫蛮馒蔓曼瞒谩
mang 忙盲茫芒莽氓
mao 毛猫矛冒贸帽貌锚铆茂茅
me 么
mei 没每美妹媒梅枚眉煤霉酶魅
men 门们闷
meng 猛蒙盟梦萌孟锰朦檬
mi 米密蜜迷秘眯觅幂
mian 面免棉眠绵冕缅沔勉
miao 妙秒苗描瞄庙渺缈藐
mie 灭蔑
min 民敏闽皿悯抿泯
ming 明名命鸣铭冥茗溟
miu 谬缪
mo 末没磨模漠莫魔墨默摩脉抹寞蘑莫脉陌
mou 某谋牟眸缪
mu 目木牧幕墓慕暮穆牡母姆拇募
na 那拿哪呐娜钠纳捺
nai 奶耐乃奈萘
nan 南男难楠喃
nang 囊
nao 脑闹恼挠淖
ne 呢
nei 内馁
nen 嫩
neng 能
ni 你泥逆拟腻尼匿昵
nian 年念粘碾撵拈蔫
niang 娘酿
niao 鸟尿
nie 捏涅镊啮镍孽
nin 您
ning 宁凝柠拧泞
niu 牛扭纽钮拗
nong 农浓弄脓
nu 努怒奴弩
nv 女衄
nuan 暖
nuo 诺挪懦糯
o 哦噢
ou 欧偶呕殴鸥藕
pa 怕爬帕趴琶耙
pai 排拍派牌迫徘
pan 盘判叛盼攀潘畔
pang 旁胖庞乓乓 pang
pao 跑炮泡抛刨咆
pei 配陪赔培佩沛裴呸
pen 盆喷
peng 碰朋棚蓬膨捧烹膨鹏篷
pi 批皮匹劈劈霹脾疲琵啤辟屁譬癖僻
pian 片偏篇骗翩
piao 票漂飘瓢
pie 撇瞥
pin 品拼频贫聘
ping 平评瓶凭屏萍苹坪
po 破迫坡泼颇婆魄泊粕
pu 普铺扑朴仆浦蒲脯葡谱瀑曝
qi 起其七气期奇齐器骑旗棋崎歧泣企启契砌漆汲戚沏缉
qia 恰掐卡洽
qian 前千钱签浅牵铅迁谦潜遣嵌欠纤歉
qiang 强枪墙抢呛腔羌
qiao 桥巧悄敲俏壳翘撬鞘锹
qie 切且窃茄怯挈
qin 亲琴勤侵秦沁擒寝芹
qing 清请情轻青倾庆晴擎卿氰顷
qiong 穷琼穹
qiu 求球秋丘邱囚仇泅
qu 去取区趣曲屈驱渠趋蛆龋
quan 全权劝拳泉圈券犬
que 却确缺雀瘸鹊阙
qun 群裙
ran 然燃染冉苒
rang 让嚷壤攘
rao 绕扰饶娆
re 热惹
ren 人认任忍仁韧刃纫壬
reng 仍扔
ri 日
rong 容融荣溶熔绒蓉戎冗
rou 肉柔揉糅蹂
ru 如入乳儒辱褥汝蠕
ruan 软阮
rui 瑞锐蕊睿
run 润闰
ruo 若弱
sa 撒洒萨飒
sai 赛塞腮鳃
san 三散伞
sang 嗓丧桑
sao 扫嫂骚搔
se 色涩瑟啬铯
sen 森
seng 僧
sha 杀沙傻啥砂纱刹莎煞
shai 筛晒色
shan 山闪善衫扇珊煽擅膳栅
shang 上商伤赏尚裳
shao 少绍烧稍哨勺韶邵芍
she 社设射舍涉蛇奢赊赦慑摄
shei 谁
shen 深什身神审伸慎参甚肾沈渗绅呻
sheng 生声省胜圣升剩盛牲绳甥
shi 是十时使事世实始石市示式识势史师士氏释饰视试适室诗施食拾矢蚀嗜逝
shou 手受首守收寿售兽瘦授狩
shu 数书术树束属述熟署鼠薯曙蜀黍漱恕刷耍摔甩帅率栓拴霜爽双水谁税睡顺说硕朔丝司私思斯撕嘶死四寺似嗣肆送宋颂诵搜艘擞嗽苏诉肃酸蒜算虽隋髓碎穗随岁遂孙损笋蓑梭缩琐索锁所
ta 他她它塔踏拓蹋
tai 太台态抬泰胎苔
tan 谈弹潭坦摊贪瘫滩坛檀痰毯探碳叹
tang 堂糖汤躺趟烫塘搪唐膛棠
tao 套逃桃讨陶淘萄陶
te 特
teng 疼腾藤
ti 体提题替踢梯剔蹄啼涕剃
tian 天田甜添填恬舔
tiao 条跳挑调窕
tie 铁贴帖
ting 听停挺庭厅亭廷艇汀
tong 同通统痛桶筒铜童捅佟
tou 头投透偷
tu 土图突吐涂兔秃途屠
tuan 团湍
tui 推退褪蜕
tun 吞屯囤臀
tuo 脱拖托驮驼妥椭拓唾
wa 挖瓦蛙洼袜哇娃
wai 外歪掰
wan 万完晚碗湾玩顽挽丸惋婉腕
wang 王网往望忘旺汪亡枉妄
wei 为位未围味微危委威维谓卫慰畏巍蔚魏纬潍
wen 问文温闻纹稳吻瘟紊
weng 翁嗡瓮
wo 我握窝卧蜗涡斡渥
wu 五物无午务武雾屋吴误悟侮戊污钨呜巫呜忤妩
xi 西系细席息希析洗袭喜戏锡熄膝夕吸悉惜稀熙锡蜥昔析淅溪汐僖腊嬉檄觋习媳隙
xia 下吓夏瞎峡侠狭霞匣辖暇
xian 先现线显限鲜险仙献县咸贤衔嫌掀纤涎舷
xiang 想向象相像响香乡享详降箱翔橡项巷
xiao 小笑消校效削晓孝啸霄肖宵淆骁
xie 写些谢鞋协血斜卸泄蟹懈挟亵榭屑携楔偕谐
xin 新心信芯欣辛锌薪衅
xing 行形性星型兴姓幸杏醒腥刑
xiong 兄胸熊雄凶匈汹
xiu 修秀休绣锈袖嗅朽羞朽袖
xu 需须许续虚序绪蓄叙恤旭酗畜絮婿栩煦
xuan 选宣旋玄悬眩绚癣炫
xue 学雪血穴靴薛削
xun 训寻巡迅讯殉逊熏荀询循驯浔
ya 压呀牙芽崖哑亚雅咽鸭讶丫
yan 眼言烟严沿演盐验岩延掩燕厌咽艳雁焰宴谚堰砚彦唁彦
yang 样阳养洋央仰痒氧殃秧扬杨疡佯
yao 要药腰遥咬摇耀妖窑谣瑶尧姚钥
ye 也业夜叶野页液爷咽掖噎曳
yi 一以已意义亿艺忆仪议移异易益衣依医疑遗宜椅蚁倚矣抑疫役翼译绎逸壹揖姨沂颐
yin 因引银印音阴饮隐姻吟吟殷淫 Yin 寅
ying 应影英营迎硬映鹰赢盈颖樱婴缨莹萤蝇荧荧
yo 哟
yong 用永勇涌咏泳拥佣臃痈庸雍踊恿蛹
you 又有右友由游尤犹油邮优幽悠忧尤由酉佑釉诱
yu 与于鱼雨语遇玉域育欲预御裕喻愈芋郁誉驭驭浴寓吁宇羽舆禹虞愚娱瑜虞舆屿
yuan 远原院元园员圆源缘愿冤渊猿鸳辕苑媛
yue 月越约乐阅跃悦岳粤钥曰
yun 运云允孕蕴酝晕韵蕴愠
za 杂砸咋
zai 在再载灾宰栽哉仔
zan 咱暂赞攒簪
zang 脏葬赃臧
zao 早造遭糟枣燥凿躁澡噪灶皂
ze 则责择泽仄啧
zei 贼
zen 怎
zeng 增曾赠憎
zha 扎炸榨炸摘渣眨栅乍诈乍轧札
zhai 宅窄债摘斋
zhan 战站占展沾盏斩辗崭詹瞻毡粘蘸
zhang 长张章掌涨障丈帐胀杖彰漳幛嶂瘴
zhao 找照赵招着兆罩爪诏棹
zhe 这者着折哲遮浙辙锗褶
zhei 这
zhen 真阵镇震振诊枕珍斟甄臻贞侦帧
zheng 正整政争证征挣症蒸睁郑筝
zhi 之只知直至值纸指志制治质置职植殖止址趾旨脂汁蜘织侄挚掷帜峙滞制智秩稚掷炙痔窒
zhong 中重种众终钟忠仲肿仲舟州洲粥周轴肘帚咒宙昼骤皱骤
zhou 周洲州舟轴肘帚咒宙昼骤皱
zhu 主住注柱祝著驻猪竹逐诸朱珠株蛛铸筑蛀贮驻
zhua 抓爪
zhuai 拽
zhuan 专转赚砖撰篆馔
zhuang 装撞壮状庄桩
zhui 追坠缀赘锥椎
zhun 准谆
zhuo 着桌捉灼拙卓琢茁拙灼涿
zi 自子字紫资仔籽滋咨姿孜兹瓷淄
zong 总宗综纵踪棕粽
zou 走奏揍邹
zu 族组足阻租祖钻
zuan 钻攥
zui 最嘴罪醉
zun 尊遵撙
zuo 做作坐座左昨佐琢撮
"""

for _line in _PINYIN_RAW.strip().split("\n"):
    _line = _line.strip()
    if not _line:
        continue
    _parts = _line.split(" ", 1)
    if len(_parts) != 2:
        continue
    _py, _chars = _parts[0].strip().lower(), _parts[1].strip()
    for _ch in _chars:
        PINYIN_MAP[_ch] = _py


# =============================================================================
# Pinyin helper
# =============================================================================
def chinese_to_id(name: str) -> str:
    """Convert a Chinese name to a slug-style ID via pinyin lookup."""
    parts = []
    for ch in name:
        if ch in PINYIN_MAP:
            parts.append(PINYIN_MAP[ch])
        elif ch.isascii() and ch.isalnum():
            parts.append(ch.lower())
        elif ch in (" ", "-", "_"):
            parts.append("_")
        else:
            # Use ordinal as last resort
            parts.append(f"x{ord(ch):04x}")
    raw = "_".join(parts)
    # Collapse underscores and clean
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw


def normalize_key(text: str) -> str:
    """Normalize Chinese text for fuzzy matching."""
    text = text.strip()
    # Remove common punctuation and brackets
    text = re.sub(r"[，。！？、；：\u201c\u201d\u2018\u2019【】《》（）\s\-.:!?\[\]()'\"\xb7]",
                  "", text)
    return text.lower()


# =============================================================================
# File parsers
# =============================================================================
def parse_tier_list(filepath: str) -> dict:
    """
    Parse file 2 (tier list).
    Returns: {tier: [(chinese_name, chinese_description), ...]}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    result = {"prismatic": [], "gold": [], "silver": []}
    current_tier = None
    current_name = None
    current_desc_lines = []
    had_blank = False

    def save_entry():
        nonlocal current_name, current_desc_lines
        if current_name and current_tier:
            desc = "".join(current_desc_lines).strip()
            if desc and current_name not in ("新", "已移除"):
                result[current_tier].append((current_name, desc))
        current_name = None
        current_desc_lines = []

    for line in lines:
        stripped = line.strip()

        # Stop at footer
        if stripped == "公司":
            save_entry()
            break

        # Tier header detection (also resets state)
        if "棱彩" in stripped and "强化符文" in stripped and "ARAM" in stripped:
            save_entry()
            current_tier = "prismatic"
            current_name = None
            current_desc_lines = []
            had_blank = False
            continue
        if "黄金" in stripped and "强化符文" in stripped and "ARAM" in stripped:
            save_entry()
            current_tier = "gold"
            current_name = None
            current_desc_lines = []
            had_blank = False
            continue
        if "白银" in stripped and "强化符文" in stripped and "ARAM" in stripped:
            save_entry()
            current_tier = "silver"
            current_name = None
            current_desc_lines = []
            had_blank = False
            continue

        if current_tier is None:
            continue

        # Blank line -> save previous entry, next line starts new entry
        if not stripped:
            save_entry()
            had_blank = True
            continue

        # Skip lines before the first blank line in each section (intro text)
        if not had_blank:
            continue

        # First non-blank line after blank -> name
        if current_name is None:
            current_name = stripped
            current_desc_lines = []
        else:
            current_desc_lines.append(stripped)

    # Don't forget last entry
    save_entry()
    return result


def parse_update_page(filepath: str):
    """
    Parse file 1 (update page).
    Returns: (new_augments, removed_augments)
        Each is a list of (chinese_name, chinese_description).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_augments = []
    removed_augments = []
    section = "new"  # starts as "new", switches to "removed"
    current_name = None
    current_desc_lines = []
    had_blank = False

    def save_entry():
        nonlocal current_name, current_desc_lines
        if current_name and current_name not in ("新", "已移除", "？？？"):
            desc = "".join(current_desc_lines).strip()
            # Clean trailing "新" or "已移除" from description
            desc = re.sub(r"[\s]*新$", "", desc)
            desc = re.sub(r"[\s]*已移除$", "", desc)
            entry = (current_name, desc)
            if section == "new":
                new_augments.append(entry)
            else:
                removed_augments.append(entry)
        current_name = None
        current_desc_lines = []

    for line in lines:
        stripped = line.strip()

        # Detect section switch
        if "已移除" in stripped and "强化符文" in stripped:
            save_entry()
            section = "removed"
            current_name = None
            current_desc_lines = []
            had_blank = False
            continue

        # Stop at footer
        if stripped == "公司":
            save_entry()
            break

        # Skip everything before the data starts
        # Look for the first section intro
        if section == "new" and not had_blank and current_name is None:
            if not stripped:
                had_blank = True
            # Skip intro lines until first blank line that precedes data
            # But we need to detect the actual data start.
            # The data starts at line ~34 (0-indexed 33).
            # Before that: nav, intro, download button, header, description.
            # The pattern: there are several blank lines in the intro.
            # We use a heuristic: if the line contains "新增" and "强化符文"
            # or "列表", the next blank line starts data.
            continue

        # Actually, let me simplify: just use blank-line logic from the start
        # of the file, and filter out noise entries.
        if not stripped:
            save_entry()
            had_blank = True
            continue

        if not had_blank:
            continue

        if current_name is None:
            current_name = stripped
            current_desc_lines = []
        else:
            current_desc_lines.append(stripped)

    save_entry()
    return new_augments, removed_augments


# =============================================================================
# Alternative parser for file 1 that handles the intro section better
# =============================================================================
def parse_update_page_v2(filepath: str):
    """
    Parse file 1 more robustly.  We know:
      - Lines 34-282 (1-indexed): NEW augments
      - Lines 284-477 (1-indexed): REMOVED augments
    But we parse by content rather than hard-coded line numbers.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Find the line that says "新增 ARAM 大乱斗强化符文" or similar
    new_start = None
    removed_start = None
    footer_start = len(lines)

    for i, line in enumerate(lines):
        s = line.strip()
        if "新增" in s and "强化符文" in s and new_start is None:
            new_start = i
        if "已移除" in s and "强化符文" in s and removed_start is None:
            removed_start = i
        if s == "公司" and footer_start == len(lines):
            footer_start = i

    if new_start is None:
        new_start = 0
    if removed_start is None:
        removed_start = len(lines)

    # Markers that appear standalone between entries in file 1.
    # They must NOT be treated as entry names; instead they signal
    # "save current entry and start fresh".
    SKIP_MARKERS = {"新", "已移除", "？？？"}

    def extract_entries(start, end):
        """Extract (name, desc) entries from a line range."""
        entries = []
        name = None
        desc_lines = []
        after_blank = False

        def save():
            nonlocal name, desc_lines
            if name and name not in SKIP_MARKERS:
                desc = "".join(desc_lines).strip()
                # Clean trailing marker words from description
                desc = re.sub(r"[\s]*新$", "", desc)
                desc = re.sub(r"[\s]*已移除$", "", desc)
                entries.append((name, desc))
            name = None
            desc_lines = []

        for i in range(start, min(end, len(lines))):
            s = lines[i].strip()
            if not s:
                save()
                after_blank = True
                continue
            # Skip intro lines (before first blank line in section)
            if not after_blank:
                continue

            # --- KEY FIX ---
            # If this line is a standalone marker ("新", "已移除", "？？？"),
            # save any current entry and reset so the NEXT line becomes a name.
            if s in SKIP_MARKERS:
                save()
                continue

            if name is None:
                name = s
                desc_lines = []
            else:
                desc_lines.append(s)

        save()
        return entries

    new_entries = extract_entries(new_start, removed_start)
    removed_entries = extract_entries(removed_start, footer_start)

    return new_entries, removed_entries


# =============================================================================
# Main logic
# =============================================================================
def main():
    print("=" * 70)
    print("  Blitz.gg ARAM Mayhem Augment Data Parser")
    print("=" * 70)
    print()

    # ------------------------------------------------------------------
    # Step 1: Parse file 2 (tier list)
    # ------------------------------------------------------------------
    print("[1/6] Parsing tier list (file 2)...")
    tier_data = parse_tier_list(FILE2_PATH)
    for tier, entries in tier_data.items():
        print(f"  {tier:>12}: {len(entries)} augments")
    total_tier = sum(len(v) for v in tier_data.values())
    print(f"  {'total':>12}: {total_tier}")
    print()

    # ------------------------------------------------------------------
    # Step 2: Parse file 1 (update page)
    # ------------------------------------------------------------------
    print("[2/6] Parsing update page (file 1)...")
    new_augments, removed_augments = parse_update_page_v2(FILE1_PATH)
    print(f"  New augments:     {len(new_augments)}")
    print(f"  Removed augments: {len(removed_augments)}")
    print()

    # ------------------------------------------------------------------
    # Step 3: Build lookup structures
    # ------------------------------------------------------------------
    print("[3/6] Building lookup structures...")

    # Build blitz_name -> {desc, tier} from tier list (file 2)
    blitz_by_name = {}
    for tier, entries in tier_data.items():
        for cn_name, cn_desc in entries:
            norm = normalize_key(cn_name)
            blitz_by_name[norm] = {
                "name": cn_name,
                "description": cn_desc,
                "tier": tier,
            }

    # Also add new augments from file 1 (if not already in tier list)
    new_from_file1 = {}
    for cn_name, cn_desc in new_augments:
        norm = normalize_key(cn_name)
        if norm not in blitz_by_name:
            new_from_file1[norm] = {
                "name": cn_name,
                "description": cn_desc,
                "tier": None,  # tier unknown
            }

    # Build removed set
    removed_norm_names = set()
    for cn_name, _ in removed_augments:
        removed_norm_names.add(normalize_key(cn_name))

    # ------------------------------------------------------------------
    # Step 4: Read existing candidates and build lookup
    # ------------------------------------------------------------------
    print("[4/6] Loading existing candidates...")

    # Backup
    if os.path.exists(CANDIDATES_PATH):
        shutil.copy2(CANDIDATES_PATH, BACKUP_PATH)
        print(f"  Backup saved to: {BACKUP_PATH}")

    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"  Loaded {len(candidates)} existing candidates")

    # Build name -> index lookup
    name_to_idx = {}
    norm_to_idx = {}
    for idx, c in enumerate(candidates):
        cn = c.get("name", "")
        if cn:
            name_to_idx[cn] = idx
            norm_to_idx[normalize_key(cn)] = idx

    # Add alias mappings so variant names resolve to the same candidate
    alias_norm_to_idx = {}
    for alias_name, canonical_name in ALIASES.items():
        canon_norm = normalize_key(canonical_name)
        if canon_norm in norm_to_idx:
            alias_norm_to_idx[normalize_key(alias_name)] = norm_to_idx[canon_norm]

    def resolve_idx(norm_name):
        """Look up candidate index by normalized name, with alias fallback."""
        idx = norm_to_idx.get(norm_name)
        if idx is None:
            idx = alias_norm_to_idx.get(norm_name)
        return idx

    # Also build id -> index
    id_to_idx = {c["id"]: i for i, c in enumerate(candidates)}

    # ------------------------------------------------------------------
    # Step 5: Match and update
    # ------------------------------------------------------------------
    print("[5/6] Matching and updating...")

    updated_count = 0
    updated_ids = []
    skipped_removed = []
    name_corrected = 0

    # 5a. Update existing candidates from tier list (file 2)
    for tier, entries in tier_data.items():
        for cn_name, cn_desc in entries:
            norm = normalize_key(cn_name)
            idx = resolve_idx(norm)
            if idx is not None:
                c = candidates[idx]
                old_effect = c.get("effect", "")
                # Update effect if current is empty or we have better data
                if cn_desc and cn_desc != old_effect:
                    c["effect"] = cn_desc
                    c["_source_blitz"] = True
                    if c.get("source", {}).get("type") != "blitz_gg":
                        c["source"] = {"type": "blitz_gg", "url": BLITZ_URL}
                    updated_count += 1
                    updated_ids.append(c["id"])
                # Also correct Chinese name if blitz uses a different form
                if cn_name != c.get("name", ""):
                    # Store the blitz name as an alias field
                    c["_blitz_name"] = cn_name
                    name_corrected += 1

    # 5b. Also try to update existing candidates from file 1 new augments
    for cn_name, cn_desc in new_augments:
        norm = normalize_key(cn_name)
        idx = resolve_idx(norm)
        if idx is not None:
            c = candidates[idx]
            old_effect = c.get("effect", "")
            if cn_desc and not old_effect:
                c["effect"] = cn_desc
                c["_source_blitz"] = True
                updated_count += 1
                updated_ids.append(c["id"])

    # 5c. Mark removed augments
    for cn_name, cn_desc in removed_augments:
        norm = normalize_key(cn_name)
        idx = resolve_idx(norm)
        if idx is not None:
            c = candidates[idx]
            c["_removed_in_patch"] = True
            skipped_removed.append(c["id"])

    # ------------------------------------------------------------------
    # Step 6: Add new candidates
    # ------------------------------------------------------------------
    added_count = 0
    added_ids = []
    existing_ids_set = {c["id"] for c in candidates}
    # Include alias norms so we don't re-add entries matched via alias
    existing_norms_set = set(norm_to_idx.keys()) | set(alias_norm_to_idx.keys())

    # Determine which new augments to add
    all_new_blitz = []  # (cn_name, cn_desc, tier)

    # From tier list (file 2): entries not in existing candidates
    for tier, entries in tier_data.items():
        for cn_name, cn_desc in entries:
            norm = normalize_key(cn_name)
            if norm not in existing_norms_set:
                all_new_blitz.append((cn_name, cn_desc, tier))

    # From file 1 new augments: entries not in tier list and not in existing
    for cn_name, cn_desc in new_augments:
        norm = normalize_key(cn_name)
        if norm not in existing_norms_set:
            # Check if already covered by tier list entry
            already_in_new = any(
                normalize_key(n) == norm for n, _, _ in all_new_blitz
            )
            if not already_in_new:
                all_new_blitz.append((cn_name, cn_desc, None))

    # Build normalized known-name-to-ID lookup
    KNOWN_NORM_TO_ID = {}
    for raw_name, cid in KNOWN_NAME_TO_ID.items():
        KNOWN_NORM_TO_ID[normalize_key(raw_name)] = cid

    # Generate new candidate entries
    for cn_name, cn_desc, tier in all_new_blitz:
        norm = normalize_key(cn_name)

        # Determine ID
        known_id = KNOWN_NORM_TO_ID.get(norm)
        if known_id:
            entry_id = known_id
        else:
            entry_id = chinese_to_id(cn_name)

        # Avoid duplicates
        if entry_id in existing_ids_set:
            # ID collision; try with tier suffix
            alt_id = f"{entry_id}_{tier}" if tier else None
            if alt_id and alt_id not in existing_ids_set:
                entry_id = alt_id
            else:
                # Skip if we can't create a unique ID
                continue

        new_candidate = {
            "id": entry_id,
            "name": cn_name,
            "name_en": "",
            "tier": tier or "unknown",
            "status": "active",
            "effect": cn_desc,
            "effect_en": "",
            "source_status": "import_candidate",
            "source": {
                "type": "blitz_gg",
                "url": BLITZ_URL,
            },
            "_source_blitz": True,
            "_newly_added": True,
        }

        candidates.append(new_candidate)
        existing_ids_set.add(entry_id)
        existing_norms_set.add(norm)
        added_count += 1
        added_ids.append(entry_id)

    # ------------------------------------------------------------------
    # Step 7: Sort and write
    # ------------------------------------------------------------------
    print("[6/6] Sorting and writing output...")

    # Sort: by tier (prismatic > gold > silver > unknown), then by id
    def sort_key(c):
        t = TIER_ORDER.get(c.get("tier", "unknown"), 99)
        return (t, c.get("id", ""))

    candidates.sort(key=sort_key)

    # Rebuild clean output (preserve all existing fields)
    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"  Written to: {CANDIDATES_PATH}")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Existing candidates updated: {updated_count}")
    print(f"  New candidates added:        {added_count}")
    print(f"  Removed augments flagged:    {len(skipped_removed)}")
    print(f"  Total candidates now:        {len(candidates)}")
    print()

    # Tier breakdown
    tier_counts = {}
    for c in candidates:
        t = c.get("tier", "unknown")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print("  Tier breakdown:")
    for t in ("prismatic", "gold", "silver", "unknown"):
        if t in tier_counts:
            print(f"    {t:>12}: {tier_counts[t]}")
    print()

    # Detail: updated IDs
    if updated_ids:
        print(f"  Updated IDs ({len(updated_ids)}):")
        for uid in sorted(set(updated_ids)):
            print(f"    - {uid}")
        print()

    # Detail: added IDs
    if added_ids:
        print(f"  Added IDs ({len(added_ids)}):")
        for aid in sorted(added_ids):
            # Find the candidate to show name
            for c in candidates:
                if c["id"] == aid:
                    print(f"    + {aid} ({c['name']}, {c.get('tier', '?')})")
                    break
        print()

    # Detail: removed IDs
    if skipped_removed:
        print(f"  Removed/flagged IDs ({len(skipped_removed)}):")
        for rid in sorted(skipped_removed):
            print(f"    x {rid}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
