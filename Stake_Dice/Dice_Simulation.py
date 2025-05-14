import hmac
import hashlib
import random
import string
from io import BytesIO
from math import floor
import json
from pandas import DataFrame
from fpdf import FPDF,XPos,YPos
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.ticker import FuncFormatter
from numpy import mean,median,quantile
from Mulitpliers import dice_multipliers

def generate_server_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(64)])
    return seed

def generate_client_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(20)])
    return seed

def sha256_encrypt(input_string: str) -> str:
    # Create a sha256 hash object
    sha256_hash = hashlib.sha256()
    
    # Update the hash object with the bytes of the input string
    sha256_hash.update(input_string.encode('utf-8'))
    
    # Return the hexadecimal representation of the hash
    return sha256_hash.hexdigest()

def seeds_to_hexadecimals(server_seed:str,client_seed:str,nonce:int) -> list[str]:
    messages:list[str] = [f"{client_seed}:{nonce}:{x}" for x in range(1)]
    hmac_objs:list[hmac.HMAC] = [hmac.new(server_seed.encode(),message.encode(),hashlib.sha256) for message in messages]
    return [hmac_obj.hexdigest() for hmac_obj in hmac_objs]

def hexadecimal_to_bytes(hexadecimal:str) -> list[int]:
    return list(bytes.fromhex(hexadecimal))

def bytes_to_basic_number(bytes_list: list[int]) -> int:
    # Calculate a weighted index based on the first four bytes
    number:float = ((float(bytes_list[0]) / float(256**1)) +
              (float(bytes_list[1]) / float(256**2)) +
              (float(bytes_list[2]) / float(256**3)) +
              (float(bytes_list[3]) / float(256**4)))
    return number

def bytes_to_number(bytes_list: list[int],multiplier:int) -> int:
    # Calculate a weighted index based on the first four bytes
    number:float =  (
                        (float(bytes_list[0]) / float(256**1)) +
                        (float(bytes_list[1]) / float(256**2)) +
                        (float(bytes_list[2]) / float(256**3)) +
                        (float(bytes_list[3]) / float(256**4))
                    )
    number = number*multiplier
    return floor(number)

def seeds_to_results(server_seed:str,client_seed:str,nonce:int) -> float:
    hexs = seeds_to_hexadecimals(server_seed=server_seed,client_seed=client_seed,nonce=nonce)
    bytes_lists:list[list[int]] = [hexadecimal_to_bytes(current_hex) for current_hex in hexs]
    row:list[list[int]] = []
    for bytes_list in bytes_lists:
        for index in range(0,len(bytes_list),4):
            row.append(bytes_to_number(bytes_list[index:index+4],10001))
            if(len(row)==1):
                return round(sum(row)/100,2)

def confirm_threshold_with_win_chance(over_under:str, threshold:float, win_chance:float) -> bool:
    if(
        (over_under.lower() == "under")and 
        (threshold == win_chance)
      ):
        return True
    
    if(
        (over_under.lower() == "over")and 
        (threshold+win_chance == 100)
      ):
        return True
    
    return False

def thousands_formatter(x, pos):
    return f"{x:,.0f}"

def thousands_formatter_with_dollar_signs(x, pos):
    return f"${x:,.0f}"

def plot_occurrences(occurrence_dict:dict[int,int]) -> BytesIO:
    """
    Creates a bar chart from a dictionary of occurrences.
    
    Parameters:
    occurrence_dict (dict): Dictionary with keys 0-36 and integer values
    """
    
    # Prepare data
    keys = list(occurrence_dict.keys())
    values = [occurrence_dict[k] for k in keys]
    colors = ["red" if index%2==0 else "blue" for index in range(len(keys))]
    bar_heights:list[float|int] = values
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    
    # Create bar chart
    bars:BarContainer = plt.bar(range(len(keys)), bar_heights, width=0.6, color=colors, edgecolor='black')
    
    # Customize the plot
    plt.title('Occurrences of Perfect Rolls', fontsize=16)
    plt.xlabel('Value', fontsize=14)
    plt.ylabel('Occurrences', fontsize=14)
    plt.xticks(ticks=range(len(keys)), labels=[f"{key:,}" for key in keys], rotation=90)
    plt.yticks(ticks=[max(bar_heights)*0.2,max(bar_heights)*0.4,max(bar_heights)*0.6,max(bar_heights)*0.8,max(bar_heights)],labels=[f"{quantile(values,0.2):,.0f}",f"{quantile(values,0.4):,.0f}",f"{quantile(values,0.6):,.0f}",f"{quantile(values,0.8):,.0f}",f"{max(values):,.0f}"])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels - vertical, centered, bold, and formatted
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2.,  # x-position: center of bar
                    height/2,  # y-position: middle of bar height
                    f'{values[bars.index(bar)]:,.0f}',  # Formatted number with thousand separators
                    ha='center', va='center',  # centered both horizontally and vertically
                    fontsize=12,
                    fontweight='bold',  # bold text
                    rotation='vertical',  # vertical text
                    color='white')  # text color
    
    # Adjust layout to prevent label cutoff
    # plt.tight_layout()
    
    # Save the plot to a bytes buffer (instead of a file)
    img_buffer:BytesIO = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
    plt.close()  # Free memory
    img_buffer.seek(0)  # Rewind buffer to start
    return img_buffer

def plot_accumulation(cumulative_games:list[int],cumulative_item_1:list[int],label_1:str,color_1:str,title:str,ylabel:str):
    plt.figure(figsize=(10, 6))
    # Plot the max point as a red dot
    plt.scatter(cumulative_games[cumulative_item_1.index(max(cumulative_item_1))], max(cumulative_item_1), color='black', s=50, label=f'Max: ({cumulative_games[cumulative_item_1.index(max(cumulative_item_1))]:,.0f}, ${max(cumulative_item_1):,.2f})',zorder=2)
    plt.scatter(cumulative_games[cumulative_item_1.index(min(cumulative_item_1))], min(cumulative_item_1), color='blue', s=50, label=f'Min: ({cumulative_games[cumulative_item_1.index(min(cumulative_item_1))]:,.0f}, ${min(cumulative_item_1):,.2f})',zorder=3)
    plt.plot(cumulative_games, cumulative_item_1, label=label_1, color=color_1, linewidth=1, zorder=1)
    plt.xlabel("Total Games Played")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    # Apply formatter to both axes
    plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter_with_dollar_signs))

    # Save the plot to a bytes buffer (instead of a file)
    img_buffer:BytesIO = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
    plt.close()  # Free memory
    img_buffer.seek(0)  # Rewind buffer to start
    return img_buffer

def generate_analysis_pdf(analysis_data:dict[str,str], filename:str, img_buffers:list[BytesIO]):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Auto-page-break with margin

    # --- Page 1: Summary ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="DICE ANALYSIS - SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_xy(10,30)
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["summary"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(filename)

if __name__ == "__main__":
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    if(True):
        server:str = configuration["ServerSeed"]
        server_hashed:str = sha256_encrypt(server)
        client:str = configuration["ClientSeed"]
        nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
        over_under:str = configuration["OverUnder"]
        threshold:float = round(configuration["Threshold"],2)
        bet_size:float = configuration["BetSize"]
        largest_bet_size:float = bet_size

        results:list[list[float|int]] = []
        current_result:list[int] = []

        biggest_winning_streak:tuple[int,int] = (0,0)
        biggest_losing_streak:tuple[int,int] = (0,0)

        current_winning_streak:int = 0
        current_losing_streak:int = 0
        losing_streak_sizes:list[int] = []
        winning_streak_sizes:list[int] = []

        total_number_of_wins:int = 0
        total_number_of_losses:int = 0
        total_games_played:int = 0

        balance:float = 10000
        starting_balance:float = balance
        biggest_balance:float = balance

        money_spent_over_current_losing_streak:float = 0
        most_money_spent_over_current_losing_streak:float = 0

        money_won:float = 0
        money_bet:float = 0
        perfect_rolls:dict[int,int] = {0:0,100:0}

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
        balance -= bet_size
        money_bet += bet_size
        if(balance < 0):
            break
        if(
            (
                (seed_result <= threshold)and
                (over_under == "Over")
            )
            or
            (
                (seed_result >= threshold)and
                (over_under == "Under")
            )
          ):
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            if(current_winning_streak>0):
                winning_streak_sizes.append(current_winning_streak)
            current_winning_streak = 0
            current_losing_streak += 1
            total_number_of_losses += 1
            money_spent_over_current_losing_streak += bet_size
            current_result.extend([over_under.upper(),threshold,seed_result,"NO",bet_size,0,money_bet,money_won])
        else:
            if(current_losing_streak > biggest_losing_streak[1]):
                biggest_losing_streak = (nonce-current_losing_streak,current_losing_streak)
            if(money_spent_over_current_losing_streak > most_money_spent_over_current_losing_streak):
                most_money_spent_over_current_losing_streak = money_spent_over_current_losing_streak
            if(current_losing_streak>0):
                losing_streak_sizes.append(current_losing_streak)
            current_losing_streak = 0
            money_spent_over_current_losing_streak = 0
            current_winning_streak += 1
            total_number_of_wins += 1
            money_won += (bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")])
            balance += bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")]
            if(balance > biggest_balance):
                biggest_balance = balance
            current_result.extend([over_under.upper(),threshold,seed_result,"YES",bet_size,bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")],round(money_bet,2),round(money_won,2)])
        if((seed_result > 99.99) or (seed_result < 0.01)):
            perfect_rolls[int(seed_result)] += 1
        results.append(current_result)
    df:DataFrame = DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Over Under","Threshold","Result","Win","Bet Size","Gross Winnings (Round)","Total Money Wagered","Gross Total Winnings"])
    df.to_csv(f"DICE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=True)
    df.to_json(f"DICE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.json",orient='table',indent=4)

    analysis_data:dict[str,int|float|str] = {
        "summary":f"""Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Threshold: {over_under.capitalize()} {threshold:,.2f}
{'-'*130}
Total Games Played: {total_games_played:,.0f}
Theoretical Number of Wins: {(total_games_played*(threshold/100)) if over_under=="Under" else (total_games_played*((100-threshold)/100)):,.2f}
Actual Number of Wins: {total_number_of_wins:,.0f}
{'-'*130}
Theoretical Number of Losses: {total_games_played - ((total_games_played*((100-threshold)/100))) if over_under=="Under" else (total_games_played*((threshold)/100)):,.2f}
Actual Number of Losses: {total_number_of_losses:,.0f}
{'-'*130}
Total Money Wagered: ${money_bet:,.2f}
Gross Winnings: ${money_won:,.2f}
Net Winnings: ${abs(money_bet-money_won):,.2f} {"won" if money_won-money_bet>0 else "lost"}
{'-'*130}
Theoretical House Edge: 1.00%
Theoretical Return to Player (RTP): 99.00%
Actual House Edge: {(1-(money_won/money_bet))*100:,.2f}%
Return to Player (RTP): {(money_won/money_bet)*100:,.2f}%""",

        "winning_losing_streaks":f"""Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Mean Winning Streak: {mean(winning_streak_sizes):,.3f}
Median Winning Streak: {median(winning_streak_sizes):,.1f}
Statistical Summary of Winning Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(winning_streak_sizes) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streak_sizes,0.25) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{median(winning_streak_sizes) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streak_sizes,0.75) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streak_sizes,0.95) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streak_sizes,0.99) if len(winning_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{max(winning_streak_sizes) if len(winning_streak_sizes)>0 else 0:,.0f}
{'-'*130}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
Mean Losing Streak: {mean(losing_streak_sizes):,.3f}
Median Losing Streak: {median(losing_streak_sizes):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(losing_streak_sizes) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.25) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{median(losing_streak_sizes) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.75) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.95) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.99) if len(losing_streak_sizes)>0 else 0:,.0f}\t\t|\t\t{max(losing_streak_sizes) if len(losing_streak_sizes)>0 else 0:,.0f}""",

    }
    generate_analysis_pdf(analysis_data,'DICE_ANALYSIS.pdf',[
                plot_occurrences()
            ])


    with open(f"DICE_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""DICE {over_under.upper()} {threshold} ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Initial Balance: ${starting_balance:,.2f}
Ending Balance: ${balance if balance>0 else 0:,.2f}
Largest Balance Ever: ${biggest_balance:,.2f}
Bet Size: ${bet_size:,.2f}
Largest Bet Made: ${largest_bet_size:,.2f}
Most Money Spent Over Losing Streak: ${most_money_spent_over_current_losing_streak:,.2f}
Winning Multiplier: {dice_multipliers[over_under][float(f"{threshold:.2f}")]:,.4f}
Net Profit per Win: ${bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")] - bet_size:,.2f}
Number of games simulated: {total_games_played:,.0f}
Number of wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Mean Losing Streak: {mean(losing_streak_sizes):,.3f}
Median Losing Streak: {median(losing_streak_sizes):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(losing_streak_sizes):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.25):,.0f}\t\t|\t\t{median(losing_streak_sizes):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.75):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.95):,.0f}\t\t|\t\t{quantile(losing_streak_sizes,0.99):,.0f}\t\t|\t\t{max(losing_streak_sizes):,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-money_bet):,.2f} {"won" if money_won-money_bet>0 else "lost"}.
Number of perfect {100 if over_under=="Over" else 0} rolls: {len(nonces_with_perfect_rolls):,.0f}

""")