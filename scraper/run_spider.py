import scrapy
import re
from datetime import datetime, timedelta
from fixtures_scraper.items import FixtureItem, TeamStatsItem


class FixturesSpider(scrapy.Spider):
    name = 'fixtures'
    allowed_domains = ['bbc.co.uk', 'bbc.com']

    def __init__(self, season='2024-25', *args, **kwargs):
        super(FixturesSpider, self).__init__(*args, **kwargs)
        self.season = season

        # BBC Sport Premier League URLs
        self.start_urls = [
            'https://www.bbc.co.uk/sport/football/premier-league/fixtures',
            'https://www.bbc.co.uk/sport/football/premier-league/results',
            'https://www.bbc.co.uk/sport/football/premier-league/table'
        ]

    def parse(self, response):
        """Main parsing method - routes to specific parsers based on URL"""

        url = response.url

        if 'fixtures' in url:
            yield from self.parse_fixtures_page(response)
        elif 'results' in url:
            yield from self.parse_results_page(response)
        elif 'table' in url:
            yield from self.parse_table_page(response)

    def parse_fixtures_page(self, response):
        """Parse upcoming fixtures"""

        self.logger.info("Parsing fixtures page...")

        # BBC Sport structure for fixtures
        fixture_sections = response.css('div[data-testid="fixture-wrapper"], .fixture-wrapper, .sp-c-fixture')

        if not fixture_sections:
            # Try alternative selectors
            fixture_sections = response.css('.gs-c-fixture, article[data-sport="football"]')

        current_gameweek = 1

        for section in fixture_sections:
            # Try to extract gameweek info
            gameweek_text = section.css('.sp-c-fixture__header ::text, .fixture-header ::text').get()
            if gameweek_text and 'matchweek' in gameweek_text.lower():
                gw_match = re.search(r'(\d+)', gameweek_text)
                if gw_match:
                    current_gameweek = int(gw_match.group(1))

            # Extract individual matches
            matches = section.css('.sp-c-fixture, .fixture, [data-testid="fixture"]')

            for match in matches:
                fixture_item = self.extract_fixture_data(match, current_gameweek, is_future=True)
                if fixture_item:
                    yield fixture_item

        # If no fixtures found with standard selectors, try generic approach
        if not fixture_sections:
            yield from self.parse_generic_fixtures(response, current_gameweek)

    def parse_results_page(self, response):
        """Parse completed matches"""

        self.logger.info("Parsing results page...")

        # Look for completed matches
        result_sections = response.css(
            'div[data-testid="results-wrapper"], .results-wrapper, .sp-c-fixture--has-result')

        current_gameweek = 1

        for section in result_sections:
            # Extract gameweek
            gameweek_text = section.css('.sp-c-fixture__header ::text, .results-header ::text').get()
            if gameweek_text:
                gw_match = re.search(r'(\d+)', gameweek_text)
                if gw_match:
                    current_gameweek = int(gw_match.group(1))

            # Extract matches with results
            matches = section.css('.sp-c-fixture, .result, [data-testid="result"]')

            for match in matches:
                fixture_item = self.extract_fixture_data(match, current_gameweek, is_future=False)
                if fixture_item:
                    yield fixture_item

    def parse_table_page(self, response):
        """Parse league table for team stats"""

        self.logger.info("Parsing league table...")

        # BBC Sport table structure
        table_rows = response.css('table.sp-c-table tbody tr, .league-table tbody tr')

        for row in table_rows:
            team_stats = self.extract_team_stats(row)
            if team_stats:
                yield team_stats

    def extract_fixture_data(self, match_element, gameweek, is_future=True):
        """Extract fixture data from a match element"""

        try:
            # Try multiple selectors for team names
            home_team = self.extract_team_name(match_element, 'home')
            away_team = self.extract_team_name(match_element, 'away')

            if not home_team or not away_team:
                return None

            # Extract date and time
            date_text = match_element.css('.sp-c-fixture__date ::text, .fixture-date ::text, time ::text').get()
            time_text = match_element.css('.sp-c-fixture__time ::text, .fixture-time ::text').get()

            # Create fixture item
            fixture = FixtureItem()
            fixture['home_team'] = home_team.strip()
            fixture['away_team'] = away_team.strip()
            fixture['gameweek'] = gameweek
            fixture['match_date'] = date_text.strip() if date_text else None
            fixture['match_time'] = time_text.strip() if time_text else None
            fixture['competition'] = 'Premier League'
            fixture['season'] = self.season

            # If it's a result, extract scores
            if not is_future:
                home_score, away_score = self.extract_score(match_element)
                if home_score is not None and away_score is not None:
                    fixture['home_goals'] = home_score
                    fixture['away_goals'] = away_score
                    fixture['is_played'] = True
                else:
                    fixture['is_played'] = False
            else:
                fixture['is_played'] = False

            return fixture

        except Exception as e:
            self.logger.warning(f"Error extracting fixture data: {e}")
            return None

    def extract_team_name(self, match_element, team_type='home'):
        """Extract team name with multiple fallback selectors"""

        # Team name selectors (BBC Sport specific)
        selectors = [
            f'.sp-c-fixture__{team_type}-team .sp-c-fixture__team-name ::text',
            f'.sp-c-fixture__{team_type} .team-name ::text',
            f'.{team_type}-team .team-name ::text',
            f'.{team_type}-team ::text',
            '.sp-c-fixture__team-name ::text',
            '.team-name ::text',
            '.sp-c-fixture__team ::text'
        ]

        for selector in selectors:
            team_name = match_element.css(selector).get()
            if team_name and team_name.strip():
                return team_name.strip()

        # Fallback: try to extract from any text content
        all_text = match_element.css('::text').getall()
        team_names = []

        for text in all_text:
            text = text.strip()
            if text and len(text) > 2 and text not in ['vs', 'v', '-', ':', 'FT']:
                # Check if it looks like a team name
                if any(keyword in text.lower() for keyword in
                       ['united', 'city', 'town', 'villa', 'palace', 'forest', 'ham', 'arsenal', 'chelsea', 'liverpool',
                        'tottenham', 'brighton', 'wolves', 'everton', 'brentford', 'fulham', 'luton', 'burnley',
                        'sheffield', 'bournemouth', 'newcastle', 'crystal']):
                    team_names.append(text)

        if len(team_names) >= 2:
            return team_names[0] if team_type == 'home' else team_names[1]

        return None

    def extract_score(self, match_element):
        """Extract match score"""

        # Score selectors
        score_selectors = [
            '.sp-c-fixture__score ::text',
            '.fixture-score ::text',
            '.score ::text',
            '[data-testid="score"] ::text'
        ]

        for selector in score_selectors:
            score_text = match_element.css(selector).get()
            if score_text:
                # Parse score like "2-1" or "2 - 1"
                score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', score_text)
                if score_match:
                    return int(score_match.group(1)), int(score_match.group(2))

        # Alternative: look for separate home and away score elements
        home_score = match_element.css('.home-score ::text, .sp-c-fixture__home-score ::text').get()
        away_score = match_element.css('.away-score ::text, .sp-c-fixture__away-score ::text').get()

        if home_score and away_score:
            try:
                return int(home_score.strip()), int(away_score.strip())
            except ValueError:
                pass

        return None, None

    def extract_team_stats(self, table_row):
        """Extract team statistics from league table row"""

        try:
            # Get all cells
            cells = table_row.css('td ::text, th ::text').getall()
            cells = [cell.strip() for cell in cells if cell.strip()]

            if len(cells) < 10:  # Not enough data
                return None

            # Standard Premier League table format:
            # Position, Team, Played, Won, Drawn, Lost, For, Against, GD, Points

            team_name = cells[1] if len(cells) > 1 else None

            if not team_name:
                return None

            stats = TeamStatsItem()
            stats['team_name'] = team_name

            try:
                stats['games_played'] = int(cells[2]) if len(cells) > 2 else 0
                stats['wins'] = int(cells[3]) if len(cells) > 3 else 0
                stats['draws'] = int(cells[4]) if len(cells) > 4 else 0
                stats['losses'] = int(cells[5]) if len(cells) > 5 else 0
                stats['goals_for'] = int(cells[6]) if len(cells) > 6 else 0
                stats['goals_against'] = int(cells[7]) if len(cells) > 7 else 0
                stats['goal_difference'] = int(cells[8]) if len(cells) > 8 else 0
                stats['points'] = int(cells[9]) if len(cells) > 9 else 0
            except ValueError:
                # If parsing fails, set defaults
                stats['games_played'] = 0
                stats['wins'] = 0
                stats['draws'] = 0
                stats['losses'] = 0
                stats['goals_for'] = 0
                stats['goals_against'] = 0
                stats['goal_difference'] = 0
                stats['points'] = 0

            return stats

        except Exception as e:
            self.logger.warning(f"Error extracting team stats: {e}")
            return None

    def parse_generic_fixtures(self, response, current_gameweek):
        """Generic parser as fallback when specific selectors fail"""

        self.logger.info("Using generic fixture parser...")

        # Look for any elements containing team names
        text_elements = response.css('*::text').getall()

        # Premier League team names to look for
        team_names = [
            'Arsenal', 'Manchester City', 'Manchester United', 'Liverpool', 'Chelsea',
            'Tottenham', 'Newcastle United', 'Brighton', 'Aston Villa', 'West Ham',
            'Crystal Palace', 'Fulham', 'Wolves', 'Everton', 'Brentford',
            'Nottingham Forest', 'Luton Town', 'Burnley', 'Sheffield United', 'Bournemouth'
        ]

        potential_matches = []
        current_text = ""

        for text in text_elements:
            text = text.strip()
            if text:
                current_text += " " + text

                # Check if we have a potential match
                teams_found = [team for team in team_names if team in current_text]

                if len(teams_found) >= 2:
                    # Potential fixture found
                    fixture = FixtureItem()
                    fixture['home_team'] = teams_found[0]
                    fixture['away_team'] = teams_found[1]
                    fixture['gameweek'] = current_gameweek
                    fixture['is_played'] = False
                    fixture['competition'] = 'Premier League'
                    fixture['season'] = self.season

                    potential_matches.append(fixture)
                    current_text = ""  # Reset for next match

        for match in potential_matches[:10]:  # Limit to prevent spam
            yield match