from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import sqlite3
import pandas as pd
from functools import lru_cache
import time
import os
import requests

app = FastAPI(title="IPL Analytics API", description="IPL Cricket Analytics API")

DATABASE = "ipl.db"

# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST TIME LOGGER
# ═══════════════════════════════════════════════════════════════════════════

@app.middleware("http")
async def log_time(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.url.path} took {duration:.3f}s")
    return response


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════

def get_db():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# QUERY HELPER
# ═══════════════════════════════════════════════════════════════════════════

def query_db(conn, query, params=()):
    """Execute query and return results as list of dicts"""
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Query error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# CREATE DATABASE INDEXES
# ═══════════════════════════════════════════════════════════════════════════

def create_indexes():
    """Create database indexes for faster queries"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_id ON deliveries(match_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batter ON deliveries(batter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bowler ON deliveries(bowler)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_season ON matches(season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_winner ON matches(winner)")

        conn.commit()
        conn.close()
        print("✅ Database indexes created")
    except Exception as e:
        print(f"Index creation error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZE DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def init_database():
    """Initialize database from CSV if it doesn't exist"""
    if not os.path.exists(DATABASE):
        print("📂 Database not found. Creating from CSV...")
        try:
            matches = pd.read_csv("data/matches.csv")
            deliveries = pd.read_csv("data/deliveries.csv")
            
            conn = sqlite3.connect(DATABASE)
            matches.to_sql("matches", conn, if_exists="replace", index=False)
            deliveries.to_sql("deliveries", conn, if_exists="replace", index=False)
            conn.commit()
            conn.close()
            
            print("✅ Database created from CSV")
        except Exception as e:
            print(f"❌ Error creating database: {e}")
    else:
        print("✅ Database found")
    
    create_indexes()


# Initialize on startup
init_database()


# ═══════════════════════════════════════════════════════════════════════════
# PLAYER IMAGE & INFO ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/player_image")
def get_player_image(player_name: str):
    """Get player image URL from multiple sources"""
    try:
        # Try cricketdata API
        url = f"https://cricketdata.org/images/players/{player_name.lower().replace(' ', '_')}.jpg"
        response = requests.head(url, timeout=2)
        if response.status_code == 200:
            return {
                "player": player_name,
                "image_url": url,
                "source": "cricketdata.org",
                "status": "success"
            }
    except:
        pass
    
    try:
        # Try ESPN Cricinfo
        name_slug = player_name.lower().replace(' ', '-')
        url = f"https://a.espncdn.com/media/cricket/players/{name_slug}.jpg"
        response = requests.head(url, timeout=2)
        if response.status_code == 200:
            return {
                "player": player_name,
                "image_url": url,
                "source": "espncricinfo.com",
                "status": "success"
            }
    except:
        pass
    
    try:
        # Try Cricapi
        url = f"https://crex.cricketdata.org/media/players/{player_name.lower().replace(' ', '-')}.jpg"
        response = requests.head(url, timeout=2)
        if response.status_code == 200:
            return {
                "player": player_name,
                "image_url": url,
                "source": "crex.cricketdata.org",
                "status": "success"
            }
    except:
        pass
    
    # Return fallback if no image found
    return {
        "player": player_name,
        "image_url": None,
        "source": "none",
        "status": "not_found",
        "fallback": "emoji"
    }


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    """Health check endpoint"""
    db_exists = "Connected" if os.path.exists(DATABASE) else "Not Found"
    return {
        "status": "API Running",
        "database": db_exists,
        "version": "1.0.0",
        "player_image_endpoint": "/player_image?player_name=Virat%20Kohli"
    }


# ═══════════════════════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
def home():
    """Home endpoint"""
    return {
        "message": "IPL Analytics API Running",
        "docs": "/docs",
        "version": "1.0.0",
        "new_endpoint": "/player_image?player_name=PlayerName"
    }


# ═══════════════════════════════════════════════════════════════════════════
# MATCHES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/matches")
def get_matches(season: int = None, limit: int = 100, offset: int = 0, db: sqlite3.Connection = Depends(get_db)):
    """Get matches with optional season filter"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        if season:
            query = """
            SELECT * FROM matches
            WHERE season=?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
            """
            return query_db(db, query, (season, limit, offset))

        query = """
        SELECT * FROM matches
        ORDER BY date DESC
        LIMIT ? OFFSET ?
        """
        return query_db(db, query, (limit, offset))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# DELIVERIES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/deliveries")
def get_deliveries(match_id: int = None, limit: int = 1000, offset: int = 0, db: sqlite3.Connection = Depends(get_db)):
    """Get deliveries with optional match filter"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        if match_id:
            query = """
            SELECT * FROM deliveries
            WHERE match_id=?
            ORDER BY over, ball
            LIMIT ? OFFSET ?
            """
            return query_db(db, query, (match_id, limit, offset))

        query = """
        SELECT * FROM deliveries
        LIMIT ? OFFSET ?
        """
        return query_db(db, query, (limit, offset))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# TEAM WINS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/teams")
def get_teams(season: int = None, db: sqlite3.Connection = Depends(get_db)):
    """Get team wins statistics"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        if season:
            query = """
            SELECT winner AS team, COUNT(*) AS wins
            FROM matches
            WHERE season=?
            GROUP BY winner
            ORDER BY wins DESC
            """
            return query_db(db, query, (season,))

        query = """
        SELECT winner AS team, COUNT(*) AS wins
        FROM matches
        GROUP BY winner
        ORDER BY wins DESC
        """
        return query_db(db, query)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# TOP BATSMEN
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/top_batsmen")
def get_top_batsmen(season: int = None, limit: int = 10, db: sqlite3.Connection = Depends(get_db)):
    """Get top run scorers"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        if season:
            query = """
            SELECT d.batter, SUM(d.batsman_runs) AS runs, COUNT(d.ball) as balls,
                   SUM(CASE WHEN d.batsman_runs=4 THEN 1 ELSE 0 END) as fours,
                   SUM(CASE WHEN d.batsman_runs=6 THEN 1 ELSE 0 END) as sixes
            FROM deliveries d
            JOIN matches m ON d.match_id=m.id
            WHERE m.season=?
            GROUP BY d.batter
            ORDER BY runs DESC
            LIMIT ?
            """
            return query_db(db, query, (season, limit))

        query = """
        SELECT batter, SUM(batsman_runs) AS runs, COUNT(ball) as balls,
               SUM(CASE WHEN batsman_runs=4 THEN 1 ELSE 0 END) as fours,
               SUM(CASE WHEN batsman_runs=6 THEN 1 ELSE 0 END) as sixes
        FROM deliveries
        GROUP BY batter
        ORDER BY runs DESC
        LIMIT ?
        """
        return query_db(db, query, (limit,))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# TOP BOWLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/top_bowlers")
def get_top_bowlers(season: int = None, limit: int = 10, db: sqlite3.Connection = Depends(get_db)):
    """Get top wicket takers"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        if season:
            query = """
            SELECT d.bowler, COUNT(d.dismissal_kind) AS wickets,
                   SUM(d.total_runs) as runs_given
            FROM deliveries d
            JOIN matches m ON d.match_id=m.id
            WHERE m.season=? AND d.dismissal_kind IS NOT NULL
            GROUP BY d.bowler
            ORDER BY wickets DESC
            LIMIT ?
            """
            return query_db(db, query, (season, limit))

        query = """
        SELECT bowler, COUNT(dismissal_kind) AS wickets,
               SUM(total_runs) as runs_given
        FROM deliveries
        WHERE dismissal_kind IS NOT NULL
        GROUP BY bowler
        ORDER BY wickets DESC
        LIMIT ?
        """
        return query_db(db, query, (limit,))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# BEST STRIKE RATE
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/best_strike_rate")
def get_best_strike_rate(min_balls: int = 100, db: sqlite3.Connection = Depends(get_db)):
    """Get best strike rates"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT batter,
        SUM(batsman_runs) AS runs,
        COUNT(ball) AS balls,
        ROUND((SUM(batsman_runs)*100.0)/COUNT(ball),2) AS strike_rate
        FROM deliveries
        GROUP BY batter
        HAVING balls > ?
        ORDER BY strike_rate DESC
        LIMIT 10
        """
        return query_db(db, query, (min_balls,))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# VENUE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/venue_analysis")
def get_venue_analysis(db: sqlite3.Connection = Depends(get_db)):
    """Get venue statistics"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT venue, city, COUNT(*) AS matches
        FROM matches
        GROUP BY venue
        ORDER BY matches DESC
        """
        return query_db(db, query)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# TOSS ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/toss_analysis")
def get_toss_analysis(db: sqlite3.Connection = Depends(get_db)):
    """Get toss statistics"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT toss_decision, COUNT(*) AS count
        FROM matches
        GROUP BY toss_decision
        """
        return query_db(db, query)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# PLAYER PROFILE (ENHANCED WITH TEAM INFO)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/player_profile")
def get_player_profile(player: str, db: sqlite3.Connection = Depends(get_db)):
    """Get detailed player statistics"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT batter,
        SUM(batsman_runs) AS runs,
        COUNT(ball) AS balls,
        COUNT(CASE WHEN batsman_runs=4 THEN 1 END) AS fours,
        COUNT(CASE WHEN batsman_runs=6 THEN 1 END) AS sixes,
        ROUND((SUM(batsman_runs)*100.0)/COUNT(ball),2) AS strike_rate
        FROM deliveries
        WHERE batter=?
        GROUP BY batter
        """
        result = query_db(db, query, (player,))
        return result[0] if result else {"error": f"Player {player} not found"}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# PLAYER TEAMS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/player_teams")
def get_player_teams(player: str, db: sqlite3.Connection = Depends(get_db)):
    """Get teams a player has played for"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT DISTINCT d.batting_team as team
        FROM deliveries d
        WHERE d.batter=?
        ORDER BY team
        """
        teams = query_db(db, query, (player,))
        return {
            "player": player,
            "teams": [t["team"] for t in teams],
            "total_teams": len(teams)
        } if teams else {"error": f"No teams found for {player}"}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# PLAYER ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/player_achievements")
def get_player_achievements(player: str, db: sqlite3.Connection = Depends(get_db)):
    """Get player achievements"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        # Get man of the match count
        query_motm = """
        SELECT COUNT(*) as count
        FROM matches
        WHERE player_of_match = ?
        """
        motm = query_db(db, query_motm, (player,))
        motm_count = motm[0]["count"] if motm else 0
        
        # Get centuries (50+ runs in a match)
        query_centuries = """
        SELECT COUNT(*) as count
        FROM (
            SELECT SUM(batsman_runs) as runs
            FROM deliveries
            WHERE batter = ?
            GROUP BY match_id
            HAVING runs >= 50
        )
        """
        centuries = query_db(db, query_centuries, (player,))
        centuries_count = centuries[0]["count"] if centuries else 0
        
        return {
            "player": player,
            "man_of_match": motm_count,
            "half_centuries_plus": centuries_count,
            "total_achievements": motm_count + centuries_count
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# PLAYERS LIST
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/players")
def get_players(db: sqlite3.Connection = Depends(get_db)):
    """Get list of all players"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT DISTINCT batter
        FROM deliveries
        ORDER BY batter
        """
        return query_db(db, query)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# COMPARE PLAYERS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/compare_players")
def compare_players(player1: str, player2: str, db: sqlite3.Connection = Depends(get_db)):
    """Compare two players"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT batter,
        SUM(batsman_runs) AS runs,
        COUNT(ball) AS balls,
        SUM(CASE WHEN batsman_runs=4 THEN 1 ELSE 0 END) as fours,
        SUM(CASE WHEN batsman_runs=6 THEN 1 ELSE 0 END) as sixes,
        ROUND((SUM(batsman_runs)*100.0)/COUNT(ball),2) AS strike_rate
        FROM deliveries
        WHERE batter=? OR batter=?
        GROUP BY batter
        """
        return query_db(db, query, (player1, player2))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# MATCH ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/match_analysis")
def get_match_analysis(match_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get match analysis"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT batting_team,
        SUM(total_runs) AS runs
        FROM deliveries
        WHERE match_id=?
        GROUP BY batting_team
        """
        return query_db(db, query, (match_id,))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# MATCH MOMENTUM
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/match_momentum")
def get_match_momentum(match_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get match momentum (runs per over)"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT over,
        SUM(total_runs) AS runs
        FROM deliveries
        WHERE match_id=?
        GROUP BY over
        ORDER BY over
        """
        return query_db(db, query, (match_id,))
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# PLAYER FORM
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/player_form")
def get_player_form(player: str, db: sqlite3.Connection = Depends(get_db)):
    """Get player's last 5 matches form"""
    try:
        if db is None:
            return {"error": "Database connection failed"}
        
        query = """
        SELECT match_id,
        SUM(batsman_runs) AS runs
        FROM deliveries
        WHERE batter=?
        GROUP BY match_id
        ORDER BY match_id DESC
        LIMIT 5
        """
        data = query_db(db, query, (player,))

        if not data:
            return {"error": f"Player {player} not found"}

        runs = [d["runs"] for d in data]
        form_index = sum(runs) / len(runs) if runs else 0

        return {
            "player": player,
            "last_5_matches_runs": runs,
            "form_index": round(form_index, 2),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# WIN PREDICTOR (FIXED)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/win_predictor")
def win_predictor(runs_left: int, balls_left: int, wickets: int):
    """Predict match winning probability"""
    try:
        if balls_left == 0:
            return {"error": "Balls left cannot be 0"}

        if runs_left < 0 or balls_left < 0 or wickets < 0:
            return {"error": "Invalid input values"}

        # Calculate required run rate
        rrr = (runs_left * 6) / balls_left
        
        # FIXED FORMULA: Better scaling for realistic probabilities
        rrr_factor = (rrr / 10) * 50
        wickets_factor = wickets * 5
        base_probability = 50
        probability = base_probability - rrr_factor + wickets_factor
        probability = max(0, min(100, probability))

        return {
            "runs_left": runs_left,
            "balls_left": balls_left,
            "wickets": wickets,
            "required_run_rate": round(rrr, 2),
            "winning_probability": round(probability, 2),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting IPL Analytics API...")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("✅ NEW: Player Image endpoint at /player_image")
    print("✅ NEW: Player Teams endpoint at /player_teams")
    print("✅ NEW: Player Achievements endpoint at /player_achievements")
    print("✅ All fixes applied - Ready to use!")
    
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )