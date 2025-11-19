import random

board = ['-', '-', '-',
         '-', '-', '-',
         '-', '-', '-']

current_player = 'X'
winner = None
gamerunning = True

# printting the game board
def printboard(board):
    print(board[0] + ' / ' + board[1] + ' / ' + board[2])
    print('----------')
    print(board[3] + ' / ' + board[4] + ' / ' + board[5])
    print('----------')
    print(board[6] + ' / ' + board[7] + ' / ' + board[8])


# take player input
def playerinput(board):
    inp = int(input("Enter a number 1-9: "))
    if 1 <= inp <= 9 and board[inp-1] == '-':
        board[inp-1] = current_player
    else:
        print("Oops player is already in that spot or invalid!")


# check horizontal win
def checkhorizontal(board):
    global winner
    if board[0] == board[1] == board[2] != '-':
        winner = board[0]
        return True
    elif board[3] == board[4] == board[5] != '-':
        winner = board[3]
        return True
    elif board[6] == board[7] == board[8] != '-':
        winner = board[6]
        return True


# check vertical win
def checkrow(board):
    global winner
    if board[0] == board[3] == board[6] != '-':
        winner = board[0]
        return True
    elif board[1] == board[4] == board[7] != '-':
        winner = board[1]
        return True
    elif board[2] == board[5] == board[8] != '-':
        winner = board[2]
        return True


# check diagonal win
def checkdiagonal(board):
    global winner
    if board[0] == board[4] == board[8] != '-':
        winner = board[0]
        return True
    elif board[2] == board[4] == board[6] != '-':
        winner = board[2]
        return True


def checktie(board):
    global gamerunning
    if '-' not in board:
        printboard(board)
        print("It is a tie!")
        gamerunning = False


def checkwin():
    global gamerunning
    if checkhorizontal(board) or checkrow(board) or checkdiagonal(board):
        printboard(board)
        print(f"The winner is {winner}!")
        gamerunning = False


def switchplayer():
    global current_player
    if current_player == 'X':
        current_player = 'O'
    else:
        current_player = 'X'


# MAIN GAME LOOP
while gamerunning:
    printboard(board)
    playerinput(board)
    checkwin()
    checktie(board)
    switchplayer()

# computer
def computer(board):
    while current_player == 'O':
        position = random.randint(0, 8)
        if board[position] == '-':
            board[position] = 'O'
            switchplayer()

            computer(board)
            checkwin(board)
            checktie(board)
