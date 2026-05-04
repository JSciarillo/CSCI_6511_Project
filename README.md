# CSCI_6511_Project

Game Rules: 
The objective of the game is to create rows, columns or diagonals of 5 connected checkers on the board. The game ends when someone or one of the team has reached 2 rows of 5 connected checkers. Thus, the problem is to create an optimal algorithm that is able to decide which card to play to win the game by analysing the board. The algorithm is also to be able to decide the next step in which to place a chip by playing the card in hand or to block the opponents. 


Objective of the agent: 
The intelligent agent is designed to play the board game **Sequence** using ExpectiMiniMax algorithm/ Monte Carlo Tree Search



## ExpectiMiniMax algorithm 
Sequence contains uncertainty because players draw random cards after each turn.
The algorithm models three types of nodes:

- **MAX node** → the AI chooses the best move
- **MIN node** → the opponent chooses the best response
- **CHANCE node** → a random card is drawn from the deck

The expected utility of a chance node is computed as:

ExpectedValue(node) = Σ P(outcome) × Value(outcome)

Where:
- `P(outcome)` is the probability of drawing a specific card
- `Value(outcome)` is the board evaluation after that draw

This allows the agent to make decisions that maximize long-term expected reward
rather than only immediate board advantage.



## Monte Carlo Tree Search 

