import streamlit as st
import pandas as pd
import sys
import os

# Add project directories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from simulation.match_sim import MatchSimulator


# Initialize database and simulator
@st.cache_resource
def init_app():
    db = DatabaseManager()
    simulator = MatchSimulator()
    return db, simulator


def main():
    st.set_page_config(
        page_title="Football Simulator",
        page_icon="⚽",
        layout="wide"
    )

    # Initialize app components
    db, simulator = init_app()

    # Sidebar navigation
    st.sidebar.title("⚽ Football Simulator")

    # Game state info
    current_gw = db.get_current_gameweek()
    user_team = db.get_user_team()

    st.sidebar.info(f"""
    **Current Status:**
    - Gameweek: {current_gw}
    - Your Team: {user_team}
    """)

    # Navigation menu
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Home"

    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Home", "📅 Fixtures", "📊 League Table", "⚙️ Settings", "🎮 Admin"],
        index=["🏠 Home", "📅 Fixtures", "📊 League Table", "⚙️ Settings", "🎮 Admin"].index(st.session_state.page)
    )

    st.session_state.page = page

    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page(db, simulator)
    elif page == "📅 Fixtures":
        show_fixtures_page(db, simulator)
    elif page == "📊 League Table":
        show_league_table(db)
    elif page == "⚙️ Settings":
        show_settings_page(db)
    elif page == "🎮 Admin":
        show_admin_page(db)


def show_home_page(db, simulator):
    st.title("⚽ Football Manager Simulator")
    st.write("Welcome to your football simulation experience!")

    current_gw = db.get_current_gameweek()
    user_team = db.get_user_team()

    # Quick stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Current Gameweek", current_gw)

    with col2:
        st.metric("Your Team", user_team)

    with col3:
        # Get user team's league position
        table = db.get_league_table()
        user_position = next((team['position'] for team in table if team['team'] == user_team), "N/A")
        st.metric("League Position", user_position)

    st.divider()

    # Current gameweek preview
    st.subheader(f"Gameweek {current_gw} Fixtures")

    fixtures = db.get_gameweek_fixtures(current_gw)

    if fixtures:
        for fixture in fixtures:
            col1, col2, col3 = st.columns([2, 1, 2])

            with col1:
                st.write(f"**{fixture['home_team']}**")

            with col2:
                if fixture['is_played']:
                    st.write(f"{fixture['home_goals']} - {fixture['away_goals']}")
                else:
                    if fixture['is_user_team']:
                        st.write("🎮 YOUR MATCH")
                    else:
                        st.write("vs")

            with col3:
                st.write(f"**{fixture['away_team']}**")
    else:
        st.info("No fixtures loaded yet. Go to Admin page to set up teams and fixtures.")

    # Quick actions
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📅 View This Week's Fixtures", use_container_width=True):
            st.session_state.page = "📅 Fixtures"
            st.rerun()

        with col2:
            if st.button("📊 View League Table", use_container_width=True):
                st.session_state.page = "📊 League Table"
                st.rerun()


def show_fixtures_page(db, simulator):
    st.title("📅 Fixtures & Results")

    current_gw = db.get_current_gameweek()
    user_team = db.get_user_team()

    # Gameweek selector
    selected_gw = st.selectbox("Select Gameweek:", range(1, 39), index=current_gw - 1)

    fixtures = db.get_gameweek_fixtures(selected_gw)

    if not fixtures:
        st.warning(f"No fixtures found for Gameweek {selected_gw}")
        return

    st.subheader(f"Gameweek {selected_gw}")

    # Separate user fixtures from others
    user_fixtures = [f for f in fixtures if f['is_user_team']]
    other_fixtures = [f for f in fixtures if not f['is_user_team']]

    # Handle user team fixtures
    if user_fixtures and selected_gw == current_gw:
        st.write("### 🎮 Your Match")

        user_fixture = user_fixtures[0]

        if not user_fixture['is_played']:
            # Input form for user match
            with st.form(f"user_match_{user_fixture['id']}"):
                st.write(f"**{user_fixture['home_team']} vs {user_fixture['away_team']}**")

                col1, col2 = st.columns(2)
                with col1:
                    home_goals = st.number_input(f"{user_fixture['home_team']} Goals",
                                                 min_value=0, max_value=10, value=0)
                with col2:
                    away_goals = st.number_input(f"{user_fixture['away_team']} Goals",
                                                 min_value=0, max_value=10, value=0)

                if st.form_submit_button("Submit Result", use_container_width=True):
                    db.update_fixture_result(user_fixture['id'], home_goals, away_goals)
                    st.success(
                        f"Result submitted: {user_fixture['home_team']} {home_goals}-{away_goals} {user_fixture['away_team']}")
                    st.rerun()
        else:
            # Show completed user match
            st.success(
                f"✅ **{user_fixture['home_team']} {user_fixture['home_goals']}-{user_fixture['away_goals']} {user_fixture['away_team']}**")

    # Show other fixtures
    if other_fixtures:
        st.write("### Other Matches")

        # Check if we can simulate (user match must be played first for current gameweek)
        can_simulate = True
        if selected_gw == current_gw and user_fixtures:
            can_simulate = user_fixtures[0]['is_played']

        if selected_gw == current_gw and not can_simulate:
            st.info("Complete your match first to simulate other fixtures!")

        # Simulation controls
        if can_simulate and selected_gw == current_gw:
            col1, col2 = st.columns([1, 3])

            with col1:
                sim_level = st.selectbox("Simulation Level:",
                                         ["basic", "rating", "stats"],
                                         index=0)

            with col2:
                if st.button("⚽ Simulate All Remaining Matches", use_container_width=True):
                    simulate_gameweek_matches(db, simulator, other_fixtures, sim_level)
                    st.rerun()

        # Display fixtures
        for fixture in other_fixtures:
            col1, col2, col3, col4 = st.columns([3, 2, 3, 1])

            with col1:
                st.write(f"**{fixture['home_team']}**")

            with col2:
                if fixture['is_played']:
                    st.write(f"**{fixture['home_goals']} - {fixture['away_goals']}**")
                else:
                    st.write("vs")

            with col3:
                st.write(f"**{fixture['away_team']}**")

            with col4:
                if not fixture['is_played'] and can_simulate and selected_gw == current_gw:
                    if st.button("Sim", key=f"sim_{fixture['id']}"):
                        simulate_single_match(db, simulator, fixture, sim_level)
                        st.rerun()

    # Advance gameweek button
    if selected_gw == current_gw:
        st.divider()

        # Check if all matches are completed
        all_played = all(f['is_played'] for f in fixtures)

        if all_played:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("➡️ Advance to Next Gameweek", use_container_width=True):
                    db.advance_gameweek()
                    db.update_league_table()
                    st.success(f"Advanced to Gameweek {current_gw + 1}!")
                    st.rerun()

            with col2:
                if st.button("📊 View Updated Table", use_container_width=True):
                    db.update_league_table()
                    st.switch_page("📊 League Table")
        else:
            remaining = len([f for f in fixtures if not f['is_played']])
            st.info(f"Complete all matches to advance gameweek ({remaining} matches remaining)")


def simulate_gameweek_matches(db, simulator, fixtures, sim_level):
    """Simulate all remaining fixtures in the gameweek"""
    for fixture in fixtures:
        if not fixture['is_played']:
            simulate_single_match(db, simulator, fixture, sim_level)


def simulate_single_match(db, simulator, fixture, sim_level):
    """Simulate a single match"""
    # Get team stats
    home_stats = db.get_team_stats(fixture['home_team']) or {'overall_rating': 50}
    away_stats = db.get_team_stats(fixture['away_team']) or {'overall_rating': 50}

    # Simulate the match
    result = simulator.simulate_match(
        fixture['home_team'],
        fixture['away_team'],
        home_stats,
        away_stats,
        sim_level
    )

    # Update the database
    db.update_fixture_result(fixture['id'], result['home_goals'], result['away_goals'])


def show_league_table(db):
    st.title("📊 Premier League Table")

    # Update table first
    db.update_league_table()
    table = db.get_league_table()

    if not table:
        st.warning("No league data available. Set up teams first!")
        return

    # Convert to DataFrame for better display
    df = pd.DataFrame(table)

    # Style the table
    def style_table(row):
        styles = [''] * len(row)

        # Highlight user team
        user_team = db.get_user_team()
        if row['team'] == user_team:
            styles = ['background-color: #e8f4f8; font-weight: bold'] * len(row)

        # Color code positions
        elif row['position'] <= 4:  # Champions League
            styles[0] = 'background-color: #90EE90'  # Light green
        elif row['position'] <= 6:  # Europa League
            styles[0] = 'background-color: #FFE4B5'  # Light orange
        elif row['position'] >= 18:  # Relegation
            styles[0] = 'background-color: #FFB6C1'  # Light red

        return styles

    # Display table
    st.dataframe(
        df.style.apply(style_table, axis=1),
        column_config={
            "position": st.column_config.NumberColumn("Pos", width="small"),
            "team": st.column_config.TextColumn("Team", width="medium"),
            "played": st.column_config.NumberColumn("P", width="small"),
            "won": st.column_config.NumberColumn("W", width="small"),
            "drawn": st.column_config.NumberColumn("D", width="small"),
            "lost": st.column_config.NumberColumn("L", width="small"),
            "goals_for": st.column_config.NumberColumn("GF", width="small"),
            "goals_against": st.column_config.NumberColumn("GA", width="small"),
            "goal_difference": st.column_config.NumberColumn("GD", width="small"),
            "points": st.column_config.NumberColumn("Pts", width="small"),
            "form": st.column_config.TextColumn("Form", width="small")
        },
        hide_index=True,
        use_container_width=True
    )

    # League position info
    user_team = db.get_user_team()
    user_pos = next((team['position'] for team in table if team['team'] == user_team), None)

    if user_pos:
        col1, col2, col3 = st.columns(3)

        with col1:
            if user_pos <= 4:
                st.success(f"🏆 Champions League Position ({user_pos})")
            elif user_pos <= 6:
                st.info(f"🥉 Europa League Position ({user_pos})")
            elif user_pos >= 18:
                st.error(f"⬇️ Relegation Zone ({user_pos})")
            else:
                st.write(f"📍 Mid-table ({user_pos})")

        with col2:
            user_data = next(team for team in table if team['team'] == user_team)
            st.metric("Points", user_data['points'])

        with col3:
            st.metric("Goal Difference",
                      f"+{user_data['goal_difference']}" if user_data['goal_difference'] >= 0 else str(
                          user_data['goal_difference']))


def show_settings_page(db):
    st.title("⚙️ Settings")

    # User team selection
    st.subheader("Team Settings")

    # Get all teams
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM teams ORDER BY name')
        teams = [row[0] for row in cursor.fetchall()]

    current_user_team = db.get_user_team()

    if teams:
        selected_team = st.selectbox("Choose your team:", teams,
                                     index=teams.index(current_user_team) if current_user_team in teams else 0)

        if st.button("Update Team"):
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE game_state SET user_team = ? WHERE id = 1', (selected_team,))
                conn.commit()
            st.success(f"Team updated to {selected_team}!")
            st.rerun()

    st.divider()

    # Simulation settings
    st.subheader("Simulation Settings")

    sim_level = st.selectbox("Default Simulation Level:",
                             ["basic", "rating", "stats", "realistic"],
                             index=0)

    st.info("Simulation level will be used as default for auto-simulations")

    st.divider()

    # Season reset
    st.subheader("⚠️ Danger Zone")

    if st.button("🔄 Reset Season", type="secondary"):
        if st.button("⚠️ Confirm Reset - This will delete all progress!", type="primary"):
            reset_season(db)
            st.success("Season reset successfully!")
            st.rerun()


def show_admin_page(db):
    st.title("🎮 Admin Panel")

    tab1, tab2, tab3 = st.tabs(["Teams", "Fixtures", "Database"])

    with tab1:
        st.subheader("Team Management")

        # Add new team
        with st.form("add_team"):
            st.write("**Add New Team**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                team_name = st.text_input("Team Name")
            with col2:
                attack = st.number_input("Attack Rating", 1, 100, 50)
            with col3:
                defense = st.number_input("Defense Rating", 1, 100, 50)
            with col4:
                overall = st.number_input("Overall Rating", 1, 100, 50)

            if st.form_submit_button("Add Team"):
                if team_name:
                    if db.add_team(team_name, attack, defense, overall):
                        st.success(f"Added {team_name}!")
                        st.rerun()
                    else:
                        st.error("Team already exists!")

        # Show existing teams
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, attack_rating, defense_rating, overall_rating FROM teams ORDER BY name')
            teams_data = cursor.fetchall()

        if teams_data:
            st.write("**Existing Teams**")
            teams_df = pd.DataFrame(teams_data, columns=['Team', 'Attack', 'Defense', 'Overall'])
            st.dataframe(teams_df, hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("Fixture Management")

        # Quick setup for Premier League
        if st.button("🏴󠁧󠁢󠁥󠁮󠁧󠁿 Setup Premier League Teams", use_container_width=True):
            setup_premier_league_teams(db)
            st.success("Premier League teams added!")
            st.rerun()

        # Add individual fixture
        with st.form("add_fixture"):
            st.write("**Add Fixture**")

            # Get teams for dropdown
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM teams ORDER BY name')
                teams = [row[0] for row in cursor.fetchall()]

            if len(teams) >= 2:
                col1, col2, col3 = st.columns(3)

                with col1:
                    gameweek = st.number_input("Gameweek", 1, 38, 1)
                with col2:
                    home_team = st.selectbox("Home Team", teams)
                with col3:
                    away_team = st.selectbox("Away Team", [t for t in teams if t != home_team])

                if st.form_submit_button("Add Fixture"):
                    db.add_fixture(gameweek, home_team, away_team)
                    st.success(f"Added: {home_team} vs {away_team} (GW{gameweek})")
                    st.rerun()
            else:
                st.warning("Add at least 2 teams first!")

    with tab3:
        st.subheader("Database Status")

        # Show database stats
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM teams')
            team_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM fixtures')
            fixture_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM fixtures WHERE is_played = TRUE')
            played_count = cursor.fetchone()[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Teams", team_count)
        with col2:
            st.metric("Fixtures", fixture_count)
        with col3:
            st.metric("Matches Played", played_count)

        # Database actions
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Recalculate League Table"):
                db.update_league_table()
                st.success("League table updated!")

        with col2:
            if st.button("📊 View Raw Data"):
                show_raw_database_data(db)


def setup_premier_league_teams(db):
    """Add all Premier League teams with realistic ratings"""
    premier_league_teams = [
        # Team, Attack, Defense, Overall
        ("Arsenal", 85, 80, 83),
        ("Manchester City", 95, 85, 90),
        ("Manchester United", 75, 70, 73),
        ("Liverpool", 88, 82, 85),
        ("Chelsea", 78, 75, 77),
        ("Tottenham", 80, 65, 73),
        ("Newcastle United", 70, 75, 73),
        ("Brighton", 68, 72, 70),
        ("Aston Villa", 75, 70, 73),
        ("West Ham", 65, 68, 67),
        ("Crystal Palace", 60, 70, 65),
        ("Fulham", 70, 65, 68),
        ("Wolves", 58, 72, 65),
        ("Everton", 55, 65, 60),
        ("Brentford", 72, 62, 67),
        ("Nottingham Forest", 58, 68, 63),
        ("Luton Town", 50, 55, 53),
        ("Burnley", 52, 60, 56),
        ("Sheffield United", 45, 50, 48),
        ("Bournemouth", 62, 58, 60)
    ]

    for team_name, attack, defense, overall in premier_league_teams:
        db.add_team(team_name, attack, defense, overall)


def show_raw_database_data(db):
    """Show raw database tables for debugging"""

    st.subheader("Raw Database Data")

    tab1, tab2, tab3, tab4 = st.tabs(["Teams", "Fixtures", "League Table", "Game State"])

    with tab1:
        with db.get_connection() as conn:
            teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
            st.dataframe(teams_df, use_container_width=True)

    with tab2:
        with db.get_connection() as conn:
            fixtures_df = pd.read_sql_query("SELECT * FROM fixtures ORDER BY gameweek, id", conn)
            st.dataframe(fixtures_df, use_container_width=True)

    with tab3:
        with db.get_connection() as conn:
            table_df = pd.read_sql_query("SELECT * FROM league_table ORDER BY points DESC", conn)
            st.dataframe(table_df, use_container_width=True)

    with tab4:
        with db.get_connection() as conn:
            state_df = pd.read_sql_query("SELECT * FROM game_state", conn)
            st.dataframe(state_df, use_container_width=True)


def reset_season(db):
    """Reset the entire season"""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Reset fixtures
        cursor.execute('UPDATE fixtures SET home_goals = NULL, away_goals = NULL, is_played = FALSE')

        # Reset league table
        cursor.execute(
            'UPDATE league_table SET played=0, won=0, drawn=0, lost=0, goals_for=0, goals_against=0, goal_difference=0, points=0, form=""')

        # Reset game state
        cursor.execute('UPDATE game_state SET current_gameweek = 1')

        conn.commit()


if __name__ == "__main__":
    main()