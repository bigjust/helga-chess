helga-chess
===========

allows the channel to play chess against Helga, or each other via e-mail

for channel games against helga, allows only one game at a time, any player
can propose a move.

uses stockfish (or any UCI-compliant backend).

Requires access to Amazon SES

TODO:

1. write tests
2. Integrate some email functionality
3. use helga-elo (https://github.com/narfman0/helga-elo)

To be honest, i'm not even sure if game termination works, at all


Installation
============

`apt install stockfish`, among other things

Settings
========

CHESS_ENGINE: default `/usr/games/stockfish`, defines the
UCI-compliant backend process name

CHESS_THINK_TIME: default `2000` (2 seconds), defines a maximum amount
of time that the engine will ponder a move

License
-------

Copyright (c) 2017 Justin Caratzas

GPLv3 Licensed
