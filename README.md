# Sequence Expectimax Agent
## Requirements
Python 3.12

Runs on a regular laptop or desktop.  


## How to run
1. Clone the repository
```
https://github.com/JSciarillo/CSCI_6511_Project.git
```

2. Install Dependencies:
```
pip install -r requirements.txt
```

3. To run the headless version of the Expectimax agent:
```
cd src/
python agent.py
```

## Sequence Game Objective
The objective of the game is to create rows, columns or diagonals of 6 connected chips on the board. The game ends when someone has reached 1 row of 6 connected chips. Thus, the problem is to create an optimal algorithm that is able to decide which card to play to win the game by analyzing the board. The algorithm is decides the next step in which to place a chip by playing the card in hand or to block the opponents. 

## Problem Statement
Sequence is a stochastic sequential decision problem. The agent cannot see the opponenent's hand, the next card drawn is random, and it is uncertain how the state of the board will change after the opponent's move.

## Related Solutions to Similar Problems


## Objective of the agent 
The agent is designed to play the Sequence game against a random opponent using an Expectimax agent.

## Nature of the game
The randomness of the game with a large state space have make it non-trivial as the player have to determine if it more beneifitcial to use their turn to build on their own sequence or block their opponent’s sequence. The uncertainty of the cards of the other player and the state transitions of the board game have cause the game to be very complex. The state space is partial observability. As players are only able to see their cards in hand as well as the placement of the chip throughout the game. Player is not able to observe the card in other player's hands including their teammate.

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
Expectimax Algorithm

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
The opponent is a random player because the agent cannot see the opponent's hand. The expecti node determines the average over all legal moves the opponent can may. 

  Expected score = sum(score for every opponent move) / number of opponent moves

### Evaluation Method
Due to the excessive computation load on the UI, we implemented the headless_game() function in agent.py to have the agent play against the opponent. The number of games and depth of the search could be adjusted here. Each game is timed and the outcome of win, loss, or draw, is recorded.


## Original Game Link
Original Sequence game implementation:
[https://github.com/heksadecimal/sequence.git](https://github.com/heksadecimal/sequence.git)
