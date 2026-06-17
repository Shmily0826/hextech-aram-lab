import json
d = json.load(open('data/champions.json', 'r', encoding='utf-8'))
checks = ['万花通灵','蒸汽机器人','不祥之刃','圣枪游侠','众星之子',
          '德玛西亚皇子','伊泽瑞尔','卡牌大师','齐天大圣','沙漠死神']
for c in d['champions']:
    if c['name'] in checks:
        print(c['name'], ':', c.get('aliases', []), ' title=', c['title'])
