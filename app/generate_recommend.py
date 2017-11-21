#!/usr/bin/env python

'''
    向数据库添加游戏推荐表
'''

from math import sqrt
from .models import Score, Game, Recommend
from . import db

def sim_distance(gameid_1, gameid_2):
    '''返回game1、game2基于距离的相似度评价'''
    si = {}

    def transform(game):
        '''将模型对象转换为字典'''
        result = {}
        for item in game:
            result[item.user_id] = item.score
        return result

    game_1 = Score.query.filter_by(game_id = gameid_1).all()
    score_1 = transform(game_1)
    game_2 = Score.query.filter_by(game_id = gameid_2).all()
    score_2 = transform(game_2)

    for user in score_1:
        if user in score_2:
            si[user] = 1

    # 如果没有共同之处，则返回0
    if len(si) == 0: return 0

    # 计算所有差值的平方和
    sum_of_sequence = sum([pow(score_1[user] - score_2[user], 2) 
                            for user in score_1 if user in score_2])

    # 返回相似度评价
    return 1/(1 + sqrt(sum_of_sequence))


def top_match(gameid):
    '''返回最最相近的3款游戏'''
    t = []
    scores = Score.query.all()
    # 找到所有被评价过的游戏id
    for game in scores:
        i = game.game_id
        if i in t: continue
        t.append(i)
    # 判断游戏是否被评分
    if gameid not in t: 
        return None

    rank = [(sim_distance(gameid, other), other) for other in t if other != gameid]

    rank.sort()
    rank.reverse()
    return rank[0:3]

def insert_similar_items():
    '''为数据库添加推荐表，定期生成即可'''
    # 查找所有的游戏
    items = Game.query.all()
    for item in items:
        # 生成最相近的三个游戏
        sim = top_match(item.id)
        if sim:
            for i in sim:
                recommend = Recommend(prim_game_id = item.id,
                                      rel_game_id = i[1],
                                      correlation = i[0])
                db.session.add(recommend)
                db.session.commit()