import sqlite3
import os
from typing import List, Dict, Tuple, Optional


class DatabaseManager:
    def __init__(self, db_path: str = "data/football.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()

    def ensure_db_directory(self):
        """Create the data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    attack_rating INTEGER DEFAULT 50,
                    defense_rating INTEGER DEFAULT 50,
                    overall_rating INTEGER DEFAULT 50,
                    goals_scored INTEGER DEFAULT 0,
                    goals_conceded INTEGER DEFAULT 0,
                    home_goals_scored INTEGER DEFAULT 0,
                    away_goals_scored INTEGER DEFAULT 0,
                    home_goals_conceded INTEGER DEFAULT 0,
                    away_goals_conceded INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    home_games_played INTEGER DEFAULT 0,
                    away_games_played INTEGER DEFAULT 0
                )
            ''')

            # Fixtures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fixtures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gameweek INTEGER NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    is_played BOOLEAN DEFAULT FALSE,
                    is_user_team BOOLEAN DEFAULT FALSE,
                    date TEXT,
                    FOREIGN KEY (home_team) REFERENCES teams (name),
                    FOREIGN KEY (away_team) REFERENCES teams (name)
                )
            ''')

            # League table (calculated view)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS league_table (
                    team_name TEXT PRIMARY KEY,
                    played INTEGER DEFAULT 0,
                    won INTEGER DEFAULT 0,
                    drawn INTEGER DEFAULT 0,
                    lost INTEGER DEFAULT 0,
                    goals_for INTEGER DEFAULT 0,
                    goals_against INTEGER DEFAULT 0,
                    goal_difference INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    form TEXT DEFAULT '',
                    FOREIGN KEY (team_name) REFERENCES teams (name)
                )
            ''')

            # Game state table (to track current gameweek, season progress)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY,
                    current_gameweek INTEGER DEFAULT 1,
                    season_year TEXT DEFAULT '2024-25',
                    user_team TEXT DEFAULT 'Sheffield United'
                )
            ''')

            conn.commit()

            # Initialize game state if not exists
            cursor.execute('SELECT COUNT(*) FROM game_state')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO game_state (id, current_gameweek) VALUES (1, 1)')
                conn.commit()

    def add_team(self, name: str, attack: int = 50, defense: int = 50, overall: int = 50):
        """Add a team to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO teams (name, attack_rating, defense_rating, overall_rating)
                    VALUES (?, ?, ?, ?)
                ''', (name, attack, defense, overall))

                # Also add to league table
                cursor.execute('''
                    INSERT OR IGNORE INTO league_table (team_name)
                    VALUES (?)
                ''', (name,))

                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Team already exists

    def add_fixture(self, gameweek: int, home_team: str, away_team: str, date: str = None):
        """Add a fixture to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if this involves the user team
            user_team = self.get_user_team()
            is_user_team = (home_team == user_team or away_team == user_team)

            cursor.execute('''
                INSERT INTO fixtures (gameweek, home_team, away_team, date, is_user_team)
                VALUES (?, ?, ?, ?, ?)
            ''', (gameweek, home_team, away_team, date, is_user_team))
            conn.commit()

    def get_current_gameweek(self) -> int:
        """Get the current gameweek"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT current_gameweek FROM game_state WHERE id = 1')
            result = cursor.fetchone()
            return result[0] if result else 1

    def get_user_team(self) -> str:
        """Get the user's team"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_team FROM game_state WHERE id = 1')
            result = cursor.fetchone()
            return result[0] if result else 'Sheffield United'

    def get_gameweek_fixtures(self, gameweek: int) -> List[Dict]:
        """Get all fixtures for a specific gameweek"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, home_team, away_team, home_goals, away_goals, is_played, is_user_team
                FROM fixtures 
                WHERE gameweek = ?
                ORDER BY is_user_team DESC, home_team
            ''', (gameweek,))

            fixtures = []
            for row in cursor.fetchall():
                fixtures.append({
                    'id': row[0],
                    'home_team': row[1],
                    'away_team': row[2],
                    'home_goals': row[3],
                    'away_goals': row[4],
                    'is_played': bool(row[5]),
                    'is_user_team': bool(row[6])
                })
            return fixtures

    def update_fixture_result(self, fixture_id: int, home_goals: int, away_goals: int):
        """Update a fixture with the match result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE fixtures 
                SET home_goals = ?, away_goals = ?, is_played = TRUE
                WHERE id = ?
            ''', (home_goals, away_goals, fixture_id))
            conn.commit()

    def get_league_table(self) -> List[Dict]:
        """Get current league table ordered by points"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT team_name, played, won, drawn, lost, 
                       goals_for, goals_against, goal_difference, points, form
                FROM league_table 
                ORDER BY points DESC, goal_difference DESC, goals_for DESC
            ''')

            table = []
            for i, row in enumerate(cursor.fetchall(), 1):
                table.append({
                    'position': i,
                    'team': row[0],
                    'played': row[1],
                    'won': row[2],
                    'drawn': row[3],
                    'lost': row[4],
                    'goals_for': row[5],
                    'goals_against': row[6],
                    'goal_difference': row[7],
                    'points': row[8],
                    'form': row[9]
                })
            return table

    def update_league_table(self):
        """Recalculate the entire league table based on played fixtures"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Reset all league table stats
            cursor.execute(
                'UPDATE league_table SET played=0, won=0, drawn=0, lost=0, goals_for=0, goals_against=0, goal_difference=0, points=0, form=""')

            # Get all played fixtures
            cursor.execute('''
                SELECT home_team, away_team, home_goals, away_goals
                FROM fixtures 
                WHERE is_played = TRUE
            ''')

            for home_team, away_team, home_goals, away_goals in cursor.fetchall():
                # Update home team stats
                self._update_team_stats(cursor, home_team, home_goals, away_goals, True)
                # Update away team stats
                self._update_team_stats(cursor, away_team, away_goals, home_goals, False)

            conn.commit()

    def _update_team_stats(self, cursor, team: str, goals_for: int, goals_against: int, is_home: bool):
        """Helper method to update individual team stats"""
        # Determine result
        if goals_for > goals_against:
            won, drawn, lost, points = 1, 0, 0, 3
        elif goals_for == goals_against:
            won, drawn, lost, points = 0, 1, 0, 1
        else:
            won, drawn, lost, points = 0, 0, 1, 0

        cursor.execute('''
            UPDATE league_table 
            SET played = played + 1,
                won = won + ?,
                drawn = drawn + ?,
                lost = lost + ?,
                goals_for = goals_for + ?,
                goals_against = goals_against + ?,
                goal_difference = goals_for - goals_against,
                points = points + ?
            WHERE team_name = ?
        ''', (won, drawn, lost, goals_for, goals_against, points, team))

    def advance_gameweek(self):
        """Move to the next gameweek"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE game_state 
                SET current_gameweek = current_gameweek + 1 
                WHERE id = 1
            ''')
            conn.commit()

    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Get detailed stats for a specific team"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT attack_rating, defense_rating, overall_rating,
                       goals_scored, goals_conceded, games_played
                FROM teams 
                WHERE name = ?
            ''', (team_name,))

            result = cursor.fetchone()
            if result:
                return {
                    'attack_rating': result[0],
                    'defense_rating': result[1],
                    'overall_rating': result[2],
                    'goals_scored': result[3],
                    'goals_conceded': result[4],
                    'games_played': result[5]
                }
            return None

    def close(self):
        """Close database connection (if needed for cleanup)"""
        pass  # Using context managers, so no explicit close needed