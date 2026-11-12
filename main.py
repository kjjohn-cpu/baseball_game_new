from drafter import *
from dataclasses import dataclass
from bakery import assert_equal
import random
import matplotlib.pyplot as plt


# ADVANCED TECHNIQUES USED
# - Dataclasses organize each player's statistics and the full application state.
# - State stores a list of Player objects; routes update the selected object.
# - Loops process base runners, player lists, and derby scores.
# - Conditional logic handles batting outcomes, innings, difficulty, and ties.
# - Helper functions separate scoring, runner movement, and inning transitions.
# - Matplotlib creates a bar chart from the selected player's statistics.
# - Drafter routes use the shared State object to move between website pages.


@dataclass
class Player:
    name: str
    singles: int
    doubles: int
    triples: int
    home_runs: int
    hits: int


@dataclass
class State:
    inning: int
    half_inning: str
    outs: int
    balls: int
    strikes: int
    player_score: int
    computer_score: int
    first_base: bool
    second_base: bool
    third_base: bool
    game_over: bool
    last_result: str
    difficulty: str
    total_innings: int
    derby_difficulty: str
    derby_players: int
    derby_scores: list[int]
    derby_player: int
    derby_swings: int
    derby_over: bool
    stats_players: list[Player]
    current_batter_index: int


# -------------------------
# QUICK PLAY FUNCTIONS
# -------------------------

def random_batting_result(state: State) -> str:
    """Choose a randomized batting result using the computer or player odds.

    Args:
        state: Current game state, including half-inning and difficulty.

    Returns:
        The result of this pitch or swing.

    This function is not unit tested because its result depends on randomness."""
    number = random.randint(1, 100)

    # Computer batting odds
    if state.half_inning == "Top":
        if number <= 30:
            return "Out"
        elif number <= 50:
            return "Single"
        elif number <= 60:
            return "Double"
        elif number <= 63:
            return "Triple"
        elif number <= 65:
            return "Home Run"
        elif number <= 80:
            return "Strike"
        elif number <= 95:
            return "Ball"
        else:
            return "Foul"

    # Player batting odds: Easy
    if state.difficulty == "Easy":
        if number <= 15:
            return "Out"
        elif number <= 45:
            return "Single"
        elif number <= 60:
            return "Double"
        elif number <= 67:
            return "Triple"
        elif number <= 75:
            return "Home Run"
        elif number <= 83:
            return "Strike"
        elif number <= 95:
            return "Ball"
        else:
            return "Foul"

    # Player batting odds: Medium
    elif state.difficulty == "Medium":
        if number <= 25:
            return "Out"
        elif number <= 50:
            return "Single"
        elif number <= 65:
            return "Double"
        elif number <= 72:
            return "Triple"
        elif number <= 77:
            return "Home Run"
        elif number <= 85:
            return "Strike"
        elif number <= 95:
            return "Ball"
        else:
            return "Foul"

    # Player batting odds: Hard
    else:
        if number <= 35:
            return "Out"
        elif number <= 55:
            return "Single"
        elif number <= 70:
            return "Double"
        elif number <= 76:
            return "Triple"
        elif number <= 79:
            return "Home Run"
        elif number <= 87:
            return "Strike"
        elif number <= 95:
            return "Ball"
        else:
            return "Foul"


def record_player_hit(state: State, result: str) -> None:
    """Add a hit and its hit type to the current HOME batter's statistics.

    Args:
        state: Current game state and batting lineup.
        result: One of Single, Double, Triple, or Home Run.

    Returns:
        None. The selected Player object is updated in place."""
    """Record a hit for the current batter in the HOME lineup."""
    if state.half_inning == "Bottom":
        player = state.stats_players[state.current_batter_index]

        player.hits += 1

        if result == "Single":
            player.singles += 1
        elif result == "Double":
            player.doubles += 1
        elif result == "Triple":
            player.triples += 1
        elif result == "Home Run":
            player.home_runs += 1


def advance_batter(state: State) -> None:
    """Move the HOME batting order to its next player, wrapping at the end.

    Args:
        state: Current game state containing the lineup index.

    Returns:
        None. The current_batter_index field is updated."""
    """Move to the next player in the batting order."""
    state.current_batter_index += 1

    if state.current_batter_index >= len(state.stats_players):
        state.current_batter_index = 0


def add_run(state: State) -> None:
    """Add one run to the team currently batting.

    Args:
        state: Current game state, used to identify the batting team.

    Returns:
        None. One team's score is increased by one."""
    if state.half_inning == "Top":
        state.computer_score += 1
    else:
        state.player_score += 1


def advance_runners(state: State, bases: int) -> None:
    """Advance every existing runner and the batter by a given number of bases.

    Args:
        state: Current game state containing base occupancy and scores.
        bases: Number of bases awarded to the batter (1, 2, or 3).

    Returns:
        None. Base occupancy and the batting team's score are updated."""
    # Copy the base flags first so each runner's destination is calculated
    # from the original play, not from a base that was just updated.
    runners = [
        state.first_base,
        state.second_base,
        state.third_base
    ]

    new_bases = [False, False, False]

    for i in range(3):
        if runners[i]:
            destination = i + bases

            if destination >= 3:
                add_run(state)
            else:
                new_bases[destination] = True

    # The batter starts at home, so a single/double/triple places them at
    # first/second/third base respectively.
    batter_destination = bases - 1

    if batter_destination >= 3:
        add_run(state)
    else:
        new_bases[batter_destination] = True

    state.first_base = new_bases[0]
    state.second_base = new_bases[1]
    state.third_base = new_bases[2]


def walk(state: State) -> None:
    """Award the batter first base and force any occupied bases to advance.

    Args:
        state: Current game state containing the base runners.

    Returns:
        None. Forced runners advance and a bases-loaded walk scores a run."""
    if state.first_base:
        if state.second_base:
            if state.third_base:
                add_run(state)
            state.third_base = True
        state.second_base = True

    state.first_base = True


def switch_sides(state: State) -> None:
    """Finish a half-inning, clear the bases and count, and advance the game.

    Args:
        state: Current game state, including inning and final scores.

    Returns:
        None. The half-inning changes or the game is marked over."""
    state.outs = 0
    state.balls = 0
    state.strikes = 0
    state.first_base = False
    state.second_base = False
    state.third_base = False

    # A complete inning consists of the Top (AWAY) and Bottom (HOME).
    if state.half_inning == "Top":
        state.half_inning = "Bottom"

    else:
        if state.inning >= state.total_innings:
            if state.player_score > state.computer_score:
                state.game_over = True
                state.last_result = "GAME OVER! HOME WINS!"

            elif state.computer_score > state.player_score:
                state.game_over = True
                state.last_result = "GAME OVER! AWAY WINS!"

            else:
                state.inning += 1
                state.half_inning = "Top"

        else:
            state.inning += 1
            state.half_inning = "Top"


def baseball_diamond(state: State) -> Table:
    first = "🟩" if state.first_base else "⬜"
    second = "🟩" if state.second_base else "⬜"
    third = "🟩" if state.third_base else "⬜"

    return Table([
        ["", second + " SECOND BASE", ""],
        [third + " THIRD BASE", "", first + " FIRST BASE"],
        ["", "◇ HOME PLATE", ""]
    ])


# -------------------------
# MAIN MENU
# -------------------------

@route
def index(state: State) -> Page:
    """Display the website's main menu.

    Args:
        state: Current application state passed between Drafter routes.

    Returns:
        A Page containing links to Quick Play, Home Run Derby, and Stats.

    This page route is best checked through a browser integration test."""
    return Page(state, [
        Header("BASEBALL GAME"),
        Text("Welcome to the baseball game!"),
        Button("QUICK PLAY", "quick_play"),
        Button("HOME RUN DERBY", "derby_menu"),
        Button("STATS", "stats")
    ])


# -------------------------
# QUICK PLAY SETUP
# -------------------------

@route
def quick_play(state: State) -> Page:
    """Display Quick Play settings and the current batting lineup.

    Args:
        state: Current application state with difficulty, innings, and players.

    Returns:
        A Page containing setup controls and the lineup.

    This page route is best checked through a browser integration test."""
    return Page(state, [
        Header("QUICK PLAY SETUP"),

        Text("Choose Difficulty"),
        SelectBox(
            "difficulty",
            ["Easy", "Medium", "Hard"],
            state.difficulty
        ),

        Text("Choose Number of Innings"),
        SelectBox(
            "innings",
            ["3", "6", "9"],
            str(state.total_innings)
        ),

        Button("UPDATE SETTINGS", "update_settings"),

        Text("Selected Difficulty: " + state.difficulty),
        Text("Selected Innings: " + str(state.total_innings)),

        Text("Your batting lineup:"),
        *[
            Text(str(i + 1) + ". " + player.name)
            for i, player in enumerate(state.stats_players)
        ],

        Button("START GAME", "start_game"),
        Button("MAIN MENU", "index")
    ])


@route
def update_settings(state: State, difficulty: str,
                    innings: str) -> Page:
    """Save the selected Quick Play difficulty and inning count.

    Args:
        state: Current application state to update.
        difficulty: Selected Easy, Medium, or Hard setting.
        innings: Selected inning count as text (3, 6, or 9).

    Returns:
        The refreshed Quick Play setup Page."""
    state.difficulty = difficulty
    state.total_innings = int(innings)

    return quick_play(state)


# -------------------------
# PLAYER STATS
# -------------------------

@route
def stats(state: State) -> Page:
    """Display the player selector for Quick Play batting statistics.

    Args:
        state: Current application state containing the Player objects.

    Returns:
        A Page with a player SelectBox and navigation buttons.

    This page route is best checked through a browser integration test."""
    return Page(state, [
        Header("PLAYER STATS"),
        Text("Choose a player to view their Quick Play batting statistics."),
        SelectBox(
            "player_name",
            [player.name for player in state.stats_players],
            state.stats_players[0].name
        ),
        Button("VIEW STATS", "show_stats"),
        Button("MAIN MENU", "index")
    ])


@route
def show_stats(state: State, player_name: str) -> Page:
    """Find a player and display their batting totals in a bar chart.

    Args:
        state: Current application state containing the stats lineup.
        player_name: Name selected in the Stats page dropdown.

    Returns:
        A Page containing the selected player's chart and totals.

    Matplotlib rendering is best checked in a running Drafter website."""
    selected_player = None

    # Search the list of Player objects for the name chosen in the dropdown.
    for player in state.stats_players:
        if player.name == player_name:
            selected_player = player

    if selected_player is None:
        return stats(state)

    categories = ["Singles", "Doubles", "Triples", "Home Runs", "Hits"]
    values = [
        selected_player.singles,
        selected_player.doubles,
        selected_player.triples,
        selected_player.home_runs,
        selected_player.hits
    ]

    plt.figure()
    plt.bar(categories, values)
    plt.title(selected_player.name + " - Quick Play Stats")
    plt.xlabel("Statistic")
    plt.ylabel("Total")
    plt.tight_layout()

    return Page(state, [
        Header(selected_player.name + " - STATS"),
        MatPlotLibPlot(),
        Text("Singles: " + str(selected_player.singles)),
        Text("Doubles: " + str(selected_player.doubles)),
        Text("Triples: " + str(selected_player.triples)),
        Text("Home Runs: " + str(selected_player.home_runs)),
        Text("Total Hits: " + str(selected_player.hits)),
        Button("CHOOSE ANOTHER PLAYER", "stats"),
        Button("MAIN MENU", "index")
    ])


# -------------------------
# START QUICK PLAY
# -------------------------

@route
def start_game(state: State) -> Page:
    """Reset Quick Play to the first inning and show the game page.

    Args:
        state: Current application state to reset for a new game.

    Returns:
        The first Quick Play game Page."""
    state.inning = 1
    state.half_inning = "Top"
    state.outs = 0
    state.balls = 0
    state.strikes = 0
    state.player_score = 0
    state.computer_score = 0
    state.first_base = False
    state.second_base = False
    state.third_base = False
    state.game_over = False
    state.last_result = "Ready to play!"
    state.current_batter_index = 0

    return game_page(state)


# -------------------------
# QUICK PLAY GAME PAGE
# -------------------------

def game_page(state: State) -> Page:
    """Build the Quick Play scoreboard, diamond, count, and game controls.

    Args:
        state: Current game state used to construct the display.

    Returns:
        A Page showing the current game or its final score."""
    inning_arrow = "↑" if state.half_inning == "Top" else "↓"
    inning_display = str(state.inning) + inning_arrow

    page_content = [
        Table([
            ["INNING", "HOME", "AWAY"],
            [
                inning_display,
                str(state.player_score),
                str(state.computer_score)
            ]
        ]),

        Text("HOME: Player"),
        Text("AWAY: Computer")
    ]

    if state.half_inning == "Bottom" and not state.game_over:
        current_batter = state.stats_players[state.current_batter_index]
        page_content.append(
            Text("Now batting: " + current_batter.name)
        )

    page_content.extend([
        baseball_diamond(state),
        Text("Outs: " + str(state.outs)),
        Text("Balls: " + str(state.balls)),
        Text("Strikes: " + str(state.strikes)),
        Text("Last Play: " + state.last_result)
    ])

    if state.game_over:
        page_content.append(Text("FINAL SCORE"))
        page_content.append(
            Text(
                "HOME: " + str(state.player_score) +
                " | AWAY: " + str(state.computer_score)
            )
        )
        page_content.append(Button("MAIN MENU", "index"))

    else:
        button_text = "PITCH!" if state.half_inning == "Top" else "SWING!"
        page_content.append(Button(button_text, "swing"))

    return Page(state, page_content)
# -------------------------
# QUICK PLAY SWING
# -------------------------

@route
def swing(state: State) -> Page:
    """Process one randomized pitch or swing during Quick Play.

    Args:
        state: Current game state, updated with the batting result.

    Returns:
        The refreshed Quick Play game Page.

    This route is not unit tested because its outcome depends on randomness;
    test it by playing both halves of an inning in the running website."""
    if state.game_over:
        return game_page(state)

    batting_half = state.half_inning
    result = random_batting_result(state)
    plate_appearance_over = False

    # Record hits for the current HOME batter.
    if result in ["Single", "Double", "Triple", "Home Run"]:
        record_player_hit(state, result)

    if result == "Strike":
        state.strikes += 1

        if state.strikes >= 3:
            state.outs += 1
            state.strikes = 0
            state.balls = 0
            result = "Strike three! You're out!"
            plate_appearance_over = True

    elif result == "Ball":
        state.balls += 1

        if state.balls >= 4:
            walk(state)
            state.balls = 0
            state.strikes = 0
            result = "Walk! Batter advances to first!"
            plate_appearance_over = True

    elif result == "Foul":
        if state.strikes < 2:
            state.strikes += 1

        result = "Foul ball!"

    elif result == "Out":
        state.outs += 1
        state.balls = 0
        state.strikes = 0
        result = "You're out!"
        plate_appearance_over = True

    elif result == "Single":
        advance_runners(state, 1)
        state.balls = 0
        state.strikes = 0
        result = "Single!"
        plate_appearance_over = True

    elif result == "Double":
        advance_runners(state, 2)
        state.balls = 0
        state.strikes = 0
        result = "Double!"
        plate_appearance_over = True

    elif result == "Triple":
        advance_runners(state, 3)
        state.balls = 0
        state.strikes = 0
        result = "Triple!"
        plate_appearance_over = True

    elif result == "Home Run":
        runs = 1

        if state.first_base:
            runs += 1
        if state.second_base:
            runs += 1
        if state.third_base:
            runs += 1

        for _ in range(runs):
            add_run(state)

        state.first_base = False
        state.second_base = False
        state.third_base = False
        state.balls = 0
        state.strikes = 0

        result = "HOME RUN! " + str(runs) + " runs scored!"
        plate_appearance_over = True

    state.last_result = result

    # A plate appearance ends on a hit, out, strikeout, or walk, but not on
    # an ordinary ball, strike, or foul. Only HOME batters use the lineup.
    # Move to the next HOME batter after a completed at-bat.
    # This happens before switching sides so the lineup continues
    # from the correct player when HOME bats again.
    if plate_appearance_over and batting_half == "Bottom":
        advance_batter(state)

    if state.outs >= 3:
        switch_sides(state)

        if not state.game_over:
            state.last_result += " Three outs! Switching sides!"

    return game_page(state)


# -------------------------
# HOME RUN DERBY SETUP
# -------------------------

@route
def derby_menu(state: State) -> Page:
    """Display the Home Run Derby player-count and difficulty settings.

    Args:
        state: Current application state containing derby settings.

    Returns:
        A Page with derby setup controls."""
    return Page(state, [
        Header("HOME RUN DERBY SETUP"),

        Text("Choose Number of Players"),
        Text("Selected: " + str(state.derby_players) + " players"),

        Button("2 PLAYERS", "derby_two"),
        Button("4 PLAYERS", "derby_four"),
        Button("8 PLAYERS", "derby_eight"),

        Text("Choose Difficulty"),
        Text("Selected: " + state.derby_difficulty),

        Button("EASY", "derby_easy"),
        Button("MEDIUM", "derby_medium"),
        Button("HARD", "derby_hard"),

        Button("START DERBY", "start_derby"),
        Button("MAIN MENU", "index")
    ])


# -------------------------
# DERBY PLAYER COUNT
# -------------------------

@route
def derby_two(state: State) -> Page:
    """Set the Home Run Derby to two participants.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_players = 2
    return derby_menu(state)


@route
def derby_four(state: State) -> Page:
    """Set the Home Run Derby to four participants.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_players = 4
    return derby_menu(state)


@route
def derby_eight(state: State) -> Page:
    """Set the Home Run Derby to eight participants.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_players = 8
    return derby_menu(state)


# -------------------------
# DERBY DIFFICULTY
# -------------------------

@route
def derby_easy(state: State) -> Page:
    """Set Home Run Derby difficulty to Easy.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_difficulty = "Easy"
    return derby_menu(state)


@route
def derby_medium(state: State) -> Page:
    """Set Home Run Derby difficulty to Medium.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_difficulty = "Medium"
    return derby_menu(state)


@route
def derby_hard(state: State) -> Page:
    """Set Home Run Derby difficulty to Hard.

    Args:
        state: Current application state to update.

    Returns:
        The refreshed Home Run Derby setup Page."""
    state.derby_difficulty = "Hard"
    return derby_menu(state)


# -------------------------
# START HOME RUN DERBY
# -------------------------

@route
def start_derby(state: State) -> Page:
    """Reset the derby scores and begin Player 1's ten-swing turn.

    Args:
        state: Current application state to initialize for a new derby.

    Returns:
        The Home Run Derby game Page."""
    state.derby_scores = [0] * state.derby_players
    state.derby_player = 1
    state.derby_swings = 0
    state.derby_over = False
    state.last_result = "Player 1 is up!"

    return derby_game_page(state)


# -------------------------
# HOME RUN DERBY GAME PAGE
# -------------------------

def derby_game_page(state: State) -> Page:
    """Build the derby scoreboard, current turn, and final winner display.

    Args:
        state: Current derby state used to construct the display.

    Returns:
        A Page showing the derby standings and controls or winner."""
    score_rows = [["PLAYER", "HOME RUNS"]]

    for i in range(state.derby_players):
        score_rows.append([
            "Player " + str(i + 1),
            str(state.derby_scores[i])
        ])

    page_content = [
        Table(score_rows),
        Text("Difficulty: " + state.derby_difficulty)
    ]

    if state.derby_over:
        page_content.append(Text("HOME RUN DERBY FINISHED!"))

        # max() finds the winning score; collecting all matching indexes
        # correctly supports a tie instead of assuming one winner.
        high_score = max(state.derby_scores)
        winners = []

        for i in range(state.derby_players):
            if state.derby_scores[i] == high_score:
                winners.append("Player " + str(i + 1))

        if len(winners) == 1:
            page_content.append(
                Text(
                    winners[0] + " WINS with " +
                    str(high_score) + " home runs!"
                )
            )
        else:
            page_content.append(
                Text(
                    "TIE! " + ", ".join(winners) +
                    " finished with " + str(high_score) + " home runs!"
                )
            )

        page_content.append(Button("MAIN MENU", "index"))

    else:
        page_content.append(
            Text("Player " + str(state.derby_player) + "'s turn")
        )
        page_content.append(
            Text("Swings: " + str(state.derby_swings) + " / 10")
        )
        page_content.append(
            Text("Swings left: " + str(10 - state.derby_swings))
        )
        page_content.append(Text(state.last_result))
        page_content.append(Button("SWING!", "derby_swing"))

    return Page(state, page_content)


# -------------------------
# HOME RUN DERBY SWING
# -------------------------

@route
def derby_swing(state: State) -> Page:
    """Process one randomized Home Run Derby swing and advance turns.

    Args:
        state: Current derby state, updated with the swing result.

    Returns:
        The refreshed Home Run Derby game Page.

    This route is not unit tested because each swing is randomized; test it
    by completing a derby in the running website."""
    if state.derby_over:
        return derby_game_page(state)

    number = random.randint(1, 100)

    if state.derby_difficulty == "Easy":
        home_run_chance = 35
    elif state.derby_difficulty == "Medium":
        home_run_chance = 25
    else:
        home_run_chance = 15

    state.derby_swings += 1

    if number <= home_run_chance:
        state.derby_scores[state.derby_player - 1] += 1
        state.last_result = "HOME RUN!"
    else:
        state.last_result = "OUT!"

    if state.derby_swings >= 10:
        if state.derby_player < state.derby_players:
            state.derby_player += 1
            state.derby_swings = 0
            state.last_result += (
                " Player " + str(state.derby_player) + " is up!"
            )
        else:
            state.derby_over = True

    return derby_game_page(state)



# -------------------------
# UNIT TESTS FOR GAME LOGIC
# -------------------------

def make_test_state() -> State:
    """Create a fresh, predictable State object for unit tests.

    Returns:
        A State with a three-player lineup and no runners on base.
    """
    return State(
        inning=1,
        half_inning="Bottom",
        outs=0,
        balls=0,
        strikes=0,
        player_score=0,
        computer_score=0,
        first_base=False,
        second_base=False,
        third_base=False,
        game_over=False,
        last_result="Testing",
        difficulty="Medium",
        total_innings=3,
        derby_difficulty="Medium",
        derby_players=2,
        derby_scores=[0, 0],
        derby_player=1,
        derby_swings=0,
        derby_over=False,
        stats_players=[
            Player("Test Batter 1", 0, 0, 0, 0, 0),
            Player("Test Batter 2", 0, 0, 0, 0, 0),
            Player("Test Batter 3", 0, 0, 0, 0, 0),
        ],
        current_batter_index=0,
    )


def run_unit_tests() -> None:
    """Run deterministic tests for the game's state-changing helper functions.

    Returns:
        None. assert_equal raises an error if a tested result is incorrect.

    Random swing routes and page-only routes are tested manually in the live
    website because they depend on randomness or Drafter's browser interface.
    Deterministic setup routes are also called directly below.
    """
    test_state = make_test_state()

    # Check that each hit is recorded on the current HOME batter.
    record_player_hit(test_state, "Single")
    assert_equal(test_state.stats_players[0].singles, 1)
    assert_equal(test_state.stats_players[0].hits, 1)

    # Check that the batting order advances and wraps to its first player.
    advance_batter(test_state)
    assert_equal(test_state.current_batter_index, 1)
    test_state.current_batter_index = 2
    advance_batter(test_state)
    assert_equal(test_state.current_batter_index, 0)

    # Check that a runner scores on a single and the batter reaches first.
    test_state.third_base = True
    advance_runners(test_state, 1)
    assert_equal(test_state.player_score, 1)
    assert_equal(test_state.first_base, True)
    assert_equal(test_state.third_base, False)

    # Check that a bases-loaded walk forces one run home.
    test_state.first_base = True
    test_state.second_base = True
    test_state.third_base = True
    walk(test_state)
    assert_equal(test_state.player_score, 2)
    assert_equal(test_state.first_base, True)
    assert_equal(test_state.second_base, True)
    assert_equal(test_state.third_base, True)

    # Check that add_run credits the correct team in each half-inning.
    add_run(test_state)
    assert_equal(test_state.player_score, 3)
    test_state.half_inning = "Top"
    add_run(test_state)
    assert_equal(test_state.computer_score, 1)

    # Check that switching from the Top moves play to the Bottom and clears
    # the count, outs, and bases.
    test_state.half_inning = "Top"
    test_state.outs = 3
    test_state.balls = 2
    test_state.strikes = 1
    switch_sides(test_state)
    assert_equal(test_state.half_inning, "Bottom")
    assert_equal(test_state.outs, 0)
    assert_equal(test_state.balls, 0)
    assert_equal(test_state.strikes, 0)
    assert_equal(test_state.first_base, False)
    assert_equal(test_state.second_base, False)
    assert_equal(test_state.third_base, False)

    # The deterministic setup routes can be called directly in unit tests.
    update_settings(test_state, "Hard", "6")
    assert_equal(test_state.difficulty, "Hard")
    assert_equal(test_state.total_innings, 6)

    derby_two(test_state)
    assert_equal(test_state.derby_players, 2)
    derby_four(test_state)
    assert_equal(test_state.derby_players, 4)
    derby_eight(test_state)
    assert_equal(test_state.derby_players, 8)

    derby_easy(test_state)
    assert_equal(test_state.derby_difficulty, "Easy")
    derby_medium(test_state)
    assert_equal(test_state.derby_difficulty, "Medium")
    derby_hard(test_state)
    assert_equal(test_state.derby_difficulty, "Hard")

    # Starting a game or derby should reset its counters and status.
    test_state.inning = 4
    test_state.outs = 2
    start_game(test_state)
    assert_equal(test_state.inning, 1)
    assert_equal(test_state.outs, 0)
    assert_equal(test_state.current_batter_index, 0)

    test_state.derby_scores = [5, 4, 3, 2, 1, 0, 0, 0]
    test_state.derby_swings = 9
    test_state.derby_over = True
    start_derby(test_state)
    assert_equal(test_state.derby_scores, [0, 0, 0, 0, 0, 0, 0, 0])
    assert_equal(test_state.derby_swings, 0)
    assert_equal(test_state.derby_player, 1)
    assert_equal(test_state.derby_over, False)


# Run the deterministic tests before starting the website. If a test fails,
# fix the logic before submitting or deploying the project.
run_unit_tests()


# -------------------------
# START SERVER
# -------------------------

start_server(State(
    inning=1,
    half_inning="Top",
    outs=0,
    balls=0,
    strikes=0,
    player_score=0,
    computer_score=0,
    first_base=False,
    second_base=False,
    third_base=False,
    game_over=False,
    last_result="Ready to play!",
    difficulty="Medium",
    total_innings=9,
    derby_difficulty="Medium",
    derby_players=2,
    derby_scores=[0, 0],
    derby_player=1,
    derby_swings=0,
    derby_over=False,
    stats_players=[
        Player("Babe Ruth", 0, 0, 0, 0, 0),
        Player("Jackie Robinson", 0, 0, 0, 0, 0),
        Player("Hank Aaron", 0, 0, 0, 0, 0),
        Player("Derek Jeter", 0, 0, 0, 0, 0),
        Player("Shohei Ohtani", 0, 0, 0, 0, 0),
        Player("Mike Trout", 0, 0, 0, 0, 0),
        Player("Willie Mays", 0, 0, 0, 0, 0),
        Player("Barry Bonds", 0, 0, 0, 0, 0)
    ],
    current_batter_index=0
))
