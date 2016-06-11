from flask import render_template, redirect, url_for, flash, request
from . import game
from ..models import Game
from sqlalchemy import or_


@game.route('/')
def index():
    '''游戏首页'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'index'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/stg')
def show_stg():
    '''显示射击类游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(or_(Game.game_type == '第三人称射击', 
                     Game.game_type =='第一人称射击')).paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_stg'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/rpg')
def show_rpg():
    '''显示角色扮演类游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(or_(Game.game_type == '角色扮演', 
                 Game.game_type =='动作角色扮演')).paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_rpg'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/rts')
def show_rts():
    '''显示及时战略类游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(Game.game_type == '即时战略').paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_rts'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/other')
def show_other():
    '''显示其他类型游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(or_(Game.game_type == '体育', Game.game_type == '冒险解谜',Game.game_type == '格斗',
                     Game.game_type =='冒险', Game.game_type =='休闲益智', Game.game_type =='赛车竞速' 
                     )).paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_other'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/slg')
def show_slg():
    '''显示策略模拟类游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(or_(Game.game_type == '模拟经营', 
                     Game.game_type =='模拟')).paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_slg'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/act')
def show_act():
    '''显示动作类游戏'''
    page = request.args.get('page', 1, type = int)
    pagination = Game.query.filter(or_(Game.game_type == '动作冒险', 
                     Game.game_type =='动作')).paginate(page, per_page = 12, error_out = False)
    games = pagination.items
    flag = 'show_act'
    return render_template('game/gameindex.html', games = games, pagination = pagination, flag = flag)

@game.route('/<int:id>')
def profile(id):
    game = Game.query.get_or_404(id)
    return render_template('game/game.html', game = game)