import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def fetch_scores():
    conn = sqlite3.connect('../data/golf_competition.db')
    query = 'SELECT * FROM scores'
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def plot_score_distribution():
    df = fetch_scores()
    plt.hist(df['total_score'], bins=20, edgecolor='black')
    plt.title('Score Distribution')
    plt.xlabel('Total Score')
    plt.ylabel('Frequency')
    plt.show()

def plot_score_trends(player_id):
    conn = sqlite3.connect('../data/golf_competition.db')
    query = 'SELECT * FROM scores WHERE player_id = ? ORDER BY competition_id'
    df = pd.read_sql_query(query, conn, params=(player_id,))
    conn.close()
    
    plt.plot(df['competition_id'], df['total_score'], marker='o')
    plt.title('Score Trends for Player ID {}'.format(player_id))
    plt.xlabel('Competition ID')
    plt.ylabel('Total Score')
    plt.show()