import random
from collections import defaultdict
from gamestate import GameState, count_consec_chips, ONE_EYE_J, TWO_EYE_J
from backend.logic import Game
from backend.player import player
import time

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
    


def headless_game(num_games=10, depth=2):
    """
    Runs the num_games of games between the agent and a random opponent.
    This is the method for evaluation because the UI cannot handle the computation load.
    """

    print(f"Headless Sequence Game")
    print(f"{num_games} game iterations\n")

    total_results = []

    for game_num in range(1, num_games + 1):

        game = Game()
        agent_player = player("agent")
        opponent_player = player("opponenet")
        game.distribute(agent_player)
        game.distribute(opponent_player)

        agent = ExpectimaxAgent(depth=depth)
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
    headless_game(num_games=10, depth=1)