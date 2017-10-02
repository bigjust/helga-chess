import datetime

from chess import pgn, svg, uci, Board, Move
from collections import OrderedDict
import pymongo
from os import path
from random import randrange
import requests
from StringIO import StringIO

from helga import log, settings
from helga.db import db
from helga.plugins import command
from helga.plugins.webhooks import route, HttpError

logger = log.getLogger(__name__)

NICK = getattr(settings, 'NICK')
ENGINE = getattr(settings, 'CHESS_ENGINE', '/usr/games/stockfish')
THINK_TIME = int(getattr(settings, 'CHESS_THINK_TIME', 2000))

def next_game_stats(channel_or_nick):
    """
    Returns the next round # and stockfish strength, by counting the
    number of games that channel_or_nick has participated in.

    (Round, Stockfish level)
    default: (1, 0)
    """

    ordered_games = db.chess.find({
        'opponent': channel_or_nick.strip('#'),
    }).sort(
        [('round', pymongo.ASCENDING)]
    )

    if not ordered_games:
        # start with level 0 for the 1st game
        return (1, 0)

    last_game = ordered_games[-1]

    next_round = last_game['round'] + 1
    last_result = last_game.headers['Result']
    stockfish_level = last_result['stockfish_level']

    if last_game.headers['Result'] in ['1-0', '0-1']:
        if (last_result.startswith('1') and last_result.headers['White'] == NICK) or\
           (last_result.startswith('0') and last_result.headers['Black'] == NICK):
            stockfish_level += 1

        else:
            stockfish_level -= 1

    return next_round, stockfish_level

def find_game(channel_or_nick):
    """
    Return the first, and hopefully only, active game, by scanning
    each game's Result header, or None if there are no active games.
    """

    games = db.chess.find({
        'opponent': channel_or_nick.strip('#'),
    })

    for game_doc in games:
        pgn_string = StringIO(game_doc['pgn'])
        pgn_game = pgn.read_game(pgn_string)

        if pgn_game.headers['Result'] == '*':
            return game_doc

def load_game(channel_or_nick):
    """
    Given a `channel_or_nick`, will load the active game from mongo.
    """

    game_doc = find_game(channel_or_nick)
    if game_doc:
        pgn_string = StringIO(game_doc['pgn'])
        return pgn.read_game(pgn_string)

def save_game(channel_or_nick, game):
    """
    Given a `channel_or_nick` and a game state, save in mongodb.
    """

    game_doc = find_game(channel_or_nick)
    exporter = pgn.StringExporter(
        headers=True,
        variations=False,
        comments=False,
    )
    pgn_string = game.accept(exporter)

    if not game_doc:
        db.chess.insert({
            'opponent': channel_or_nick.strip('#'),
            'pgn': pgn_string,
            'round': game.headers['Round'],
            'stockfish_level': game.headers['Event'],
        })

    else:
        db.chess.update_one({
            '_id': game_doc['_id'],
        },{
            '$set': {
                'pgn': pgn_string,
            },
        })

@command('chess', help='chess in irc')
def chess_plugin(client, channel, nick, message, cmd, args):
    """

    Command for helga-chess.

    Usage:

    <bigjust> !chess board
    <helga> <url to dpaste.com>

    <bigjust> !chess newgame
    <helga> I chose black, white to move
    <helga> I chose white, e5

    Between each move, the game is saved and persisted on file.

    board and move commands always assume latest game in the
    gamefile. Multiple games will be stored per channel/user in
    history.
    """

    engine = uci.popen_engine(ENGINE)
    headers = OrderedDict()
    current_game = None

    game = load_game(channel)

    if not game:
        game = pgn.Game()

    board = game.end().board()

    if args[0] in ['newgame', 'move', 'board']:
        if args[0] == 'board':
            return 'http://localhost:8080/chess/{}/'.format(channel)

        if args[0] == 'move':
            if len(args) < 2:
                return 'usage: move e3e5'

            try:
                board.push(Move.from_uci(args[1]))
            except ValueError:
                return 'not a valid move. valid moves: {}'.format(
                    ', '.join([str(move) for move in board.legal_moves])
                )

            engine.position(board)
            move = engine.go(movetime=THINK_TIME).bestmove
            client.msg(channel, 'my move: {}'.format(str(move)))
            board.push(move)

        if args[0] == 'newgame':

            # setup a new game, choose a random side, persist after
            # setup(), and possibly first move
            engine.ucinewgame()
            board = Board()
            engine.position(board)

            next_round, stockfish_level = next_game_stats(channel)

            bot_turn = randrange(2)

            if not bot_turn:
                # we're white
                headers.update({
                    'White': NICK,
                    'Black': channel,
                })

                best_move = engine.go(movetime=THINK_TIME).bestmove
                board.push(best_move)
                next_turn = 'Black'

            else:
                headers.update({
                    'Black': NICK,
                    'White': channel,
                })
                next_turn = 'White'

            now = datetime.datetime.now()
            headers.update({
                'Date': '{}.{}.{}'.format(
                    now.year,
                    now.month,
                    now.day
                ),
                'Round': next_round,
                'Event': stockfish_level,
            })

            client.msg(channel, '{} to move'.format(next_turn))

        # persist the game
        game = pgn.Game.from_board(board)
        game.headers = headers
        save_game(channel, game)

@route(r'/chess/(?P<channel>[\w\-\_]+)/')
def chess_board_webhook(request, client, channel=None):

    request.setHeader('Content-Type', 'text/html')

    game = load_game(channel)

    if not game:
        raise HttpError(404)

    board = game.end().board()
    board_svg = svg.board(
        board=board,
        flipped=not board.turn,
        size=500
    )
    return '<html><body>{}</body></html>'.format(board_svg)
