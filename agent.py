import random
import time
from collections import defaultdict
from backend.logic import Game
from backend.player import player

BOARD = Game().board

ONE_EYE_JACKS = {"JH", "JS"}
TWO_EYE_JACKS = {"JD", "JC"}


class RandomAgent:
    def select_action(self, obs, valid_actions):
        return random.choice(valid_actions)



class GameState:
    def __init__(self, my_chips, opp_chips, my_hand, deck, my_score, opp_score, game_over):
        self.my_chips   = my_chips
        self.opp_chips  = opp_chips
        self.my_hand    = my_hand
        self.deck       = deck
        self.my_score   = my_score
        self.opp_score  = opp_score
        self.game_over  = game_over

    def copy(self):
        return GameState(
            [row[:] for row in self.my_chips],
            [row[:] for row in self.opp_chips],
            list(self.my_hand),
            list(self.deck),
            self.my_score,
            self.opp_score,
            self.game_over,
        )


def make_snapshot(game, my_player, opp_player):
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
        my_chips   = [row[:] for row in my_player.playerBox],
        opp_chips  = [row[:] for row in opp_player.playerBox],
        my_hand    = list(my_player.playerCards),
        deck       = remaining_deck,
        my_score   = my_player.playerScore,
        opp_score  = opp_player.playerScore,
        game_over  = game.winner,
    )


def count_run(chip_grid, row, col, row_step, col_step):
    count = 0
    r, c = row, col
    while 0 <= r < 10 and 0 <= c < 10 and chip_grid[r][c]:
        count += 1
        r += row_step
        c += col_step
    return count


def would_complete_sequence(chip_grid, row, col):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for row_step, col_step in directions:
        forward  = count_run(chip_grid, row + row_step, col + col_step,  row_step,  col_step)
        backward = count_run(chip_grid, row - row_step, col - col_step, -row_step, -col_step)
        total = 1 + forward + backward 
        if total >= 6:
            return True
    return False


def get_valid_moves(state, is_my_turn):
    moves = []
    already_added = set() 

    if is_my_turn:
        cards_to_check = set(state.my_hand)
    else:
        cards_to_check = set(state.deck)

    for card in cards_to_check:
        if card in ONE_EYE_JACKS:
            target_grid = state.opp_chips if is_my_turn else state.my_chips
            for r in range(10):
                for c in range(10):
                    if BOARD[r][c] != "XX" and target_grid[r][c] and (r, c) not in already_added:
                        moves.append((card, r, c))
                        already_added.add((r, c))

        elif card in TWO_EYE_JACKS:
            for r in range(10):
                for c in range(10):
                    if BOARD[r][c] != "XX" and not state.my_chips[r][c] and not state.opp_chips[r][c]:
                        if (r, c) not in already_added:
                            moves.append((card, r, c))
                            already_added.add((r, c))

        else:
            for r in range(10):
                for c in range(10):
                    if BOARD[r][c] == card and not state.my_chips[r][c] and not state.opp_chips[r][c]:
                        if (r, c) not in already_added:
                            moves.append((card, r, c))
                            already_added.add((r, c))

    return moves


def apply_move(state, card, row, col, is_my_turn):
    new_state = state.copy()

    if card in ONE_EYE_JACKS:
        if is_my_turn:
            new_state.opp_chips[row][col] = 0
        else:
            new_state.my_chips[row][col] = 0

    else:
        if is_my_turn:
            new_state.my_chips[row][col] = 1
            if would_complete_sequence(new_state.my_chips, row, col):
                new_state.my_score += 1
                new_state.game_over = True
        else:
            new_state.opp_chips[row][col] = 1
            if would_complete_sequence(new_state.opp_chips, row, col):
                new_state.opp_score += 1
                new_state.game_over = True

    if is_my_turn and card in new_state.my_hand:
        new_state.my_hand.remove(card)
    if card in new_state.deck:
        new_state.deck.remove(card)

    return new_state


def draw_card(state, card):

    new_state = state.copy()
    if card in new_state.deck:
        new_state.deck.remove(card)
    new_state.my_hand.append(card)
    return new_state



def score_board(state):
    if state.game_over:
        if state.my_score >= 1:
            return 100000
        if state.opp_score >= 1:
            return -100000

    score = 0

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(10):
        for c in range(10):
            for dr, dc in directions:
                if state.my_chips[r][c]:
                    run = count_run(state.my_chips, r, c, dr, dc)
                    score += run * run
                if state.opp_chips[r][c]:
                    run = count_run(state.opp_chips, r, c, dr, dc)
                    score -= run * run

    return score


def sort_moves_best_first(moves, state, is_my_turn):
    def move_priority(move):
        card, r, c = move
        priority = 0

        grid = state.my_chips if is_my_turn else state.opp_chips
        temp_grid = [row[:] for row in grid]
        temp_grid[r][c] = 1
        if would_complete_sequence(temp_grid, r, c):
            priority += 1000

        if card in TWO_EYE_JACKS:
            priority += 30

        if card in ONE_EYE_JACKS:
            opp_grid = state.opp_chips if is_my_turn else state.my_chips
            if opp_grid[r][c]:
                priority += 15

        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            priority += count_run(grid, r, c, dr, dc)

        return priority

    return sorted(moves, key=move_priority, reverse=True)



class ExpectiminimaxAgent:
    def __init__(self, depth=2, max_moves=15):
        self.depth = depth
        self.max_moves = max_moves
        self.current_state = None

    def set_state(self, game, my_player, opp_player):
        """Snapshot the live game before each search."""
        self.current_state = make_snapshot(game, my_player, opp_player)

    def select_action(self, obs, valid_actions):
        if not valid_actions:
            return None
        if len(valid_actions) == 1:
            return valid_actions[0]

        state = self.current_state
        candidates = sort_moves_best_first(valid_actions, state, is_my_turn=True)
        candidates = candidates[:self.max_moves]

        best_score = float("-inf")
        best_move  = candidates[0]

        for card, r, c in candidates:
            next_state = apply_move(state, card, r, c, is_my_turn=True)
            score = self.chance_node(next_state, self.depth, float("-inf"), float("inf"))
            if score > best_score:
                best_score = score
                best_move  = (card, r, c)

        return best_move

    def max_node(self, state, depth, alpha, beta):
        if state.game_over or depth == 0:
            return score_board(state)

        moves = get_valid_moves(state, is_my_turn=True)
        if not moves:
            return score_board(state)

        moves = sort_moves_best_first(moves, state, True)[:self.max_moves]

        best = float("-inf")
        for card, r, c in moves:
            next_state = apply_move(state, card, r, c, is_my_turn=True)
            best = max(best, self.chance_node(next_state, depth, alpha, beta))
            alpha = max(alpha, best)
            if alpha >= beta:
                break  

        return best

    def chance_node(self, state, depth, alpha, beta):
       
        if not state.deck:
            return self.min_node(state, depth - 1, alpha, beta)

        card_counts = defaultdict(int)
        for card in state.deck:
            card_counts[card] += 1
        total_cards = len(state.deck)

        card_options = [(card, count / total_cards) for card, count in card_counts.items()]


        if len(card_options) > 8:
            card_options = random.sample(card_options, 8)
            total_prob = sum(p for _, p in card_options)
            card_options = [(c, p / total_prob) for c, p in card_options]

        expected_score = 0.0
        for card, probability in card_options:
            next_state = draw_card(state, card)
            expected_score += probability * self.min_node(next_state, depth - 1, alpha, beta)

        return expected_score

    def min_node(self, state, depth, alpha, beta):
        if state.game_over or depth == 0:
            return score_board(state)

        moves = get_valid_moves(state, is_my_turn=False)
        if not moves:
            return score_board(state)

        moves = sort_moves_best_first(moves, state, False)[:self.max_moves]

        worst = float("inf")
        for card, r, c in moves:
            next_state = apply_move(state, card, r, c, is_my_turn=False)
            worst = min(worst, self.max_node(next_state, depth, alpha, beta))
            beta = min(beta, worst)
            if alpha >= beta:
                break 

        return worst

class HeadlessPlayer:
    def __init__(self, name):
        self.playerName  = name
        self.playerScore = 0
        self.playerCards = []
        self.playerBox   = [[0] * 10 for _ in range(10)]
        self.playerBox[0][0] = self.playerBox[0][9] = 1
        self.playerBox[9][0] = self.playerBox[9][9] = 1

    def addCard(self, card):
        if card:
            self.playerCards.append(card)

    def hasWildCard(self):
        return "JC" in self.playerCards or "JD" in self.playerCards

    def getWildCard(self):
        return "JC" if "JC" in self.playerCards else "JD"

    def hasRemove(self):
        return "JH" in self.playerCards or "JS" in self.playerCards

    def getRemove(self):
        return "JH" if "JH" in self.playerCards else "JS"

    def hasChosenValid(self, x, y, opponent_box, card):
        if self.playerBox[x][y]:
            return False
        if opponent_box[x][y]:
            if self.hasRemove():
                self.playerCards.remove(self.getRemove())
                return 2
            return False
        if card in self.playerCards:
            self.playerCards.remove(card)
            return 1
        if self.hasWildCard():
            self.playerCards.remove(self.getWildCard())
            return 1
        return False


class HeadlessGame:
    def __init__(self):
        self.deck = [
            f"{rank}{suit}"
            for rank in list("KQJA") + list(map(str, range(2, 11)))
            for suit in "SHCD"
        ] * 2
        self.board  = BOARD
        self.used   = defaultdict(int)
        self.filled = [[0] * 10 for _ in range(10)]
        self.winner = False
        random.shuffle(self.deck)

    def distribute(self, player, num_cards=5):
        for _ in range(num_cards):
            player.addCard(self.getNewCard())

    def getNewCard(self):
        while self.deck:
            card = self.deck.pop()
            if self.used[card] < 2:
                self.used[card] += 1
                return card
        return False

    def checkSequence(self, x, y, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            total = 1
            for sign in (1, -1):
                nr, nc = x + sign * dr, y + sign * dc
                while 0 <= nr < 10 and 0 <= nc < 10 and player.playerBox[nr][nc]:
                    total += 1
                    nr += sign * dr
                    nc += sign * dc
            if total >= 6:
                player.playerScore += 1
        if player.playerScore > 0:
            self.winner = True

    def setBox(self, player, opponent_box, x, y):
        if self.board[x][y] == "XX":
            return False
        ok = player.hasChosenValid(x, y, opponent_box, self.board[x][y])
        if ok == 1:
            player.playerBox[x][y] = 1
            self.checkSequence(x, y, player)
            self.filled[x][y] = 1
        elif ok == 2:
            self.filled[x][y] = 0
            opponent_box[x][y] = 0
        return ok

    def make_bot_move(self, bot, challenger):
        for _ in range(200):
            if not bot.playerCards:
                return False
            card = random.choice(bot.playerCards)

            if card in ("JH", "JS"):
                for r in range(10):
                    for c in range(10):
                        if self.board[r][c] != "XX" and challenger.playerBox[r][c]:
                            challenger.playerBox[r][c] = 0
                            bot.playerCards.remove(card)
                            self.filled[r][c] = 0
                            bot.addCard(self.getNewCard())
                            return (r, c, 0)
                bot.playerCards.remove(card)
                bot.addCard(self.getNewCard())
                return False

            elif card in ("JD", "JC"):
                for r in range(10):
                    for c in range(10):
                        if (self.board[r][c] != "XX"
                                and bot.playerBox[r][c] == 0
                                and challenger.playerBox[r][c] == 0):
                            bot.playerBox[r][c] = 1
                            self.filled[r][c] = 1
                            self.checkSequence(r, c, bot)
                            bot.playerCards.remove(card)
                            bot.addCard(self.getNewCard())
                            return (r, c, 1)
                bot.playerCards.remove(card)
                bot.addCard(self.getNewCard())
                return False

            else:
                for r in range(10):
                    for c in range(10):
                        if (self.board[r][c] == card
                                and bot.playerBox[r][c] == 0
                                and challenger.playerBox[r][c] == 0):
                            bot.playerBox[r][c] = 1
                            self.filled[r][c] = 1
                            self.checkSequence(r, c, bot)
                            bot.playerCards.remove(card)
                            bot.addCard(self.getNewCard())
                            return (r, c, 1)
                bot.playerCards.remove(card)
                bot.addCard(self.getNewCard())
                return False
        return False


def get_agent_actions(game, agent_player, bot_player):
    actions = []
    for card in set(agent_player.playerCards):
        if card in ("JH", "JS"):
            for r in range(10):
                for c in range(10):
                    if bot_player.playerBox[r][c]:
                        actions.append((card, r, c))
        elif card in ("JD", "JC"):
            for r in range(10):
                for c in range(10):
                    if (game.board[r][c] != "XX"
                            and agent_player.playerBox[r][c] == 0
                            and bot_player.playerBox[r][c] == 0):
                        actions.append((card, r, c))
        else:
            for r in range(10):
                for c in range(10):
                    if (game.board[r][c] == card
                            and agent_player.playerBox[r][c] == 0
                            and bot_player.playerBox[r][c] == 0):
                        actions.append((card, r, c))
    return actions


def run_experiment(num_games=5, depth=2, max_moves=15):
    
    DIVIDER      = "─" * 60
    THICK_DIVIDER = "═" * 60

    print(f"\n{THICK_DIVIDER}")
    print(f"  SEQUENCE EXPERIMENT")
    print(f"  Agent : ExpectiminimaxAgent (depth={depth}, max_moves={max_moves})")
    print(f"  Bot   : RandomAgent")
    print(f"  Games : {num_games}")
    print(f"{THICK_DIVIDER}\n")

    all_results = []

    for game_num in range(1, num_games + 1):
        game       = HeadlessGame()
        agent_player = HeadlessPlayer("agent")
        bot_player   = HeadlessPlayer("bot")
        game.distribute(agent_player)
        game.distribute(bot_player)

        agent      = ExpectiminimaxAgent(depth=depth, max_moves=max_moves)
        move_times = []
        num_turns  = 0
        outcome    = "draw"

        game_start = time.perf_counter()

        while num_turns < 500:  
    
            actions = get_agent_actions(game, agent_player, bot_player)
            if not actions:
                outcome = "loss"
                break

            t0 = time.perf_counter()
            agent.set_state(game, agent_player, bot_player)
            chosen = agent.select_action(None, actions)
            move_times.append(time.perf_counter() - t0)

            card, x, y = chosen
            ok = game.setBox(agent_player, bot_player.playerBox, x, y)
            if ok:
                agent_player.addCard(game.getNewCard())
            num_turns += 1

            if game.winner:
                outcome = "win" if agent_player.playerScore >= 1 else "loss"
                break
            if not game.deck:
                outcome = "draw"
                break

            for _ in range(20):  # retry if bot can't move
                if game.make_bot_move(bot_player, agent_player) is not False:
                    break
            num_turns += 1

            if game.winner:
                outcome = "win" if agent_player.playerScore >= 1 else "loss"
                break
            if not game.deck:
                outcome = "draw"
                break

        game_time = time.perf_counter() - game_start
        avg_move_ms = (sum(move_times) / len(move_times) * 1000) if move_times else 0
        max_move_ms = (max(move_times) * 1000)                   if move_times else 0

        all_results.append({
            "outcome"    : outcome,
            "turns"      : num_turns,
            "game_time"  : game_time,
            "avg_move_ms": avg_move_ms,
            "max_move_ms": max_move_ms,
            "agent_score": agent_player.playerScore,
            "bot_score"  : bot_player.playerScore,
            "num_moves"  : len(move_times),
        })

        icon = {"win": "WIN", "loss": "LOSS", "draw": "DRAW"}[outcome]
        print(f"  Game {game_num}  [{icon}]")
        print(f"  {DIVIDER}")
        print(f"  Score        : Agent {agent_player.playerScore} - Bot {bot_player.playerScore}")
        print(f"  Turns played : {num_turns}  (agent made {len(move_times)} moves)")
        print(f"  Game time    : {game_time:.2f}s")
        print(f"  Avg move time: {avg_move_ms:.1f}ms")
        print(f"  Max move time: {max_move_ms:.1f}ms")
        print()

    wins   = sum(1 for r in all_results if r["outcome"] == "win")
    losses = sum(1 for r in all_results if r["outcome"] == "loss")
    draws  = sum(1 for r in all_results if r["outcome"] == "draw")
    total_time    = sum(r["game_time"]   for r in all_results)
    avg_game_time = total_time / num_games
    avg_move_time = sum(r["avg_move_ms"] for r in all_results) / num_games

    print(f"{THICK_DIVIDER}")
    print(f"  FINAL RESULTS  ({num_games} games)")
    print(f"{THICK_DIVIDER}")
    print(f"  Wins   : {wins} / {num_games}  ({100 * wins / num_games:.0f}%)")
    print(f"  Losses : {losses} / {num_games}  ({100 * losses / num_games:.0f}%)")
    print(f"  Draws  : {draws} / {num_games}  ({100 * draws / num_games:.0f}%)")
    print(f"  {DIVIDER}")
    print(f"  Total runtime  : {total_time:.2f}s")
    print(f"  Avg game time  : {avg_game_time:.2f}s")
    print(f"  Avg move time  : {avg_move_time:.1f}ms")
    print(f"{THICK_DIVIDER}\n")

    return all_results


if __name__ == "__main__":
    run_experiment(num_games=5, depth=2, max_moves=15)