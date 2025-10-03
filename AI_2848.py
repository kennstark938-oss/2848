from flask import Flask, render_template_string, request, jsonify, session
import random
import copy

app = Flask(__name__)
app.secret_key = "super-secret-key"

def initialize_board():
    board = [[0] * 4 for _ in range(4)]
    add_new_tile(board)
    add_new_tile(board)
    return board

def add_new_tile(board):
    empty = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if empty:
        i, j = random.choice(empty)
        board[i][j] = 2 if random.random() < 0.9 else 4

def move_left(board):
    new_board = copy.deepcopy(board)
    gain = 0
    for row in new_board:
        nonzero = [tile for tile in row if tile != 0]
        merged = []
        skip = False
        for i in range(len(nonzero)):
            if skip:
                skip = False
                continue
            if i + 1 < len(nonzero) and nonzero[i] == nonzero[i + 1]:
                merged_value = nonzero[i] * 2
                merged.append(merged_value)
                gain += merged_value
                skip = True
            else:
                merged.append(nonzero[i])
        merged += [0] * (4 - len(merged))
        for i in range(4):
            row[i] = merged[i]
    return new_board, gain

def rotate_board(board, k=1):
    new_board = copy.deepcopy(board)
    for _ in range(k):
        new_board = [list(row) for row in zip(*new_board[::-1])]
    return new_board

def try_move(board, direction):
    if direction == "A":
        nb, gain = move_left(board)
    elif direction == "W":
        nb1 = rotate_board(board, 1)
        nb2, gain = move_left(nb1)
        nb = rotate_board(nb2, 3)
    elif direction == "S":
        nb1 = rotate_board(board, 3)
        nb2, gain = move_left(nb1)
        nb = rotate_board(nb2, 1)
    elif direction == "D":
        nb1 = rotate_board(board, 2)
        nb2, gain = move_left(nb1)
        nb = rotate_board(nb2, 2)
    else:
        return board, False, 0
    moved = (nb != board)
    return nb, moved, gain

def is_game_over(board):
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return False
            if i < 3 and board[i][j] == board[i+1][j]:
                return False
            if j < 3 and board[i][j] == board[i][j+1]:
                return False
    return True

def max_tile(board):
    return max(max(row) for row in board)

def get_ai_move(board):
    moves = ['W', 'A', 'S', 'D']
    best_score = -1
    best_move = None
    for move in moves:
        nb, moved, _ = try_move(board, move)
        if moved:
            score = sum(sum(x) for x in nb)
            if score > best_score:
                best_score = score
                best_move = move
    return best_move

@app.route('/')
def index():
    session['board'] = initialize_board()
    session['history'] = []
    session['score'] = 0
    return render_template_string(TEMPLATE)

@app.route('/get_board')
def get_board():
    board = session.get('board', initialize_board())
    return jsonify({
        'board': board,
        'game_over': is_game_over(board),
        'score': session.get('score', 0),
        'max_tile': max_tile(board)
    })

@app.route('/move', methods=['POST'])
def move():
    direction = request.json.get('direction')
    board = session['board']
    history = session['history']
    score = session.get('score', 0)
    new_board, moved, gain = try_move(board, direction)
    if moved:
        history.append(copy.deepcopy(board))
        add_new_tile(new_board)
        session['board'] = new_board
        session['history'] = history
        session['score'] = score + gain
    game_over = is_game_over(session['board'])
    max_tile_now = max_tile(session['board'])
    win = max_tile_now >= 2048
    return jsonify({
        'board': session['board'],
        'moved': moved,
        'game_over': game_over,
        'score': session.get('score', 0),
        'max_tile': max_tile_now,
        'win': win
    })

@app.route('/hint')
def hint():
    move = get_ai_move(session['board'])
    return jsonify({'hint': move})

@app.route('/ai_play', methods=['POST'])
def ai_play():
    board = session['board']
    history = session['history']
    score = session.get('score', 0)
    if is_game_over(board):
        return jsonify({'board': board, 'game_over': True})
    direction = get_ai_move(board)
    if direction:
        new_board, moved, gain = try_move(board, direction)
        if moved:
            history.append(copy.deepcopy(board))
            add_new_tile(new_board)
            session['board'] = new_board
            session['history'] = history
            session['score'] = score + gain
    game_over = is_game_over(session['board'])
    max_tile_now = max_tile(session['board'])
    win = max_tile_now >= 2048
    return jsonify({
        'board': session['board'],
        'game_over': game_over,
        'move': direction,
        'score': session.get('score', 0),
        'max_tile': max_tile_now,
        'win': win
    })

@app.route('/undo', methods=['POST'])
def undo():
    history = session.get('history', [])
    if history:
        session['board'] = history.pop()
        session['history'] = history
        session['score'] = sum(sum(x) for x in session['board'])
    return jsonify({
        'board': session['board'],
        'score': session['score'],
        'max_tile': max_tile(session['board'])
    })

@app.route('/reset', methods=['POST'])
def reset():
    session['board'] = initialize_board()
    session['history'] = []
    session['score'] = 0
    return jsonify({'board': session['board'], 'score': 0, 'max_tile': max_tile(session['board'])})

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>2048 - Enhanced AI Edition</title>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <style>
        body {
            background: linear-gradient(to bottom right,#222, #555 90%);
            color: #fff; font-family: 'Segoe UI', Arial, sans-serif;
            display: flex; flex-direction: column; align-items: center; min-height: 100vh;
        }
        h1 {color: #ffd700; font-size: 2.7em; margin: 24px 0 12px; font-weight: 800;}
        #game-container {background: #222; padding: 25px; border-radius: 16px; box-shadow: 0 4px 24px #222; margin-top: 24px;}
        table {border-spacing: 12px;}
        td {
            width: 60px;height: 60px; text-align:center; font-size:2em; font-weight:700; border-radius:10px;
            background: #333;
            box-shadow: 0 2px 8px #111;
            transition: background 0.18s, color 0.18s, transform 0.12s;
            position: relative;
            user-select: none;
        }
        .tile-0 {background: #484848; color: #888;}
        .tile-2 {background:#eee4da; color:#222;}
        .tile-4 {background:#ede0c8; color:#222;}
        .tile-8 {background:#f2b179; color:#fff;}
        .tile-16 {background:#f59563;}
        .tile-32 {background:#f67c5f;}
        .tile-64 {background:#f65e3b;}
        .tile-128 {background:#edcf72;}
        .tile-256 {background:#edcc61;}
        .tile-512 {background:#edc850;}
        .tile-1024 {background:#eec944;}
        .tile-2048 {background:#ffd700; color:#222; box-shadow:0 0 20px #fff568;}
        .tile-4096, .tile-8192, .tile-16384 {background:#7745c1; color:#fff; box-shadow:0 0 25px #7e54d5;}
        #scoreboard {color:#ffd700; margin-bottom:16px; font-size:1.25em;}
        #score, #maxTile {color:#ffd700; margin:0 10px;}
        #controls {margin-top:28px;}
        button {
            background:#444;color:#fff;padding:12px 20px; margin-right:8px;border-radius:8px;
            border:none; font-size:1.08em; font-family:inherit; transition: background 0.2s;
            box-shadow: 0 2px 6px #222; cursor:pointer;
        }
        button:hover {background:#ffd700; color:#222;}
        #status {margin-top:15px; font-size:1.15em; height:26px;}
        #game-over {
            position: absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.68);
            display:flex;align-items:center;justify-content:center;flex-direction:column;
            border-radius:16px; color:#ffd700; font-size:2em; z-index:5;
            animation: fadein 0.7s;
        }
        #win {color:#ffd700; background:rgba(56,56,16,0.94); font-size:2em; font-weight:700;
             padding:12px 34px; border-radius:14px; box-shadow:0 6px 22px #ffd700;}
        @keyframes fadein {from{opacity:0;} to{opacity:1;}}
        @media (max-width: 700px) {
            #game-container { padding: 8px; }
            td { width: 38px; height: 38px; font-size: 1.1em; }
        }
    </style>
</head>
<body>
    <h1>2048 - Enhanced AI Edition 🚀</h1>
    <div id="scoreboard">
        Score: <span id="score">0</span> &nbsp;&nbsp; | &nbsp;&nbsp;
        Highest Tile: <span id="maxTile">0</span>
    </div>
    <div id="game-container">
        <div style="position:relative;">
            <div id="board-parent"></div>
            <div id="game-over" style="display:none;">
                <span>Game Over!</span>
                <br><button onclick="resetGame()">Restart</button>
            </div>
            <div id="win" style="display:none;">🎉 You reached 2048!</div>
        </div>
        <div id="controls">
            <button onclick="move('W')">↑</button>
            <button onclick="move('A')">←</button>
            <button onclick="move('S')">↓</button>
            <button onclick="move('D')">→</button>
            <button onclick="getHint()">Hint</button>
            <button onclick="aiPlay()">AI Play</button>
            <button onclick="undoMove()">Undo</button>
            <button onclick="resetGame()">Reset</button>
        </div>
        <div id="status"></div>
    </div>
    <script>
        let is_ai_playing = false;
        document.addEventListener('keydown', function(e) {
            if(is_ai_playing) return;
            let code = e.code;
            if(code=='ArrowUp'){move('W');}
            else if(code=='ArrowLeft'){move('A');}
            else if(code=='ArrowDown'){move('S');}
            else if(code=='ArrowRight'){move('D');}
        });

        function wrapBoard(board, score, maxTile) {
            let html = '<table>';
            for(let i=0;i<4;i++){
                html += '<tr>';
                for(let j=0;j<4;j++){
                    let val = board[i][j];
                    let extra = '';
                    if(val >= 4096) extra = ' tile-4096';
                    else if(val >= 2048) extra = ' tile-2048';
                    html += `<td class="tile-${val}${extra}">${val||''}</td>`;
                }
                html += '</tr>';
            }
            html += '</table>';
            document.getElementById('board-parent').innerHTML = html;
            document.getElementById('score').innerText = score;
            document.getElementById('maxTile').innerText = maxTile;
        }
        function loadBoard(){
            fetch('/get_board')
              .then(resp=>resp.json())
              .then(data=>{
                wrapBoard(data.board, data.score, data.max_tile);
                checkWin(data.max_tile)
                if(data.game_over) showGameOver();
                else hideGameOver();
              });
        }
        function move(direction){
            if(is_ai_playing) return;
            fetch('/move', {
                method: 'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({direction})
            })
            .then(resp=>resp.json())
            .then(data=>{
                wrapBoard(data.board, data.score, data.max_tile);
                checkWin(data.max_tile)
                if(data.max_tile >= 2048 && !data.game_over) showWin();
                if(data.game_over) showGameOver();
                else hideGameOver();
            });
        }
        function getHint(){
            fetch('/hint')
            .then(resp=>resp.json())
            .then(data=>{
                let move = data.hint;
                document.getElementById('status').innerText = "AI suggests: " + move;
                setTimeout(()=>{document.getElementById('status').innerText = "";},2000);
            });
        }
        function aiPlay(){
            if(is_ai_playing) return;
            is_ai_playing = true;
            function step(){
                fetch('/ai_play',{method:'POST'})
                .then(resp=>resp.json())
                .then(data=>{
                    wrapBoard(data.board, data.score, data.max_tile);
                    checkWin(data.max_tile);
                    if(data.game_over) {showGameOver(); is_ai_playing=false; return;}
                    if(data.move) setTimeout(step,280);
                    else is_ai_playing = false;
                    if(data.max_tile >= 2048 && !data.game_over) showWin();
                });
            }
            step();
        }
        function undoMove(){
            fetch('/undo',{method:'POST'})
            .then(resp=>resp.json())
            .then(data=>{
                wrapBoard(data.board, data.score, data.max_tile);
                checkWin(data.max_tile);
                hideGameOver();
            });
        }
        function resetGame(){
            is_ai_playing = false;
            fetch('/reset',{method:'POST'})
            .then(resp=>resp.json())
            .then(data=>{
                wrapBoard(data.board, data.score, data.max_tile);
                checkWin(data.max_tile);
                hideGameOver();
                hideWin();
            });
        }
        function showGameOver(){
            document.getElementById('game-over').style.display = 'flex';
        }
        function hideGameOver(){
            document.getElementById('game-over').style.display = 'none';
        }
        function showWin(){
            const winDiv = document.getElementById('win');
            winDiv.style.display = 'block';
            setTimeout(()=>{winDiv.style.display='none';}, 4000);
        }
        function hideWin(){
            document.getElementById('win').style.display = 'none';
        }
        function checkWin(maxTile){
            if(maxTile >= 2048) showWin();
        }
        window.onload = loadBoard;
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)

