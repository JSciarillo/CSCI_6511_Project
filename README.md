# Sequence Expectimax Agent

## Problem Statement
Sequence is a stochastic sequential decision problem where players can only see their own hand, not the opponent's, the next card drawn is random, and it is uncertain how the state of the board will change after the opponent's move. Players may only observe their own hand of cards and the chip placements already on the board, and use this information to win the game.

The board is a layout of two decks of cards and players have a hand of 5 cards. Special cards include the one-eyed jack which allows a player to remove an opponent's chip on the board, and the two-eyed jack that acts as a wild card to place a chip anywhere.

The objective is to create rows, columns, or diagonals of 6 connected chips on the board. The game ends when a player has reached 1 sequence of 6 connected chips. Thus, the problem is to decide which card to play to win the game by analyzing the board and determine whether to build on its own sequence or block the opponent's.

The large state space in combination with the randomness of card draws and uncertain opponent information creates a non-trivial problem.

## Motivation
The motivation for this project is to implement an approximately optimal agent that decides between building upon its sequence or blocking the opponent. We chose Expectimax for this problem since the opponent moves could be modeled by their expected score, given that the agent has no information about the opponent's hand.  

## Requirements
Python 3.12

Runs on a regular laptop or desktop. 

## Setup
1. Clone the repository
```
git clone https://github.com/JSciarillo/CSCI_6511_Project.git
```
2. Install Dependencies:
```
pip install -r requirements.txt
```
```
cd src/
```

## How to run Expectimax Agent
To run the headless version of the Expectimax agent:

**Run Expectimax agent with specified number of games and depth:**
```
python agent.py expectimax <num_games> <depth>
```
for example to run 10 games at depth 1
```
python agent.py expectimax 10 1
```

**Optionally, to limit the number of opponent actions searched (useful for any depth besides 1):**
```
python agent.py expectimax <num_games> <depth> <action_limit>
```
for example to run 10 games at depth 2 with an action limit of 15:
```
python agent.py expectimax 10 2 15
```
### Visual with the UI
**To watch the agent run on the board:**
```
python main.py expectimax <depth>
```
**Optionally, to limit the number of opponent actions searched (useful for any depth besides 1):**
```
python main.py expectimax <depth> <action_limit>
```

## Related Solutions to Similar Problems
**Pacman**


## State Space
There is a board of 100 spaces, each space represents a card. Each space can either have a chip or not have a chip. The cards can either be in the card deck, in the player’s hand, or in the discard pile. The state space is every possible arrangement of chips being on the board.

## Action space
This implementation leverages a 2 player game. The agent vs a random opponent.

Actions include: 
- Play a card from hand
- Placing a chip on the corresponding board space 
- Removing an opponent’s chip (if player played a one-eyed jack)
- Placing a chip anywhere on the board (if player played a two-eyed jack)
- Draw a replacement card after each move

# Solution Method
**Expectimax Algorithm**

## Implementation of Expectimax algorithm 

The algorithm models two types of nodes:
- **Max node** :
The agent chooses the move that would return the highest evaluation score. The length of the run is squared so that longer runs result in an exponentially higher score for the agent to base off of. 

The evaluation function rewards the agent for its chips placed consecutively:
```python
run = count_consec_chips(state.agent_chips, row, col, drow, dcol)
score += run * run
```
As well as penalizes the agent for the opponent's chips placed consecutively:
```python
run = count_consec_chips(state.opp_chips, row, col, drow, dcol)
score -= run * run
```

- **Expecti node** :
The opponent is a random player because the agent cannot see the opponent's hand. The expecti node determines the average over all legal moves the opponent can make. 

  Expected score = sum(score for every opponent move) / number of opponent moves

### Evaluation Method
Due to the excessive computation load on the UI, we implemented the headless_game() function in agent.py to have the agent play against the opponent. The number of games and depth of the search could be adjusted here. Each game is timed and the outcome of win, loss, or draw, is recorded.

### Results
**10 Games at Depth 2 with Action Limit of 10**
Results of 10 games-

Wins- 9 out of 10

Losses- 1 out of 10

Draws- 0 out of 10

Total run time- 953.41 seconds

Average game time- 95.34 seconds

Average move time- 4443.6ms

Depth- 2

Action limit- 10

**10 Games at Depth 1 with no Action Limit**
Results of 10 games-

Wins- 9 out of 10

Losses- 1 out of 10

Draws- 0 out of 10

Total run time- 34.21 seconds

Average game time- 3.42 seconds

Average move time- 139.9ms

Depth- 1

**100 Games at Depth 1 with no Action Limit**
Results of 100 games-

Wins- 83 out of 100

Losses- 17 out of 100

Draws- 0 out of 100

Total run time- 274.77 seconds

Average game time- 2.75 seconds

Average move time- 122.0ms

Depth- 1


**50 Games at Depth 1 with no Action Limit**
Results of 50 games-

Wins- 40 out of 50

Losses- 10 out of 50

Draws- 0 out of 50

Total run time- 119.98 seconds

Average game time- 2.40 seconds

Average move time- 105.6ms

## Stretch Goal: Monte Carlo Tree Search Agent
Although not outlined in our approved proposal, we began implementing a MCTS agent. This implementation method was motivated by the time constraint of Expectimax at depth 2.

The phases of MCTS include:
1. Selection: Leverages the upper confidence bound formula for deciding whether to explore or exploit
2. Expansion: Upon the first visit to a node, expands child nodes for all valid moves
3. Rollout: Runs random moves to simulate the game until terminal state
4. Backpropagation: Updates N and Q back through previous nodes

## How to Run MCTS Agent
To run the headless version of the MCTS agent:

**Run MCTS agent with specified number of games and simulations:**
```
python agent.py mcts <num_games> <num_simulations>
```
for example to run 10 games with 200 simulations
```
python agent.py mcts 10 200
```

### Visual with the UI
**To watch the MCTS agent run on the board:**
```
python main.py mcts <num_simulations>
```

## Original Game Link
Original Sequence game implementation:
[https://github.com/heksadecimal/sequence.git](https://github.com/heksadecimal/sequence.git)

### Modified Files
#### `src/main.py`
#### `src/views/game.py`
#### `src/views/menu.py`
#### `src/backend/player.py`
### Unchanged Files (from original creators)
#### `src/img`
#### `src/assets`
#### `src/backend/logic.py`
#### `src/backend/data.py`
#### `src/backend/sound.py`
#### `src/backend/userdata.json`
#### `src/backend/sound.py`
#### `src/views/settings.py`
#### `src/views/statistics.py`
#### `src/components`


#### New Files Added
`src/agent.py`
`src/gamestate.py`

## Other Resources
For MCTS:
[https://www.geeksforgeeks.org/machine-learning/monte-carlo-tree-search-mcts-in-machine-learning/](https://www.geeksforgeeks.org/machine-learning/monte-carlo-tree-search-mcts-in-machine-learning/)

Psuedocode from class / Mykal Kochenderfer. Decision Making Under Uncertainty, MIT Press 2015: 
[https://faculty.cs.gwu.edu/goldfrank/4511/notes/10/10.html#/uct-search---algorithm](https://faculty.cs.gwu.edu/goldfrank/4511/notes/10/10.html#/uct-search---algorithm)

Youtube Video: [https://www.youtube.com/watch?v=UXW2yZndl7U](https://www.youtube.com/watch?v=UXW2yZndl7U)
[https://www.geeksforgeeks.org/artificial-intelligence/expectimax-search-algorithm-in-ai/](https://www.geeksforgeeks.org/artificial-intelligence/expectimax-search-algorithm-in-ai/)

Expectimax Guidelines:
[https://www.geeksforgeeks.org/artificial-intelligence/expectimax-search-algorithm-in-ai/](https://www.geeksforgeeks.org/artificial-intelligence/expectimax-search-algorithm-in-ai/)

Sequence Game Rules:
[https://images-na.ssl-images-amazon.com/images/I/81c4gCJTojL.pdf](https://images-na.ssl-images-amazon.com/images/I/81c4gCJTojL.pdf)

