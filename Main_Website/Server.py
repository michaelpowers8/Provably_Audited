import sys
sys.path.append("C:/Code/Provably_Audited/Stake_Plinko")
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from Plinko_Simulation import seeds_to_results, sha256_encrypt
from Multipliers import plinko_multipliers
from numpy import mean,median,quantile

app = Flask(__name__)
CORS(app)
@app.route('/run_plinko_simulation', methods=['POST'])
def run_plinko_simulation():
    try:
        data = request.json
        
        # Create a temporary configuration file
        config:dict[str,str|int|float] = {
            "ServerSeed": data.get('ServerSeed') or generate_server_seed(),
            "ClientSeed": data.get('ClientSeed') or generate_client_seed(),
            "MinimumNonce": int(data['nonceStart']),
            "MaximumNonce": int(data['nonceEnd']),
            "Risk": data['risk'],
            "Rows": int(data['rows']),
            "BetSize": float(data['betSize'])
        }
        
        # Run simulation (simplified for API)
        server = config["ServerSeed"]
        client = config["ClientSeed"]
        nonces = range(config["MinimumNonce"], config["MaximumNonce"] + 1)
        risk = config["Risk"]
        rows = config["Rows"]
        bet_size = config["BetSize"]
        
        # Initialize counters
        results = []
        stats:dict[str,int|list[float|int]] = {
            "total_wins": 0,
            "total_losses": 0,
            "biggest_win_streak": 0,
            "biggest_loss_streak": 0,
            "current_win_streak": 0,
            "current_loss_streak": 0,
            "money_won": 0,
            "top_multipliers": [],
            "second_multipliers": [],
            "third_multipliers": [],
            "winning_streak_sizes":[],
            "losing_streak_sizes":[]
        }
        
        # Process each nonce
        for nonce in nonces:
            prize_index, multiplier = seeds_to_results(server, client, nonce, risk, rows)
            results.append({
                "nonce": nonce,
                "prize index": prize_index,
                "multiplier": multiplier,
                "payout": f"${bet_size*multiplier:,.2f}"
            })
            stats["money_won"] += bet_size * multiplier
            
            if multiplier >= 1:
                stats["total_wins"] += 1
                stats["current_win_streak"] += 1
                if(stats["current_loss_streak"] > 0):
                    stats['losing_streak_sizes'].append(stats["current_loss_streak"])
                stats["current_loss_streak"] = 0
                if stats["current_win_streak"] > stats["biggest_win_streak"]:
                    stats["biggest_win_streak"] = stats["current_win_streak"]
            else:
                stats["total_losses"] += 1
                stats["current_loss_streak"] += 1
                if(stats["current_win_streak"] > 0):
                    stats['winning_streak_sizes'].append(stats["current_win_streak"])
                stats["current_win_streak"] = 0
                if stats["current_loss_streak"] > stats["biggest_loss_streak"]:
                    stats["biggest_loss_streak"] = stats["current_loss_streak"]
            
            # Track top multipliers
            if prize_index in [0, rows + 1]:
                stats["top_multipliers"].append(str(nonce))
            elif prize_index in [1, rows]:
                stats["second_multipliers"].append(str(nonce))
            elif prize_index in [2, rows - 1]:
                stats["third_multipliers"].append(str(nonce))
        
        # Prepare response
        response = {
            "config": config,
            "stats": stats,
            "results": results,
            "analysis": generate_plinko_analysis_text(config, stats),
            "server_seed_hashed": sha256_encrypt(config["ServerSeed"])
        }
        
        # Store results in temporary files
        # with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
        #     json.dump(results, f)
        #     response['raw_data_path'] = f.name
            
        # with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        #     f.write(response['analysis'])
        #     response['analysis_path'] = f.name
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_raw_data', methods=['POST'])
def download_raw_data():
    data = request.json
    try:
        # Create a more comprehensive raw data structure
        raw_data = {
            "config": data.get('config', {}),
            "stats": data.get('results', {}),
            "simulation_parameters": {
                "server_seed": data.get('config', {}).get('ServerSeed', ''),
                "client_seed": data.get('config', {}).get('ClientSeed', ''),
                "nonce_range": f"{data.get('config', {}).get('MinimumNonce', 0)}-{data.get('config', {}).get('MaximumNonce', 0)}",
                "risk_level": data.get('config', {}).get('Risk', ''),
                "rows": data.get('config', {}).get('Rows', 0),
                "bet_size": data.get('config', {}).get('BetSize', 0)
            },
            "results": data["results"]
        }
        
        return jsonify({
            'filename': f"plinko_simulation_raw_data.json",
            'content': json.dumps(raw_data, indent=4)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_analysis', methods=['POST'])
def download_analysis():
    data = request.json
    return jsonify({
        'filename': 'plinko_analysis.txt',
        'content': data['analysis']
    })

def generate_plinko_analysis_text(config:dict[str,str|int|float], stats:dict[str,int|list[float|int]]):
    multipliers = plinko_multipliers[f"{config['Risk']}{config['Rows']}"]
    total_wagered = (config['MaximumNonce'] - config['MinimumNonce'] + 1) * config['BetSize']
    net_result = stats['money_won'] - total_wagered
    rtp = (stats['money_won'] / total_wagered) * 100 if total_wagered > 0 else 0
    losing_streak_sizes = stats['losing_streak_sizes']
    win_streak_sizes = stats['winning_streak_sizes']
    
    return f"""PLINKO BALL {config['Risk'].upper()} RISK {config['Rows']} ROWS ANALYSIS
Server Seed: {config['ServerSeed']}
Server Seed (Hashed): {sha256_encrypt(config['ServerSeed'])}
Client Seed: {config['ClientSeed']}
Nonces: {config['MinimumNonce']:,} - {config['MaximumNonce']:,}
Number of games simulated: {(config['MaximumNonce'] - config['MinimumNonce'] + 1):,}
Number of Wins: {stats['total_wins']:,}
Number of Losses: {stats['total_losses']:,}
Win Rate: {(stats['total_wins'] / (stats['total_wins'] + stats['total_losses']) * 100):.2f}%
Biggest Winning Streak: {stats['biggest_win_streak']:,}
Biggest Losing Streak: {stats['biggest_loss_streak']:,}

WINNING STREAK ANALYSIS:
Mean Winning Streak: {mean(win_streak_sizes):,.3f}
Median Winning Streak: {median(win_streak_sizes):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(win_streak_sizes):,.0f}\t\t|\t\t{quantile(win_streak_sizes,0.25):,.0f}\t\t|\t\t{median(win_streak_sizes):,.0f}\t\t|\t\t{quantile(win_streak_sizes,0.75):,.0f}\t\t|\t\t{quantile(win_streak_sizes,0.95):,.0f}\t\t|\t\t{quantile(win_streak_sizes,0.99):,.0f}\t\t|\t\t{max(win_streak_sizes):,.0f}

LOSING STREAK ANALYSIS:
Mean Losing Streak: {mean(losing_streak_sizes):,.3f}
Median Losing Streak: {median(losing_streak_sizes):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(losing_streak_sizes):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.25):,.0f}\t\t|\t\t{median(losing_streak_sizes):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.75):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.95):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.99):,.0f}\t\t|\t\t{max(losing_streak_sizes):,.0f}

BETTING ANALYSIS
Bet Size: ${config['BetSize']:,.2f}
Total Money Wagered: ${total_wagered:,.2f}
Gross Winnings: ${stats['money_won']:,.2f}
Net Result: ${abs(net_result):,.2f} {'profit' if net_result > 0 else 'loss'}
Return to Player (RTP): {rtp:,.2f}%

MULTIPLIER ANALYSIS
Number of {multipliers[0]}x multipliers: {len(stats['top_multipliers']):,}
Nonces with {multipliers[0]}x: {', '.join(stats['top_multipliers'][:100])}{'...' if len(stats['top_multipliers']) > 100 else ''}
Number of {multipliers[1]}x multipliers: {len(stats['second_multipliers']):,}
Number of {multipliers[2]}x multipliers: {len(stats['third_multipliers']):,}"""

def generate_server_seed():
    import random
    return ''.join(random.choice('0123456789abcdef') for _ in range(64))

def generate_client_seed():
    import random
    return ''.join(random.choice('0123456789abcdef') for _ in range(20))

if __name__ == '__main__':
    app.run(debug=True)