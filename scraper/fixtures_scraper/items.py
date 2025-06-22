import scrapy


class FixtureItem(scrapy.Item):
    # Match details
    home_team = scrapy.Field()
    away_team = scrapy.Field()
    match_date = scrapy.Field()
    match_time = scrapy.Field()
    gameweek = scrapy.Field()

    # Optional fields for completed matches
    home_goals = scrapy.Field()
    away_goals = scrapy.Field()
    is_played = scrapy.Field()

    # Additional metadata
    competition = scrapy.Field()
    season = scrapy.Field()
    venue = scrapy.Field()

    # Raw data for debugging
    raw_text = scrapy.Field()


class TeamStatsItem(scrapy.Item):
    # Team information
    team_name = scrapy.Field()

    # Basic stats
    games_played = scrapy.Field()
    wins = scrapy.Field()
    draws = scrapy.Field()
    losses = scrapy.Field()
    goals_for = scrapy.Field()
    goals_against = scrapy.Field()
    goal_difference = scrapy.Field()
    points = scrapy.Field()

    # Home/Away splits
    home_wins = scrapy.Field()
    home_draws = scrapy.Field()
    home_losses = scrapy.Field()
    home_goals_for = scrapy.Field()
    home_goals_against = scrapy.Field()

    away_wins = scrapy.Field()
    away_draws = scrapy.Field()
    away_losses = scrapy.Field()
    away_goals_for = scrapy.Field()
    away_goals_against = scrapy.Field()

    # Form data
    recent_form = scrapy.Field()  # Last 5 games

    # Calculated ratings
    attack_rating = scrapy.Field()
    defense_rating = scrapy.Field()
    overall_rating = scrapy.Field()