import random
import numpy as np
from typing import Tuple, Dict, Optional


class MatchSimulator:
    def __init__(self):
        # You can adjust these factors to fine-tune simulation
        self.home_advantage = 5  # Rating boost for home team
        self.randomness_factor = 15  # How much random variation
        self.max_goals = 7  # Cap on goals per team

    def simulate_basic(self, home_rating: int, away_rating: int) -> Tuple[int, int]:
        """
        Level 1: Super Simple simulation
        Just compare ratings with some randomness
        """
        # Add home advantage and randomness
        home_strength = home_rating + self.home_advantage + random.randint(-self.randomness_factor,
                                                                           self.randomness_factor)
        away_strength = away_rating + random.randint(-self.randomness_factor, self.randomness_factor)

        strength_diff = home_strength - away_strength

        # Determine result based on strength difference
        if strength_diff > 20:  # Home team much stronger
            return random.choice([(3, 0), (2, 0), (3, 1), (4, 1), (2, 1)])
        elif strength_diff > 10:  # Home team stronger
            return random.choice([(2, 1), (1, 0), (3, 2), (2, 0)])
        elif strength_diff < -20:  # Away team much stronger
            return random.choice([(0, 3), (0, 2), (1, 3), (1, 4), (1, 2)])
        elif strength_diff < -10:  # Away team stronger
            return random.choice([(1, 2), (0, 1), (2, 3), (0, 2)])
        else:  # Evenly matched
            return random.choice([(1, 1), (0, 0), (2, 2), (1, 0), (0, 1), (2, 1), (1, 2)])

    def simulate_rating_based(self, home_attack: int, home_defense: int,
                              away_attack: int, away_defense: int) -> Tuple[int, int]:
        """
        Level 2: Rating-based goals
        Uses separate attack/defense ratings
        """
        # Calculate goal expectancy based on attack vs defense
        home_goal_potential = max(0, (home_attack - away_defense + 50) / 100)
        away_goal_potential = max(0, (away_attack - home_defense + 40) / 100)  # Less home advantage

        # Add some randomness
        home_goal_potential *= random.uniform(0.7, 1.4)
        away_goal_potential *= random.uniform(0.7, 1.4)

        # Convert to actual goals (with some probability)
        home_goals = 0
        away_goals = 0

        # Simulate goal scoring chances
        for _ in range(10):  # 10 chances per team
            if random.random() < home_goal_potential:
                home_goals += 1
            if random.random() < away_goal_potential:
                away_goals += 1

        return min(home_goals, self.max_goals), min(away_goals, self.max_goals)

    def simulate_with_stats(self, home_team_stats: Dict, away_team_stats: Dict,
                            gameweek: int = 1) -> Tuple[int, int]:
        """
        Level 3: Multiple factors simulation
        Uses team stats and various factors
        """
        # Base strength from overall rating
        home_strength = home_team_stats.get('overall_rating', 50)
        away_strength = away_team_stats.get('overall_rating', 50)

        # Home advantage
        home_strength += self.home_advantage

        # Form factor (if available)
        home_form = home_team_stats.get('recent_form', 0)
        away_form = away_team_stats.get('recent_form', 0)
        home_strength += home_form * 2
        away_strength += away_form * 2

        # Fatigue factor (later in season)
        if gameweek > 30:
            fatigue = random.randint(2, 5)
            home_strength -= fatigue
            away_strength -= fatigue

        # Motivation factor (random events, derby matches, etc.)
        motivation = random.randint(-8, 8)
        home_strength += motivation
        away_strength -= motivation // 2

        # Convert strength difference to goals
        strength_diff = home_strength - away_strength
        base_goals = 1.3  # Average goals per team

        # Expected goals calculation
        home_expected = base_goals + max(0, strength_diff / 25)
        away_expected = base_goals + max(0, -strength_diff / 25)

        # Add randomness and generate goals
        home_goals = max(0, int(np.random.normal(home_expected, 0.9)))
        away_goals = max(0, int(np.random.normal(away_expected, 0.9)))

        return min(home_goals, self.max_goals), min(away_goals, self.max_goals)

    def simulate_realistic_stats(self, home_stats: Dict, away_stats: Dict) -> Tuple[int, int]:
        """
        Level 4: Realistic simulation using actual team statistics
        Requires real stats like goals_per_game, goals_conceded_per_game
        """
        # Get scoring rates (goals per game)
        home_attack_rate = home_stats.get('goals_per_game_home', 1.2)
        home_defense_rate = home_stats.get('goals_conceded_per_game_home', 1.2)

        away_attack_rate = away_stats.get('goals_per_game_away', 1.0)
        away_defense_rate = away_stats.get('goals_conceded_per_game_away', 1.4)

        # Calculate expected goals for this matchup
        # Home team's expected goals = their attack rate vs away team's defense
        home_expected = (home_attack_rate + away_defense_rate) / 2
        away_expected = (away_attack_rate + home_defense_rate) / 2

        # Apply form multipliers if available
        home_form_mult = 1 + (home_stats.get('form_goals_last_5', 5) - 5) / 20
        away_form_mult = 1 + (away_stats.get('form_goals_last_5', 5) - 5) / 20

        home_expected *= home_form_mult
        away_expected *= away_form_mult

        # Generate goals using Poisson distribution (more realistic)
        home_goals = max(0, int(np.random.poisson(home_expected)))
        away_goals = max(0, int(np.random.poisson(away_expected)))

        return min(home_goals, self.max_goals), min(away_goals, self.max_goals)

    def simulate_match(self, home_team: str, away_team: str,
                       home_stats: Dict, away_stats: Dict,
                       simulation_level: str = "basic", gameweek: int = 1) -> Dict:
        """
        Main simulation method - chooses simulation level and returns detailed result

        Args:
            home_team: Name of home team
            away_team: Name of away team
            home_stats: Home team statistics dict
            away_stats: Away team statistics dict
            simulation_level: "basic", "rating", "stats", or "realistic"
            gameweek: Current gameweek number

        Returns:
            Dict with match result and details
        """

        if simulation_level == "basic":
            home_goals, away_goals = self.simulate_basic(
                home_stats.get('overall_rating', 50),
                away_stats.get('overall_rating', 50)
            )

        elif simulation_level == "rating":
            home_goals, away_goals = self.simulate_rating_based(
                home_stats.get('attack_rating', 50),
                home_stats.get('defense_rating', 50),
                away_stats.get('attack_rating', 50),
                away_stats.get('defense_rating', 50)
            )

        elif simulation_level == "stats":
            home_goals, away_goals = self.simulate_with_stats(
                home_stats, away_stats, gameweek
            )

        elif simulation_level == "realistic":
            home_goals, away_goals = self.simulate_realistic_stats(
                home_stats, away_stats
            )

        else:
            # Default to basic
            home_goals, away_goals = self.simulate_basic(
                home_stats.get('overall_rating', 50),
                away_stats.get('overall_rating', 50)
            )

        # Determine result
        if home_goals > away_goals:
            result = "H"  # Home win
        elif away_goals > home_goals:
            result = "A"  # Away win
        else:
            result = "D"  # Draw

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'result': result,
            'scoreline': f"{home_goals}-{away_goals}",
            'simulation_level': simulation_level
        }

    def get_result_probability(self, home_stats: Dict, away_stats: Dict) -> Dict[str, float]:
        """
        Calculate win/draw/loss probabilities for a match
        Useful for showing odds before simulation
        """
        home_rating = home_stats.get('overall_rating', 50) + self.home_advantage
        away_rating = away_stats.get('overall_rating', 50)

        rating_diff = home_rating - away_rating

        # Convert rating difference to probabilities
        if rating_diff > 20:
            return {'home_win': 0.70, 'draw': 0.20, 'away_win': 0.10}
        elif rating_diff > 10:
            return {'home_win': 0.55, 'draw': 0.25, 'away_win': 0.20}
        elif rating_diff > 0:
            return {'home_win': 0.45, 'draw': 0.30, 'away_win': 0.25}
        elif rating_diff > -10:
            return {'home_win': 0.35, 'draw': 0.30, 'away_win': 0.35}
        elif rating_diff > -20:
            return {'home_win': 0.25, 'draw': 0.25, 'away_win': 0.50}
        else:
            return {'home_win': 0.15, 'draw': 0.20, 'away_win': 0.65}


# Convenience function for quick simulation
def simulate_quick_match(home_team: str, away_team: str,
                         home_rating: int = 50, away_rating: int = 50) -> Tuple[int, int]:
    """Quick simulation for testing"""
    simulator = MatchSimulator()
    home_stats = {'overall_rating': home_rating}
    away_stats = {'overall_rating': away_rating}

    result = simulator.simulate_match(home_team, away_team, home_stats, away_stats, "basic")
    return result['home_goals'], result['away_goals']


# Example usage and testing
if __name__ == "__main__":
    # Test the simulator
    simulator = MatchSimulator()

    # Test basic simulation
    home_stats = {'overall_rating': 75}  # Strong team
    away_stats = {'overall_rating': 45}  # Weak team

    print("Testing Match Simulator:")
    print("-" * 30)

    for level in ["basic", "rating", "stats"]:
        result = simulator.simulate_match("Manchester City", "Sheffield United",
                                          home_stats, away_stats, level)
        print(f"{level.title()} Simulation: {result['home_team']} {result['scoreline']} {result['away_team']}")

    # Test probabilities
    probs = simulator.get_result_probability(home_stats, away_stats)
    print(
        f"\nMatch Probabilities: Home {probs['home_win']:.1%}, Draw {probs['draw']:.1%}, Away {probs['away_win']:.1%}")