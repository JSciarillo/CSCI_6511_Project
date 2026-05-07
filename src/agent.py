import random
from collections import defaultdict
from gamestate import GameState, count_consec_chips, ONE_EYE_J, TWO_EYE_J
from backend.logic import Game
from backend.player import player
import time
import math
import sys

class RandomAgent:
    """
    Baseline random action agent to test the environment
    """
    def getAction(self, obs, valid_actions):
        return random.choice(valid_actions)
    

def capture_state(game, my_player, opp_player):
    """
    Converts the live game into a game state for the agent.
    """
    full_deck = [
        f"{rank}{suit}"
        for rank in list("KQJA") + list(map(str, range(2, 11)))
        for suit in "SHCD"
    ] * 2

    already_used = defaultdict(int)
    for card in my_player.playerCards:
        already_used[card] += 1
    for card, count in game.used.items():
        already_used[card] += count

    remaining_deck = [c for c in full_deck if already_used[c] < full_deck.count(c)]
    random.shuffle(remaining_deck)

    return GameState(
        agent_chips  = [row[:] for row in my_player.playerBox],
        opp_chips    = [row[:] for row in opp_player.playerBox],
        agent_hand   = list(my_player.playerCards),
        deck         = remaining_deck,
        agent_score  = my_player.playerScore,
        opp_score    = opp_player.playerScore,
        game_over    = game.winner,
    )


def evaluationFunction(state):
    """
    Scores the board state from the agent's perspective.
    Higher is better for the agent but worse for the opponent.
    """
    if state.isWin():
        return 100000
    if state.isLose():
        return -100000

    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for row in range(10):
        for col in range(10):
            for drow, dcol in directions:
                #reward agent runs
                if state.agent_chips[row][col]:
                    run = count_consec_chips(state.agent_chips, row, col, drow, dcol)
                    score += run * run
                #penalize opponent runs
                if state.opp_chips[row][col]:
                    run = count_consec_chips(state.opp_chips, row, col, drow, dcol)
                    score -= run * run

    return score

class ExpectimaxAgent:
    """
    Expectimax agent for Sequence.
    Max nodes are for the agent's turn, agent picks highest value move
    Chance nodes are the opponent's turn, averages over all possible moves
    """
    def __init__(self, depth=2):
        self.depth = depth
        self.current_state = None

    def set_state(self, game, my_player, opp_player):
        """Capture the live game before each search"""
        self.current_state = capture_state(game, my_player, opp_player)

    def getAction(self, obs, valid_actions):
        """Gets the best action from hte current state"""
        if not valid_actions:
            return None
        
        if len(valid_actions) == 1:
            return valid_actions[0]

        highestValue  = -float('inf')
        bestMove = valid_actions[0]

        for action in valid_actions:
            #generates successor after agent takes action
            successor = self.current_state.generateSuccessor(0, action)
            #evaluate the move
            value = self.ExpectiValue(successor, 0, 1)
            if value > highestValue:
                highestValue  = value
                bestMove = action

        return bestMove

    def MaxValue(self, gameState, depth, agentIndex):
        """
        Agent picks move with the highest value
        """
        if gameState.isWin() or gameState.isLose() or depth == self.depth:
            return evaluationFunction(gameState)

        value   = -float('inf')
        actions = gameState.getLegalActions(agentIndex)

        for action in actions:
            successor = gameState.generateSuccessor(agentIndex, action)
            
            #after agent move, goes to expecti node
            newValue    = self.ExpectiValue(successor, depth, 1)
            if newValue > value:
                value = newValue

        return value

    def ExpectiValue(self, gameState, depth, agentIndex):
        """
        Chance node
        """
        if gameState.isWin() or gameState.isLose() or depth == self.depth:
            return evaluationFunction(gameState)

        value   = 0
        actions = gameState.getLegalActions(agentIndex)

        #sets a limit to the number of legal actions searched
        #actions = actions[:15]

        #agent is 0, opponent is 1
        numAgents = 2

        for action in actions:
            successor = gameState.generateSuccessor(agentIndex, action)
            nextAgent = (agentIndex + 1) % numAgents

            if nextAgent == 0:
                #back to agent's node, increment depth
                newValue = self.MaxValue(successor, depth + 1, 0)
            else:
                #stay in chance node for next agent
                newValue = self.ExpectiValue(successor, depth, nextAgent)

            value += newValue

        #takes average over opponent
        return value / len(actions)

#Followed the algorithm from the slides in class / Decision Making Under Uncertainty, MIT Press 2015.
#https://faculty.cs.gwu.edu/goldfrank/4511/notes/10/10.html#/uct-search---algorithm
#Followed this article and this YouTube video for guidelines:
#https://www.geeksforgeeks.org/machine-learning/monte-carlo-tree-search-mcts-in-machine-learning/
#https://www.youtube.com/watch?v=UXW2yZndl7U
class MCTSNode:
    """
    Elements for one node in the MCTS search tree.
    """
    def __init__(self, gamestate, parent=None, action=None):
        self.gamestate = gamestate #current gamestate
        self.parent = parent #parent node of current node
        self.action= action #action that led to this node
        self.children = [] #child nodes
        self.not_tried = list(gamestate.getLegalActions(0)) #not tried actions from this state

        #tracks visit count N(s,a)
        self.N = 0

        #tracks action value Q(s,a)
        self.Q = 0

    def is_fully_expanded(self):
        """all actions in A(s) have been tried"""
        return len(self.not_tried) == 0

    def uct_score(self, c=2):
        """
        UCT formula:
        Q(s,a) + c * squareroot(log N(s) / N(s,a))

        Used a constant of 2
        """
        #unvisited nodes get selected first
        if self.N == 0:
            return float('inf')
        #updated score:
        return self.Q + c * math.sqrt(math.log(self.parent.N) / self.N)

    def best_child(self, c=2):
        """
        Select child with highest UCT score.
        For the selection phase
        """
        if not self.children:
            return None

        best = self.children[0]
        for child in self.children:
            if child.uct_score(c) > best.uct_score(c):
                best = child
        return best

    def best_action(self):
        """
        Return action with highest visit count for final decision
        Since the most visited is the most reliable estimate
        """
        best = self.children[0]
        for child in self.children:
            if child.N > best.N:
                best = child
        return best


class MCTSAgent:
    """
    Monte Carlo Tree Search agent for Sequence.
    Using UCT Search and Rollout algorithm
    from class slides/Kochenderfer, Decision Making Under Uncertainty, MIT Press 2015.
    """
    def __init__(self, num_simulations=100, c=1.41, gamma=1.0):
        self.num_simulations = num_simulations #number of simulations
        self.c = c # constant
        self.gamma = gamma #discount factor
        self.current_state = None

    def set_state(self, game, my_player, opp_player):
        """Capture the live game before each search."""
        self.current_state = capture_state(game, my_player, opp_player)

    def getAction(self, obs, valid_actions):
        """
        Gets the actions with the most visits
        """
        if not valid_actions:
            return None
        if len(valid_actions) == 1:
            return valid_actions[0]

        root = MCTSNode(self.current_state)

        #run simulations 
        for _ in range(self.num_simulations):
            self.simulate(root, depth=3)

        #action with most visits
        return root.best_action().action

    def simulate(self, node, depth):
        """
        Builds the tree with UCT selection.
        Follows the phases: selection, expansion, rollout, back-propagation
        """
        #checks if depth limit is reached or game is in terminal state
        if depth == 0 or node.gamestate.isWin() or node.gamestate.isLose():
            return 0


        #checks if this is first visit to node then expands all actions, then does rollout
        if not node.is_fully_expanded() and not node.children:

            #makes a child node for each legal action
            for action in list(node.not_tried):
                new_state = node.gamestate.generateSuccessor(0, action)
                child = MCTSNode(new_state, parent=node, action=action)
                node.children.append(child)
            node.not_tried = []

            #chooses random child and does rollout
            child = random.choice(node.children)
            q = self.rollout(child.gamestate, depth)

            #backpropagates (update N and Q for child)
            child.N += 1
            child.Q += (q - child.Q) / child.N
            node.N  += 1
            return q
        #chooses the best child
        child = node.best_child(self.c)

        if child is None:
            return 0

        #opponent makes a random move after agent
        opp_actions = child.gamestate.getLegalActions(1)
        if opp_actions:
            opp_action = random.choice(opp_actions)
            next_state = child.gamestate.generateSuccessor(1, opp_action)
        else:
            next_state = child.gamestate

        #temporary node for opponent's resulting state
        next_node = MCTSNode(next_state, parent=child)

        r = 1 if child.gamestate.isWin() else 0
        q = r + self.gamma * self.simulate(next_node, depth - 1)

        #update number of times visited
        child.N += 1
        #update Q value
        child.Q += (q - child.Q) / child.N
        node.N  += 1

        return q

    def rollout(self, state, depth):
        """
        Random simulation from state to end of game.
        Returns discounted cumulative reward.
        """
        #base case if the depth limit is 0 or game is in terminal state
        if depth == 0 or state.isWin() or state.isLose():
            if state.isWin():
                return 1
            else:
                return 0

        #agent picks random action
        actions = state.getLegalActions(0)
        if not actions:
            return 0
        action = random.choice(actions)

        #generate successor and receives reward
        next_state = state.generateSuccessor(0, action)
        r = 1 if next_state.isWin() else 0

        #opponent's random move after agent
        opp_actions = next_state.getLegalActions(1)
        if opp_actions:
            opp_action = random.choice(opp_actions)
            next_state = next_state.generateSuccessor(1, opp_action)
        
        #new discounted reward
        new_r = r + self.gamma * self.rollout(next_state, depth - 1)
        return new_r

    

def headless_game(num_games=10, agent_type="mcts", num_simulations=200, depth=1):
    """
    Runs the num_games of games between the agent and a random opponent.
    This is the method for evaluation because the UI cannot handle the computation load.
    """

    print(f"Headless Sequence Game")
    print(f"Running " + agent_type + " agent")
    print(f"{num_games} game iterations\n")

    total_results = []

    for game_num in range(1, num_games + 1):

        game = Game()
        agent_player = player("agent")
        opponent_player = player("opponent")
        game.distribute(agent_player)
        game.distribute(opponent_player)

        #runs respective agent
        if agent_type == "expectimax":
            agent = ExpectimaxAgent(depth=depth)
        elif agent_type == "mcts":
            agent = MCTSAgent(num_simulations=num_simulations)

        move_times = []
        num_turns = 0
        outcome = "draw"

        game_start = time.time()

        while num_turns < 500:
            #builds valid actions for agent
            actions = []
            for card in set(agent_player.playerCards):

                if card in ONE_EYE_J:
                    for i in range(10):
                        for j in range(10):
                            if opponent_player.playerBox[i][j]:
                                actions.append((card, i, j))
                elif card in TWO_EYE_J:
                    for i in range(10):
                        for j in range(10):
                            if (game.board[i][j] != "XX"
                                    and agent_player.playerBox[i][j] == 0
                                    and opponent_player.playerBox[i][j] == 0):
                                actions.append((card, i, j))
                else:
                    for i in range(10):
                        for j in range(10):
                            if (game.board[i][j] == card
                                    and agent_player.playerBox[i][j] == 0
                                    and opponent_player.playerBox[i][j] == 0):
                                actions.append((card, i, j))

            if not actions:
                outcome = "draw"
                break

            #amount of time it takes agent to pick a move
            time0 = time.time()
            agent.set_state(game, agent_player, opponent_player)
            chosen = agent.getAction(None, actions)
            move_times.append(time.time() - time0)

            #agent's chosen move
            card, row, col = chosen
            works = game.setBox(agent_player, opponent_player.playerBox, row, col)
            if works:
                agent_player.addCard(game.getNewCard())
            num_turns += 1

            if game.winner:
                outcome = "win" if agent_player.playerScore >= 1 else "loss"
                break
            if not game.deck:
                outcome = "draw"
                break

            while True:
                works = game.makeRandomMove(opponent_player, agent_player)
                if works:
                    break
            num_turns += 1
                  

            if game.winner:
                outcome = "win" if agent_player.playerScore >= 1 else "loss"
                break
            if not game.deck:
                outcome = "draw"
                break

        #tracks results of the game
        game_time = time.time() - game_start
        #converts to milliseconds
        avg_move_ms = (sum(move_times) / len(move_times) * 1000) if move_times else 0
        max_move_ms = (max(move_times) * 1000) if move_times else 0

        total_results.append({
            "outcome": outcome,
            "turns": num_turns,
            "game_time": game_time,
            "avg_move_ms": avg_move_ms,
            "max_move_ms": max_move_ms,
        })

        print(f"Game {game_num}: {outcome}")
        print(f"Agent {agent_player.playerScore} - Opponent {opponent_player.playerScore}")
        print(f"Turns- {num_turns}  (agent made {len(move_times)} moves)")
        print(f"Game time- {game_time:.2f}s")
        print(f"Average move time- {avg_move_ms:.1f}ms")
        print(f"Max move time- {max_move_ms:.1f}ms\n")

    #results across all games
    counts = {"win": 0, "loss": 0, "draw": 0}
    for r in total_results:
        counts[r["outcome"]] += 1
    wins = counts["win"]
    losses = counts["loss"]
    draws = counts["draw"]
    

    total_time = sum(result["game_time"] for result in total_results)
    avg_game_time = total_time / num_games
    avg_move_time = sum(r["avg_move_ms"] for r in total_results) / num_games

    print(f"Results of {num_games} games-")
    print(f"Wins- {wins} out of {num_games}")
    print(f"Losses- {losses} out of {num_games}")
    print(f"Draws- {draws} out of {num_games}")
    print(f"Total run time- {total_time:.2f} seconds")
    print(f"Average game time- {avg_game_time:.2f} seconds")
    print(f"Average move time- {avg_move_time:.1f}ms")



    return total_results


if __name__ == "__main__":
    #takes in command line argument to load agent type
    agent_type = sys.argv[1]
    num_games = int(sys.argv[2])

    #sets the expectimax depth and number of games on the arguments
    if agent_type == "expectimax":
        depth = int(sys.argv[3])
        headless_game(num_games=num_games, agent_type=agent_type,depth=depth)
    #sets the mcts numbers simulations games based on the arguments 
    elif agent_type == "mcts":
        num_simulations = int(sys.argv[3])
        headless_game(num_games=num_games,agent_type=agent_type,num_simulations=num_simulations)