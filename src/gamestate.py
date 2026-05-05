import random
from backend.logic import Game

BOARD = Game().board

#Jack card sets for the special moves
ONE_EYE_J = {"JH", "JS"}
TWO_EYE_J = {"JD", "JC"}

def count_consec_chips(grid, row, col, row_step, col_step):
    """
    Counts how many chips are placed consecutively in one direction.
    """
    count = 0
    #keep moving while on the board and current space has a chip
    while 0 <= row < 10 and 0 <= col < 10 and grid[row][col]:
        count += 1
        row += row_step
        col += col_step

    return count

def get_legal_moves(state, is_agent_turn):
    """
    Returns a list of legal actions for the specified player
    """
    actions = []

    #tracks positions already added
    added = set()
    hand = state.agent_hand if is_agent_turn else state.deck

    for card in set(hand):
        if card in ONE_EYE_J:
                #One eyed jack removes any opp chip on board
                for row in range(10):
                    for col in range(10):
                         if (BOARD[row][col] != "XX"
                            and (state.opp_chips[row][col] if is_agent_turn else state.agent_chips[row][col])
                            and (row, col) not in added):
                              
                              actions.append((card, row, col))
                              added.add((row, col))
        elif card in TWO_EYE_J:
             #Two eyed jack, wild card
             for row in range(10):
                  for col in range(10):
                       if (BOARD[row][col] != "XX"
                           and state.agent_chips[row][col] == 0
                           and state.opp_chips[row][col] == 0
                           and (row, col) not in added):
                            actions.append((card, row, col))
                            added.add((row, col))
        else:
             #Normal card
             for row in range(10):
                  for col in range(10):
                       if (BOARD[row][col] == card
                           and state.agent_chips[row][col] == 0
                           and state.opp_chips[row][col] == 0
                           and (row, col) not in added):
                            actions.append((card, row, col))
                            added.add((row, col))

    return actions


def execute_action(state, card, row, col, is_agent_turn):
    """
    Gets the new game state of the successor
    """
    #Works on a copy of the current state
    new_state = state.copy()

    if card in ONE_EYE_J:
        #agent removes opp chip
        if is_agent_turn:
            new_state.opp_chips[row][col] = 0
        #opp removes agent chip
        else:
            new_state.agent_chips[row][col] = 0
    else:
        if is_agent_turn:
            #place agent chips
            new_state.agent_chips[row][col] = 1
            #checks each direction to see if this move completes a sequence of 6
            directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
            for drow, dcol in directions:

                forward  = count_consec_chips(new_state.agent_chips, row + drow, col + dcol,  drow,  dcol)
                backward = count_consec_chips(new_state.agent_chips, row - drow, col - dcol, -drow, -dcol)
                
                if 1 + forward + backward >= 6:
                    #adds 1 to the agent score for a sequence of 6
                    new_state.agent_score += 1
                    new_state.game_over = True
                    break

        else:
            #place opp chip
            new_state.opp_chips[row][col] = 1
            directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
            for dr, dc in directions:
                forward  = count_consec_chips(new_state.opp_chips, row + dr, col + dc,  dr,  dc)
                backward = count_consec_chips(new_state.opp_chips, row - dr, col - dc, -dr, -dc)
                if 1 + forward + backward >= 6:
                    new_state.opp_score += 1
                    new_state.game_over = True
                    break
    #removes the card from the hand and deck
    if is_agent_turn and card in new_state.agent_hand:
        new_state.agent_hand.remove(card)
    if card in new_state.deck:
        new_state.deck.remove(card)
        
    return new_state

class GameState:
    """
    Specifies the game state with the board configuration,
    both player's chip positions, hands, deck, scores,
    and the status of the game
    """
    def __init__(self, agent_chips, opp_chips, agent_hand, deck, agent_score,
                 opp_score, game_over):
        self.agent_chips = agent_chips
        self.opp_chips = opp_chips
        self.agent_hand = agent_hand
        self.deck = deck
        self.agent_score = agent_score
        self.opp_score = opp_score
        self.game_over = game_over

    def getLegalActions(self, agentIndex=0):
        """
        Gets legal actions of the agent. Index 0 is the agent, index 1 is the opponent.
        """
        if self.isWin() or self.isLose():
            return []
        return get_legal_moves(self, is_agent_turn=(agentIndex == 0))
    
    def generateSuccessor(self, agentIndex, action):
        """
        Gets the successor state after the agent takes an action.
        """
        if self.isWin() or self.isLose():
            raise Exception("Terminal state")
        card, row, col = action
        return execute_action(self, card, row, col, is_agent_turn=(agentIndex == 0))
    
    def isWin(self):
        return self.agent_score >= 1
    
    def isLose(self):
        return self.opp_score >= 1
    
    def copy(self):
        """
        Gets a deep copy of the state. Used during simulation for Expectimax and MCTS.
        """
        agent_chips_copy = [row[:] for row in self.agent_chips]
        opp_chips_copy = [row[:] for row in self.opp_chips]
        agent_hand_copy = list(self.agent_hand)
        deck_copy = list(self.deck)

        return GameState(
            agent_chips_copy, opp_chips_copy, agent_hand_copy, deck_copy,
            self.agent_score, self.opp_score, self.game_over)