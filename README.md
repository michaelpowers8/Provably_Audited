# 🎰 Provably Audited Casino Game Simulations  
**Cryptographically verifiable simulations of popular casino games using server seeds, client seeds, and nonces**  

![GitHub](https://img.shields.io/github/license/michaelpowers8/Provably_Audited)  
![GitHub last commit](https://img.shields.io/github/last-commit/michaelpowers8/Provably_Audited)  

---

## 📖 Overview  
This repository contains **provably fair** simulations of casino games (Roulette, Plinko, Mines, Limbo, etc.) using:  
- **Server seeds** (hashed for transparency)  
- **Client seeds** (user-provided)  
- **Nonces** (sequential integers)  

Each game's outcome is generated via HMAC-SHA256, ensuring tamper-proof results that can be independently verified.  
This is designed to audit stake.us original games. Many people claim that bet size has an effect on the outcome of games you play. This repository gives people the opportunity to see if their games were indeed provably fair.

---

## 🎮 Games Included  

| Game         | Description                                   | Key Features                              |  
|--------------|-----------------------------------------------|-------------------------------------------|  
| **Roulette** | European roulette simulator                   | Tracks streaks, RTP, and color statistics |  
| **Plinko**   | Ball-drop multiplier game                     | Supports risk profiles (Low/Medium/High)  |  
| **Mines**    | Grid-based bomb avoidance game                | Custom mine layouts and multipliers       |  
| **Limbo**    | Multiplier prediction game                    | Analyzes milestone multiplier frequency   |  
| **Wheel**    | Spinning wheel with segments                  | Configurable risk/segment counts          |  
| **Pump**     | Volatility-based multiplier game              | Difficulty tiers (Easy to Expert)         |  
| **Flip**     | Consecutive coin flip prediction              | Custom sequence betting                   |  
| **Dice**     | Dice roll from 1-100 threshold prediction     | Custom strategy options                   |  

---

## 📂 Folder Structure  
```bash
Provably_Audited/  
├── Roulette/  
│   ├── Configuration.json    # Betting rules, seeds, nonce range  
│   ├── Roulette_Simulation.py  
│   └── Multipliers.py        # Payout multipliers  
├── Plinko/  
│   ├── Configuration.json    # Risk level, rows, bet size  
│   ├── Plinko_Simulation.py  
│   └── Multipliers.py  
├── Mines/  
│   ├── Configuration.json    # Mine count, grid layout  
│   ├── Mines_Simulation.py  
│   └── Multipliers.py  
└── ... (other games follow same structure)
```

---

## ⚙️ How It Works  
1. **Seeds & Nonces**:  
   - `ServerSeed`: Hashed initial state (verifiable post-simulation)  
   - `ClientSeed`: User-defined string  
   - `Nonce`: Incremental counter for each bet  

2. **Result Generation**:  
   ```python
   HMAC-SHA256(server_seed, f"{client_seed}:{nonce}:{index}")
   ```  
   Converted to game outcomes (e.g., roulette numbers, mine positions).  

3. **Analysis**:  
   - Win/loss streaks  
   - Return-to-Player (RTP)  
   - Statistical deviations from theoretical probabilities  

---

## 🛠️ Setup & Usage  
1. **Configure**: Edit `Configuration.json` for each game:  
   ```json
   {
       "ServerSeed": "your_seed_here",
       "ClientSeed": "user_input",
       "MinimumNonce": 1,
       "MaximumNonce": 1000,
       "Risk": "Medium",
       "BetSize": 2.0
   }
   ```  
2. **Run**: Execute the simulation script:  
   ```bash
   python Roulette_Simulation.py
   ```  
3. **Output**:  
   - CSV files with raw results  
   - PDF/Text reports with analytics  

---

## 📊 Example Output (Roulette)  
```
ROULETTE ANALYSIS  
-------------------------------------  
Server Seed: fa18081cb423... (hashed)  
Games Played: 10,000  
Theoretical RTP: 97.30%  
Actual RTP: 97.12%  
Biggest Winning Streak: 12  
Biggest Losing Streak: 18  
```  

---

## 📜 License  
MIT © [Michael Powers](https://github.com/michaelpowers8)  

---

## 📬 Contact  
- **Email**: [micpowers98@gmail.com](mailto:micpowers98@gmail.com)  

---

### 🌟 **Star this repo if you find it useful!**  
*Contributions welcome. Submit a PR or open an issue.*  

--- 

### Key Features:  
- **Transparency**: All scripts use open-source, verifiable logic.  
- **Modular Design**: Easily add new games or betting strategies.  
- **Detailed Analytics**: Streaks, RTP, and statistical summaries. 
