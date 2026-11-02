# app.py  –  TypeSprint Typing Speed Game
# =========================================================
# This is the main file. Run it with:
#   python -m streamlit run app.py
#
# HOW STREAMLIT WORKS (beginner note):
#   Every time you click a button or type something, Streamlit
#   re-runs this whole Python file from top to bottom.
#   That means normal variables reset every time.
#   We use  st.session_state  (a special dictionary) to keep
#   important values alive across those reruns.
# =========================================================

import time          # used to measure how many seconds have passed
import random        # used to shuffle and pick words
import streamlit as st  # the main framework that builds the website

# streamlit_autorefresh makes the page refresh automatically every second
# so the countdown timer ticks smoothly without the user having to type.
# It is a tiny, single-purpose helper – it does not touch the game logic.
from streamlit_autorefresh import st_autorefresh

# st_keyup provides a text input that sends its value to Python on EVERY
# keystroke. The standard st.text_area() only sends text when thpye user
# presses Ctrl+Enter, which is too slow for a live typing test.
# st_keyup triggers a page rerun on each key press, so Python always
# has the latest typed text immediately.
from st_keyup import st_keyup

# Import our word lists from words.py
from words import EASY_WORDS, MEDIUM_WORDS, HARD_WORDS


# =========================================================
# SECTION 1: PAGE CONFIGURATION
# =========================================================
# This must be the very first Streamlit call in the file.
st.set_page_config(
    page_title="TypeSprint",
    page_icon="⌨️",
    layout="centered",
)


# =========================================================
# SECTION 2: THEME STYLES
# =========================================================
# We use a small amount of CSS here because Streamlit does not
# have built-in light/dark theme switching that we can control
# ourselves. This CSS changes background colours and text colours.
# Nothing here affects game logic – it is purely visual.

DARK_CSS = """
<style>
/* Dark theme: dark background, light text */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #1a1a2e !important;
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] { background-color: #16213e !important; }
/* Style the st_keyup input container */
.stTextInput input, iframe { border-radius: 6px !important; }
.stButton > button {
    background-color: #e94560 !important;
    color: white !important;
    border-radius: 8px !important;
}
/* Style the target text box */
.target-box {
    background-color: #0f3460;
    color: #e0e0e0;
    padding: 16px;
    border-radius: 8px;
    font-size: 1.15rem;
    line-height: 1.8;
    border: 1px solid #e94560;
    font-family: monospace;
}
/* Result numbers */
.big-number { font-size: 2.5rem; font-weight: bold; color: #e94560; }
.label-text { font-size: 0.9rem; color: #aaa; margin-top: -10px; }
</style>
"""

LIGHT_CSS = """
<style>
/* Light theme: white background, dark text */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #f5f5f5 !important;
    color: #1a1a1a !important;
}
[data-testid="stSidebar"] { background-color: #e8e8e8 !important; }
.stTextInput input, iframe { border-radius: 6px !important; }
.stButton > button {
    background-color: #0066cc !important;
    color: white !important;
    border-radius: 8px !important;
}
.target-box {
    background-color: #ffffff;
    color: #1a1a1a;
    padding: 16px;
    border-radius: 8px;
    font-size: 1.15rem;
    line-height: 1.8;
    border: 1px solid #0066cc;
    font-family: monospace;
}
.big-number { font-size: 2.5rem; font-weight: bold; color: #0066cc; }
.label-text { font-size: 0.9rem; color: #555; margin-top: -10px; }

/* Streamlit widgets set their own text color, so they ignore the
   color on the page background. We have to target them directly. */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stSlider"] p,
[data-testid="stSliderTickBarMin"],
[data-testid="stSliderTickBarMax"],
[data-testid="stCaptionContainer"] {
    color: #1a1a1a !important;
}
[data-testid="stAlert"] p {
    color: #1a1a1a !important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * {
    color: #555 !important;
}


</style>
"""



# =========================================================
# SECTION 3: HELPER FUNCTIONS
# =========================================================
# Functions are reusable blocks of code. We define them here
# and call them later in the app.

def get_word_list(difficulty):
    """Return the correct word list based on the chosen difficulty."""
    if difficulty == "Easy":
        return EASY_WORDS
    elif difficulty == "Medium":
        return MEDIUM_WORDS
    else:
        return HARD_WORDS  # Hard


def build_target_text(difficulty, num_words=60):
    """
    Pick 'num_words' random words from the right word list and
    join them into a single string separated by spaces.

    We use random.sample() so no word repeats in one session.
    If the list is shorter than num_words, we repeat the list first.
    """
    word_list = get_word_list(difficulty)

    # Make sure we always have enough words by repeating the list if needed
    while len(word_list) < num_words:
        word_list = word_list + word_list  # double the list

    chosen = random.sample(word_list, num_words)
    return " ".join(chosen)  # join into one string: "cat sun fish ..."


def calculate_results(target_text, typed_text, elapsed_seconds):
    """
    Calculate WPM, accuracy, and number of correct words.

    Parameters:
        target_text   – the words the user was supposed to type
        typed_text    – what the user actually typed
        elapsed_seconds – how many seconds the user spent typing

    Returns a dictionary with the results.
    """

    # Split both texts into lists of individual words
    target_words = target_text.split()
    typed_words  = typed_text.strip().split()

    # --- Count correct words ---
    # We compare each typed word with the matching target word.
    correct_words = 0
    for i in range(len(typed_words)):
        if i < len(target_words):           # make sure there IS a target word
            if typed_words[i] == target_words[i]:
                correct_words += 1

    # --- Calculate WPM ---
    # WPM = correctly typed words / time in minutes
    # We protect against division by zero: if time < 1 second, use 1 second.
    elapsed_minutes = max(elapsed_seconds, 1) / 60
    wpm = round(correct_words / elapsed_minutes)

    # --- Calculate accuracy ---
    # We compare character by character.
    # Only count as many characters as the user actually typed.



# Count how many words the user typed
    typed_words = typed_text.split()
    target_words = target_text.split()

    total_typed_words = len(typed_words)
    correct_typed_words = 0

    # Compare each typed word with the target word
    for i in range(total_typed_words):
        if i < len(target_words):
            if typed_words[i] == target_words[i]:
                correct_typed_words += 1

    # Calculate word accuracy
    if total_typed_words > 0:
        accuracy = round(
            (correct_typed_words / total_typed_words) * 100, 1
        )
    else:
        accuracy = 0


    return {
        "wpm":           wpm,
        "accuracy":      accuracy,
        "correct_words": correct_words,
        "elapsed":       round(elapsed_seconds),
    }


def reset_game_state():
    """
    Clear all the game-related values in session_state so a new
    game starts fresh. We keep the user's settings (difficulty,
    duration, theme) because those should survive a restart.
    """
    st.session_state.game_started   = False   # has the user started typing?
    st.session_state.game_over      = False   # has the game ended?
    st.session_state.start_time     = None    # when did the user start typing?
    st.session_state.target_text    = ""      # what the user must type
    st.session_state.typed_text     = ""      # what the user has typed so far
    st.session_state.results        = None    # final WPM / accuracy / words
    st.session_state.input_key      = st.session_state.get("input_key", 0) + 1
    # ↑ Changing input_key forces Streamlit to create a fresh text area widget,
    #   which clears any text the user had typed before.


# =========================================================
# SECTION 4: INITIALISE SESSION STATE
# =========================================================
# The first time the app loads, none of these keys exist yet.
# We set safe default values here so the rest of the code can
# always read them without crashing.

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"


if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"

if "duration" not in st.session_state:
    st.session_state.duration = 40   # seconds

if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "game_over" not in st.session_state:
    st.session_state.game_over = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "target_text" not in st.session_state:
    st.session_state.target_text = ""

if "typed_text" not in st.session_state:
    st.session_state.typed_text = ""

if "results" not in st.session_state:
    st.session_state.results = None

if "input_key" not in st.session_state:
    st.session_state.input_key = 0


# =========================================================
# SECTION 5: APPLY THEME
# =========================================================
# Inject the CSS for whichever theme the user has chosen.
if st.session_state.theme == "Dark":
    st.markdown(DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)


# =========================================================
# SECTION 6: AUTO-REFRESH (timer tick)
# =========================================================
# While the game is running, we refresh the page every 500 ms
# so the countdown display updates smoothly.
# When the game is not running, we do NOT refresh automatically
# (that would waste resources and feel glitchy).

is_game_running = (
    st.session_state.game_started
    and not st.session_state.game_over
)

if is_game_running:
    # Refresh every 500 milliseconds (half a second).
    # The count variable is just a counter – we don't use its value.
    st_autorefresh(interval=500, key="timer_refresh")


# =========================================================
# SECTION 7: HEADER
# =========================================================
st.title("⌨️ TypeSprint")
st.markdown("*Test your typing speed. Choose a difficulty and duration, then start typing!*")
st.divider()


# =========================================================
# SECTION 8: SETTINGS PANEL
# =========================================================
# We hide settings while a game is actively running so the user
# can't accidentally change difficulty mid-game. They reappear
# after the game ends.

settings_locked = st.session_state.game_started and not st.session_state.game_over

if not settings_locked:
    st.subheader("⚙️ Settings")

    col1, col2 = st.columns(2)

    with col1:
        # Duration selector
        new_duration = st.select_slider(
            "Duration (seconds)",
            options=[20, 40, 60],
            value=st.session_state.duration,
        )
        if new_duration != st.session_state.duration:
            st.session_state.duration = new_duration

        # Difficulty selector
        new_difficulty = st.radio(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty),
        )
        if new_difficulty != st.session_state.difficulty:
            st.session_state.difficulty = new_difficulty
            reset_game_state()
            st.rerun()

    with col2:
        # Theme selectorx``
        new_theme = st.radio(
            "Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.theme == "Dark" else 1,
        )
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()  # rerun to apply the new CSS immediately

    st.divider()


# =========================================================
# SECTION 9: GENERATE TARGET TEXT
# =========================================================
# If no target text exists yet (start of a new game), we generate
# one now. This happens once per game, not every rerun.

if st.session_state.target_text == "":
    st.session_state.target_text = build_target_text(st.session_state.difficulty)


# =========================================================
# SECTION 10: GAME AREA
# =========================================================
st.subheader("🎮 Game")

# --- Show difficulty and duration badge ---
st.markdown(
    f"⏱️ **Timed Challenge** &nbsp;|&nbsp; "
    f"**{st.session_state.difficulty}** difficulty"
    f" &nbsp;|&nbsp; ⏳ **{st.session_state.duration}s**",
    unsafe_allow_html=True,
)

# ---- TIMER LOGIC (Timed Challenge only) ----
# We calculate time BEFORE showing anything, so every widget on
# the page uses the same consistent value this rerun.

elapsed_seconds  = 0
remaining_seconds = st.session_state.duration  # default: full time remaining

if st.session_state.game_started and st.session_state.start_time is not None:
    elapsed_seconds   = time.time() - st.session_state.start_time
    remaining_seconds = st.session_state.duration - elapsed_seconds

    # Check if time has run out
    if remaining_seconds <= 0 and not st.session_state.game_over:
        # Game over! Calculate and store results, then mark game as done.
        elapsed_seconds = st.session_state.duration  # use full duration for fairness
        st.session_state.results = calculate_results(
            st.session_state.target_text,
            st.session_state.typed_text,
            elapsed_seconds,
        )
        st.session_state.game_over = True
        st.rerun()  # rerun to show the results screen

# ---- DISPLAY TIMER ----
if not st.session_state.game_started:
    # Timer hasn't started yet
    st.info(
        f"⏳ **{st.session_state.duration}s** — "
        "Timer starts when you type your first character."
    )
elif not st.session_state.game_over:
    # Game is running – show live countdown
    secs_left = max(0, int(remaining_seconds))
    pct_left  = secs_left / st.session_state.duration

    # Colour the countdown based on urgency
    if secs_left > 15:
        timer_colour = "🟢"
    elif secs_left > 5:
        timer_colour = "🟡"
    else:
        timer_colour = "🔴"

    st.markdown(f"### {timer_colour} Time remaining: **{secs_left}s**")
    st.progress(pct_left)   # visual bar showing time remaining


# ---- TARGET TEXT BOX ----
if not st.session_state.game_over:
    st.markdown("**Type the text below:**")
    st.markdown(
        f'<div class="target-box">{st.session_state.target_text}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")  # small visual gap


# =========================================================
# SECTION 11: RESULTS SCREEN
# =========================================================
# Shown after the game ends (when the timer runs out).

if st.session_state.game_over and st.session_state.results is not None:
    res = st.session_state.results
    st.success("✅ Game Over! Here are your results:")
    st.divider()

    # Display the three main metrics in three side-by-side columns
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f'<div class="big-number">{res["wpm"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="label-text">Words per Minute (WPM)</div>', unsafe_allow_html=True)
    with r2:
        st.markdown(f'<div class="big-number">{res["accuracy"]}%</div>', unsafe_allow_html=True)
        st.markdown('<div class="label-text">Accuracy</div>', unsafe_allow_html=True)
    with r3:
        st.markdown(f'<div class="big-number">{res["correct_words"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="label-text">Correct Words</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown(f"⏱️ Time elapsed: **{res['elapsed']} seconds**")

    # --- Play Again button ---
    if st.button("🔄 Play Again", use_container_width=True):
        reset_game_state()
        st.rerun()


# =========================================================
# SECTION 12: TYPING INPUT
# =========================================================
# We only show the input area when the game is NOT over.
#
# WHY st_keyup instead of st.text_area?
#   st.text_area only sends its value to Python when the user
#   presses Ctrl+Enter. That means mid-game, Python might be
#   working with outdated text.
#   st_keyup fires a Streamlit rerun on EVERY keystroke, so
#   Python always has the latest typed text right away.
#
# The `key` includes input_key so that reset_game_state()
# (which increments input_key) forces a fresh, empty input.

elif not st.session_state.game_over:

    # st_keyup returns whatever the user has typed so far.
    # It returns None before the user has typed anything.
    typed = st_keyup(
        label="Your typing — just start typing, no need to press Enter:",
        key=f"typing_input_{st.session_state.input_key}",
    )

    # Treat None (nothing typed yet) as an empty string
    if typed is None:
        typed = ""

    # --- Detect when the user starts typing ---
    # The very first character triggers the timer to start.
    if typed and not st.session_state.game_started:
        st.session_state.game_started = True
        st.session_state.start_time   = time.time()
        st.session_state.typed_text   = typed
        st.rerun()  # rerun immediately to show the live countdown

    elif typed != st.session_state.typed_text:
        # User has typed more — update the stored text
        st.session_state.typed_text = typed

    # ---- Live word count hint ----
    if st.session_state.game_started:
        typed_word_count = len(typed.strip().split()) if typed.strip() else 0
        target_word_count = len(st.session_state.target_text.strip().split())
        st.caption(f"Words typed so far: {typed_word_count} / {target_word_count}")

    # ---- CASE B: Early completion ----
    # If the user has typed all target words correctly before the
    # timer runs out, end the game immediately and show results.
    #
    # How it works:
    #   1. Split both texts into word lists.
    #   2. Check that the user has typed at least as many words
    #      as the target.
    #   3. Check that every target word matches the typed word
    #      at the same position.
    #   4. If all match, calculate elapsed time and end the game.
    if st.session_state.game_started and typed.strip():
        target_words = st.session_state.target_text.strip().split()
        typed_words  = typed.strip().split()

        if len(typed_words) >= len(target_words):
            # Check every single target word matches what was typed
            all_match = all(
                typed_words[i] == target_words[i]
                for i in range(len(target_words))
            )
            if all_match:
                # Player finished the full target text early!
                # Elapsed time = now minus when they started typing.
                actual_elapsed = time.time() - st.session_state.start_time
                st.session_state.results = calculate_results(
                    st.session_state.target_text,
                    typed,
                    actual_elapsed,
                )
                st.session_state.game_over = True
                st.rerun()  # show the results screen now


# =========================================================
# SECTION 13: FOOTER
# =========================================================
st.divider()
st.caption("TypeSprint — Built with Python & Streamlit  |  AIE1101 Vibe Coding Project")

