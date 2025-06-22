# Football Simulator Project - Complete Documentation

## 🎯 Project Overview

A Python-based football simulation game where the user manually controls one team (Sheffield United) and simulates all other Premier League matches. Built with Streamlit for the frontend, SQLite for data storage, and Scrapy for data collection.

## 🎮 Core Concept

- **User Team**: Sheffield United (configurable)
- **User Input**: Manual entry of your team's match results
- **Auto Simulation**: All other Premier League matches simulated automatically
- **Season Progression**: Advance through gameweeks, track league position
- **Real Data**: Scrape fixtures and team stats from websites

## 🏗️ Current Architecture

### Project Structure
```
football_simulator/
├── data/
│   └── football.db                    # SQLite database
├── database/
│   └── db_manager.py                  # Database management
├── scraper/
│   ├── scrapy.cfg                     # Scrapy configuration
│   ├── fixtures_scraper/
│   │   ├── __init__.py
│   │   ├── settings.py                # Spider settings
│   │   ├── items.py                   # Data structures
│   │   ├── pipelines.py               # Database integration
│   │   └── spiders/
│   │       ├── __init__.py
│   │       ├── fixtures_spider.py     # BBC Sport spider
│   │       └── simple_fixtures.py     # Fallback spider
│   ├── run_spider.py                  # Spider runner
│   └── setup_football_sim.py          # Setup script
├── simulation/
│   └── match_sim.py                   # Match simulation engine
└── streamlit_app.py                   # Main application
```

### Database Schema
```sql
-- Teams table
teams: id, name, attack_rating, defense_rating, overall_rating, 
       goals_scored, goals_conceded, games_played, etc.

-- Fixtures table  
fixtures: id, gameweek, home_team, away_team, home_goals, away_goals, 
          is_played, is_user_team, date

-- League table
league_table: team_name, played, won, drawn, lost, goals_for, 
              goals_against, goal_difference, points, form

-- Game state
game_state: current_gameweek, season_year, user_team
```

## ✅ Features Currently Built

### 1. Database Management (`database/db_manager.py`)
- SQLite database with complete Premier League structure
- Team management (add teams, ratings, stats)
- Fixture management (add/update matches)
- League table calculations
- Gameweek progression
- User team configuration

### 2. Match Simulation (`simulation/match_sim.py`)
- **4 Simulation Levels**:
  - `basic`: Simple rating comparison with randomness
  - `rating`: Attack vs Defense calculations
  - `stats`: Multiple factors (form, fatigue, motivation)
  - `realistic`: Poisson distribution with real stats
- Home advantage factor
- Configurable randomness
- Match result probabilities

### 3. Web Scraping (`scraper/`)
- **Scrapy Project**: Complete setup for data extraction
- **BBC Sport Spider**: Scrapes fixtures, results, and league table
- **Fallback Spider**: Sample fixtures if scraping fails
- **Smart Pipeline**: Cleans team names, calculates gameweeks
- **Database Integration**: Automatically populates database

### 4. Streamlit Application (`streamlit_app.py`)
- **5 Main Pages**:
  - **Home**: Overview, current gameweek, quick stats
  - **Fixtures**: Input your results, simulate other matches
  - **League Table**: Live standings with position highlighting
  - **Settings**: Change team preferences
  - **Admin**: Add teams, fixtures, database management

### 5. User Interface Features
- Manual result input for user team
- One-click simulation of remaining matches
- Gameweek advancement system
- League position tracking
- Real-time table updates
- Premier League team setup (20 teams with realistic ratings)

## 🔧 Technical Implementation Details

### Match Simulation Logic
```python
# Basic simulation example
def simulate_basic(home_rating, away_rating):
    home_strength = home_rating + 5 + random.randint(-15, 15)  # home advantage
    away_strength = away_rating + random.randint(-15, 15)
    
    if home_strength > away_strength + 20:
        return random.choice([(3,0), (2,0), (3,1)])  # home win
    elif away_strength > home_strength + 20:
        return random.choice([(0,3), (0,2), (1,3)])  # away win
    else:
        return random.choice([(1,1), (0,0), (2,1)])  # close match
```

### Database Operations
```python
# Add fixture
db.add_fixture(gameweek=1, home_team="Sheffield United", away_team="Arsenal")

# Update result
db.update_fixture_result(fixture_id=1, home_goals=2, away_goals=1)

# Get league table
table = db.get_league_table()  # Returns sorted by points
```

### Web Scraping
```python
# Scrapy spider extracts fixture data
def parse_fixtures(self, response):
    for fixture_element in response.css('.fixture'):
        home_team = self.extract_team_name(fixture_element, 'home')
        away_team = self.extract_team_name(fixture_element, 'away')
        yield FixtureItem(home_team=home_team, away_team=away_team)
```

## 🚀 How to Use (Current State)

### Setup
1. **Install dependencies**: `pip install streamlit pandas numpy scrapy`
2. **Initialize database**: Run `python setup_football_sim.py`
3. **Add teams**: Use Admin panel → "Setup Premier League Teams"
4. **Add fixtures**: Either scrape or manually add in Admin panel

### Playing
1. **Start app**: `streamlit run streamlit_app.py`
2. **Go to Fixtures page**
3. **Input your team's result** (Sheffield United by default)
4. **Simulate other matches** with one click
5. **Advance gameweek** when all matches complete
6. **Track your progress** in League Table

### Scraping Data
```bash
cd scraper
python run_spider.py  # Interactive setup
# OR
scrapy crawl fixtures  # Direct command
```

## 🎯 Future Features Planned

### 1. Enhanced Data (Next Priority)
- **Real Schedule**: User will provide correct Premier League fixtures
- **Custom Teams**: User-specified team names and data
- **Accurate Ratings**: Based on real team performance

### 2. Player Management System
```
Players Table:
- id, name, number, position, team_id
- rating, age, nationality (optional)

Features:
- Add/edit players for user team
- Basic player stats
- Simple squad management
```

### 3. First 11 Selection System
```
Lineup Table:
- formation (4-4-2, 4-3-3, etc.)
- starting_11 (11 player IDs)
- substitutes (bench players)

Features:
- Drag-and-drop team selection
- Formation templates
- Basic validation (right number of players, positions)
```

### 4. Simple Tactics Page
```
Tactics Configuration:
- Formation selection (dropdown)
- Playing style (attacking/defensive slider)
- Focus areas (wings/center, high/low pressing)
- Basic mentality settings

Impact on Simulation:
- Slight rating modifiers based on tactics
- Formation vs formation bonuses/penalties
- Style matchup effects
```

### 5. Enhanced Simulation Features
- **Weather effects**: Rain = fewer goals
- **Injury system**: Random player unavailability
- **Momentum**: Winning/losing streaks affect performance
- **Derby matches**: Local rivalries get intensity bonus
- **European competitions**: Champions League/Europa League fixture congestion

## 🐛 Known Issues & Fixes

### 1. Scrapy Installation Issues
**Problem**: Module not found errors despite installation
**Solutions Tried**:
- Multiple reinstalls
- Different Python environments
- Direct executable calls

**Current Workaround**: Manual fixture addition via Admin panel

### 2. Navigation Issues
**Problem**: `st.switch_page()` looking for non-existent files
**Fix Applied**: Using `st.session_state` for navigation instead

### 3. Empty Database
**Problem**: No fixtures loaded by default
**Solution**: Setup script with sample fixtures, manual addition tools

## 📊 Team Ratings (Current)

```python
premier_league_teams = [
    ("Arsenal", 85, 80, 83),           # (name, attack, defense, overall)
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
    ("Sheffield United", 45, 50, 48),  # User team (lower rating for challenge)
    ("Bournemouth", 62, 58, 60)
]
```

## 🔄 Development Workflow

### Adding New Features
1. **Database Changes**: Update `db_manager.py` schema if needed
2. **Backend Logic**: Add to appropriate module (`simulation/`, `database/`)
3. **Frontend**: Add Streamlit pages/components
4. **Testing**: Manual testing via Streamlit interface
5. **Documentation**: Update this project knowledge

### Testing Process
1. **Unit Testing**: Individual component testing
2. **Integration Testing**: Database → Simulation → UI flow
3. **User Testing**: Complete season simulation
4. **Edge Cases**: Empty database, invalid inputs, etc.

## 💡 Design Decisions

### Why SQLite?
- **Simple setup**: No external database required
- **Portable**: Single file database
- **Sufficient performance**: For single-user application
- **Python integration**: Built-in sqlite3 module

### Why Streamlit?
- **Rapid development**: Quick UI creation
- **Python-native**: No separate frontend framework
- **Interactive widgets**: Perfect for forms and buttons
- **Easy deployment**: Simple sharing and hosting

### Why Scrapy?
- **Robust scraping**: Handles complex websites
- **Built-in features**: Retry logic, respectful crawling
- **Scalable**: Can handle large-scale data extraction
- **Pipeline system**: Clean data processing workflow

## 🎮 User Experience Goals

### Core User Journey
1. **Setup**: One-click team and fixture setup
2. **Play Match**: Simple form to input your result
3. **Simulate**: One button to simulate all other matches
4. **Review**: Clear league table showing your position
5. **Progress**: Easy advancement to next gameweek
6. **Track**: Season-long progression and statistics

### Ease of Use Priorities
1. **Minimal clicks**: Essential actions in 1-2 clicks
2. **Clear feedback**: Success/error messages for all actions
3. **Visual clarity**: Important information highlighted
4. **No technical knowledge**: Hide database/technical details
5. **Forgiving**: Handle invalid inputs gracefully

## 📈 Future Enhancement Ideas

### Advanced Features (Long-term)
- **Multiple seasons**: Progress through multiple years
- **Transfer market**: Buy/sell players
- **Financial management**: Budget constraints
- **Manager reputation**: Performance affects opportunities
- **Multiple leagues**: Championship, League One, etc.
- **International competitions**: World Cup, Euros
- **Multiplayer**: Multiple users controlling different teams

### Data Integration
- **Real APIs**: Official Premier League API
- **Live scores**: Real-time match updates
- **Historical data**: Past seasons for comparison
- **Player databases**: Detailed player statistics
- **Advanced metrics**: xG, xA, PPDA, etc.

## 🔧 Technical Debt & Improvements

### Code Quality
- **Error handling**: More comprehensive try/catch blocks
- **Input validation**: Robust form validation
- **Code documentation**: More inline comments and docstrings
- **Testing suite**: Automated unit and integration tests
- **Logging**: Better error logging and debugging info

### Performance
- **Database indexing**: Optimize query performance
- **Caching**: Cache frequently accessed data
- **Async operations**: Non-blocking database operations
- **Memory management**: Efficient data structures

### Maintainability
- **Configuration files**: Externalize settings
- **Modular design**: Further separate concerns
- **Version control**: Better git workflow
- **Deployment**: Containerization with Docker

## 📝 Development Notes

### Next Session TODO
1. **Real Fixture Data**: User to provide actual Premier League schedule
2. **Custom Team Names**: Update team list based on user preferences
3. **Player System**: Basic player management for user team
4. **Formation Selection**: Simple 11-player lineup system
5. **Basic Tactics**: Elementary tactical choices

### Long-term Roadmap
- **Q1**: Player management and tactics
- **Q2**: Enhanced simulation algorithms
- **Q3**: Multiple competitions
- **Q4**: Advanced features and polish

---

*This documentation will be updated as the project evolves. Each major feature addition should include updates to this knowledge base.*