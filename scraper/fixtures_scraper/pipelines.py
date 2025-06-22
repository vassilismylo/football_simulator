import sys
import os
from datetime import datetime, timedelta
import re

# Add the parent directory to Python path to import our database manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager


class FixturesPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.fixtures_added = 0
        self.teams_added = 0

    def open_spider(self, spider):
        spider.logger.info("Starting fixtures pipeline...")

    def close_spider(self, spider):
        spider.logger.info(f"Pipeline completed: {self.fixtures_added} fixtures, {self.teams_added} teams added")

    def process_item(self, item, spider):
        """Process scraped fixture items"""

        if item.__class__.__name__ == 'FixtureItem':
            return self.process_fixture_item(item, spider)
        elif item.__class__.__name__ == 'TeamStatsItem':
            return self.process_team_stats_item(item, spider)

        return item

    def process_fixture_item(self, item, spider):
        """Process a fixture item and add to database"""

        try:
            # Clean and validate team names
            home_team = self.clean_team_name(item.get('home_team', ''))
            away_team = self.clean_team_name(item.get('away_team', ''))

            if not home_team or not away_team:
                spider.logger.warning(f"Invalid team names: '{home_team}' vs '{away_team}'")
                return item

            # Ensure teams exist in database
            self.ensure_team_exists(home_team)
            self.ensure_team_exists(away_team)

            # Parse gameweek
            gameweek = self.parse_gameweek(item.get('gameweek'), item.get('match_date'))

            # Parse match date
            match_date = self.parse_match_date(item.get('match_date'), item.get('match_time'))

            # Add fixture to database
            self.db.add_fixture(
                gameweek=gameweek,
                home_team=home_team,
                away_team=away_team,
                date=match_date
            )

            # If match is completed, update the result
            if item.get('is_played') and item.get('home_goals') is not None:
                # Find the fixture we just added and update it
                fixtures = self.db.get_gameweek_fixtures(gameweek)
                for fixture in fixtures:
                    if (fixture['home_team'] == home_team and
                            fixture['away_team'] == away_team and
                            not fixture['is_played']):
                        self.db.update_fixture_result(
                            fixture['id'],
                            int(item.get('home_goals', 0)),
                            int(item.get('away_goals', 0))
                        )
                        break

            self.fixtures_added += 1
            spider.logger.info(f"Added fixture: {home_team} vs {away_team} (GW{gameweek})")

        except Exception as e:
            spider.logger.error(f"Error processing fixture: {e}")
            spider.logger.error(f"Item data: {dict(item)}")

        return item

    def process_team_stats_item(self, item, spider):
        """Process team statistics and update ratings"""

        try:
            team_name = self.clean_team_name(item.get('team_name', ''))

            if not team_name:
                return item

            # Calculate ratings based on stats
            attack_rating = self.calculate_attack_rating(item)
            defense_rating = self.calculate_defense_rating(item)
            overall_rating = (attack_rating + defense_rating) // 2

            # Update team in database
            self.db.add_team(team_name, attack_rating, defense_rating, overall_rating)

            spider.logger.info(f"Updated team stats: {team_name} (A:{attack_rating}, D:{defense_rating})")

        except Exception as e:
            spider.logger.error(f"Error processing team stats: {e}")

        return item

    def clean_team_name(self, team_name):
        """Clean and standardize team names"""
        if not team_name:
            return ""

        # Remove extra whitespace
        team_name = team_name.strip()

        # Common name mappings
        name_mappings = {
            'Man City': 'Manchester City',
            'Man Utd': 'Manchester United',
            'Man United': 'Manchester United',
            'Spurs': 'Tottenham',
            'Brighton & Hove Albion': 'Brighton',
            'Brighton and Hove Albion': 'Brighton',
            'West Ham United': 'West Ham',
            'Newcastle': 'Newcastle United',
            'Wolves': 'Wolves',
            'Wolverhampton': 'Wolves',
            'Nottm Forest': 'Nottingham Forest',
            'Nott\'m Forest': 'Nottingham Forest',
            'Sheffield Utd': 'Sheffield United',
            'Sheffield United': 'Sheffield United',
        }

        return name_mappings.get(team_name, team_name)

    def parse_gameweek(self, gameweek_str, match_date_str):
        """Parse gameweek from string or estimate from date"""

        # Try to extract gameweek number
        if gameweek_str:
            match = re.search(r'(\d+)', str(gameweek_str))
            if match:
                return int(match.group(1))

        # Estimate gameweek from date (Premier League starts mid-August)
        if match_date_str:
            try:
                # Parse various date formats
                date_obj = self.parse_date_string(match_date_str)
                if date_obj:
                    # Premier League 2024-25 started around August 17, 2024
                    season_start = datetime(2024, 8, 17)
                    days_since_start = (date_obj - season_start).days
                    estimated_gameweek = max(1, (days_since_start // 7) + 1)
                    return min(estimated_gameweek, 38)  # Cap at 38 gameweeks
            except:
                pass

        return 1  # Default to gameweek 1

    def parse_match_date(self, date_str, time_str):
        """Parse match date and time into a standardized format"""

        if not date_str:
            return None

        try:
            # Try to parse the date
            date_obj = self.parse_date_string(date_str)

            if date_obj and time_str:
                # Try to add time
                time_match = re.search(r'(\d{1,2}):(\d{2})', str(time_str))
                if time_match:
                    hour, minute = int(time_match.group(1)), int(time_match.group(2))
                    date_obj = date_obj.replace(hour=hour, minute=minute)

            return date_obj.strftime('%Y-%m-%d %H:%M') if date_obj else None

        except Exception:
            return date_str  # Return original if parsing fails

    def parse_date_string(self, date_str):
        """Parse various date string formats"""

        date_formats = [
            '%d %B %Y',  # 17 August 2024
            '%d %b %Y',  # 17 Aug 2024
            '%Y-%m-%d',  # 2024-08-17
            '%d/%m/%Y',  # 17/08/2024
            '%m/%d/%Y',  # 08/17/2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def ensure_team_exists(self, team_name):
        """Ensure team exists in database, add if not"""

        existing_stats = self.db.get_team_stats(team_name)
        if not existing_stats:
            # Add team with default ratings
            self.db.add_team(team_name, 50, 50, 50)
            self.teams_added += 1

    def calculate_attack_rating(self, item):
        """Calculate attack rating from team stats"""

        try:
            goals_for = int(item.get('goals_for', 0))
            games_played = int(item.get('games_played', 1))

            if games_played == 0:
                return 50

            goals_per_game = goals_for / games_played

            # Scale to 20-90 range based on Premier League averages
            # Average is about 1.4 goals per game
            rating = 30 + (goals_per_game / 2.5) * 60
            return max(20, min(90, int(rating)))

        except (ValueError, TypeError):
            return 50  # Default rating

    def calculate_defense_rating(self, item):
        """Calculate defense rating from team stats"""

        try:
            goals_against = int(item.get('goals_against', 0))
            games_played = int(item.get('games_played', 1))

            if games_played == 0:
                return 50

            goals_conceded_per_game = goals_against / games_played

            # Scale to 20-90 range (fewer goals conceded = higher rating)
            # Average is about 1.4 goals conceded per game
            rating = 90 - (goals_conceded_per_game / 2.5) * 60
            return max(20, min(90, int(rating)))

        except (ValueError, TypeError):
            return 50  # Default rating