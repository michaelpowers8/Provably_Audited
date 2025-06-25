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

def seeds_to_results(server_seed:str,client_seed:str,nonce:int) -> str:
    hexs = seeds_to_hexadecimals(server_seed=server_seed,client_seed=client_seed,nonce=nonce)
    bytes_lists:list[list[int]] = [hexadecimal_to_bytes(current_hex) for current_hex in hexs]
    row:list[list[int]] = []
    for bytes_list in bytes_lists:
        for index in range(0,len(bytes_list),4):
            row.append(bytes_to_number(bytes_list[index:index+4],16777216))
            if(len(row)==1):
                return floor(((16777216)/(row[0]+1)*(1-0.01))*100)/100

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
    bar_heights:list[float|int] = [(x+2)**1.12 for x in range(len(values))]
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    
    # Create bar chart
    bars:BarContainer = plt.bar(range(len(keys)), bar_heights, width=0.6, color=colors, edgecolor='black')
    
    # Customize the plot
    plt.title('Occurrences of Milestone Multipliers', fontsize=16)
    plt.xlabel('Multiplier', fontsize=14)
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
    pdf.cell(200, 10, text="LIMBO ANALYSIS - SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_xy(10,30)
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["summary"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 2: Milestone Multiplier Frequency ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="MILESTONE MULTIPLIER FREQUENCY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[0], x=8, y=30, w=190)  # No filename needed!
    pdf.set_xy(12,150)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
            w=190,
            h=10,
            text="""HOW TO READ THIS CHART:
This chart shows the frequency of various milestone multipliers commonly bet on in Limbo. The numbers inside the bars represent how many multipliers were equal to the target below, or larger. For example, if the bar above 1,000,000 had a 5 in it, that means there were 5 instances where the resulting multiplier was 1,000,000 or larger. If the bar above the multiplier 500 has the number 350 in it, that means there were 350 instances where the resulting multiplier was at least 500 AND smaller than 1,000.""",
            border=0,
            align='L'
        )

    # --- Page 3: Winning/Losing Streaks ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="WINNING/LOSING STREAKS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=14)
    for line in analysis_data["winning_losing_streaks"].split('\n'):
        if "Statistical Summary of" in line:
            # This is a table header
            pdf.set_font("Helvetica", size=12, style='B')
            pdf.cell(0, 10, text=line.replace("Statistical Summary of", "").strip(":").strip(), 
                    border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Courier", size=10)  # Use monospace for tables
            
            # Get the next line which contains the column headers
            headers = analysis_data["winning_losing_streaks"].split('\n')[analysis_data["winning_losing_streaks"].split('\n').index(line)+1].split('|')
            # Get the line after that which contains the data
            data_line = next(iter(analysis_data["winning_losing_streaks"].split('\n')[i+2] for i, l in enumerate(analysis_data["winning_losing_streaks"].split('\n')) if l == line))
            data = data_line.split('|')
            
            # Draw table
            col_width = 25  # Adjust as needed
            pdf.set_fill_color(200, 220, 255)
            
            # Header row
            for header in headers:
                pdf.cell(col_width, 8, header.strip(), border=1, align='C', fill=True)
            pdf.ln()
            
            # Data row
            for item in data:
                pdf.cell(col_width, 8, item.strip(), border=1, align='C')
            pdf.ln()
            
            pdf.set_font("Helvetica", size=14)  # Reset font
        elif("|" in line):
            pass
        else:
            pdf.cell(0, 10, text=line, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 2: Milestone Multiplier Frequency ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="CUMULATIVE NET PROFIT OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[1], x=8, y=30, w=190)  # No filename needed!

    pdf.output(filename)

def main():
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    server:str = configuration["ServerSeed"]
    server_hashed:str = sha256_encrypt(server)
    client:str = configuration["ClientSeed"]
    nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
    target_multiplier = configuration["TargetMultiplier"]
    win_chance = ((1/target_multiplier)*0.99)*100
    bet_size = configuration["BetSize"]

    results:list[list[float|int]] = []
    current_result:list[int] = []
    cumulative_profit:list[float] = []

    biggest_winning_streak:tuple[int,int] = (0,0)
    biggest_losing_streak:tuple[int,int] = (0,0)

    current_winning_streak:int = 0
    current_losing_streak:int = 0

    winning_streaks:list[int] = []
    losing_streaks:list[int] = []

    total_number_of_wins:int = 0
    total_number_of_losses:int = 0

    total_games_played:int = 0
    total_money_bet:float = 0
    cumulative_games:list[int] = []

    money_won:float = 0

    milestone_multiplier:dict[int,int] = {
            1_000_000:0,
            500_000:0,
            250_000:0,
            100_000:0,
            50_000:0,
            25_000:0,
            10_000:0,
            5_000:0,
            2_500:0,
            1_000:0,
            500:0,
            250:0,
            100:0,
            50:0,
            25:0,
            10:0,
            5:0,
            2:0,
            1.01:0
        }
    milestone_multiplier[target_multiplier] = 0
    milestone_multiplier = dict(sorted(milestone_multiplier.items(),reverse=True))

    for nonce in nonces:
        total_games_played += 1
        cumulative_games.append(total_games_played)
        total_money_bet += bet_size
        current_result = [server,server_hashed,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
        for key,item in milestone_multiplier.items():
            if(seed_result>key):
                milestone_multiplier[key] += 1
                break
        if(seed_result < target_multiplier):
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            if(current_winning_streak>0):
                winning_streaks.append(current_winning_streak)
            current_winning_streak = 0
            current_losing_streak += 1
            total_number_of_losses +=1
            current_result.extend([target_multiplier,seed_result,"NO",bet_size,0,round(total_money_bet,2),round(money_won,2)])
        else:
            if(current_losing_streak > biggest_losing_streak[1]):
                biggest_losing_streak = (nonce-current_losing_streak,current_losing_streak)
            if(current_losing_streak>0):
                losing_streaks.append(current_losing_streak)
            current_losing_streak = 0
            current_winning_streak += 1
            total_number_of_wins += 1
            money_won += (bet_size*target_multiplier)
            current_result.extend([target_multiplier,round(seed_result,2),"YES",bet_size,round(bet_size*target_multiplier,2),round(total_money_bet,2),round(money_won,2)])
        results.append(current_result)
        cumulative_profit.append(money_won-total_money_bet)

    df:DataFrame = DataFrame(results,columns=["Server Seed","Server Seed (Hashed)","Client Seed","Nonce","Target","Result","Win","Bet Size","Money Won (Round)","Total Money Wagered","Total Gross Winnings"])
    df.to_csv(f"LIMBO_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    df.to_json(f"LIMBO_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.json",orient='table',indent=4)
    del df

    analysis_data:dict[str,int|float|str] = {
        "summary":f"""Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Target Multiplier: {target_multiplier:,.2f}x
{'-'*130}
Total Games Played: {total_games_played:,.0f}
Theoretical Number of Wins: {(total_games_played/target_multiplier)*0.99:,.2f}
Actual Number of Wins: {total_number_of_wins:,.0f}
{'-'*130}
Theoretical Number of Losses: {total_games_played - ((total_games_played/target_multiplier)*0.99):,.2f}
Actual Number of Losses: {total_number_of_losses:,.0f}
{'-'*130}
Total Money Wagered: ${total_money_bet:,.2f}
Gross Winnings: ${money_won:,.2f}
Net Winnings: ${abs(total_money_bet-money_won):,.2f} {"won" if money_won-total_money_bet>0 else "lost"}
{'-'*130}
Theoretical House Edge: 1.00%
Theoretical Return to Player (RTP): 99.00%
Actual House Edge: {(1-(money_won/total_money_bet))*100:,.2f}%
Return to Player (RTP): {(money_won/total_money_bet)*100:,.2f}%""",

        "winning_losing_streaks":f"""Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Mean Winning Streak: {mean(winning_streaks):,.3f}
Median Winning Streak: {median(winning_streaks):,.1f}
Statistical Summary of Winning Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(winning_streaks) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streaks,0.25) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{median(winning_streaks) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streaks,0.75) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streaks,0.95) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(winning_streaks,0.99) if len(winning_streaks)>0 else 0:,.0f}\t\t|\t\t{max(winning_streaks) if len(winning_streaks)>0 else 0:,.0f}
{'-'*120}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
Mean Losing Streak: {mean(losing_streaks):,.3f}
Median Losing Streak: {median(losing_streaks):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(losing_streaks) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streaks,0.25) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{median(losing_streaks) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streaks,0.75) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streaks,0.95) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{quantile(losing_streaks,0.99) if len(losing_streaks)>0 else 0:,.0f}\t\t|\t\t{max(losing_streaks) if len(losing_streaks)>0 else 0:,.0f}""",
        }
    generate_analysis_pdf(analysis_data,"LIMBO_ANALYSIS.pdf",[
                        plot_occurrences(milestone_multiplier),
                        plot_accumulation(cumulative_games,cumulative_profit,'Net Profit','Red','Cumulative Net Profit Over Time','Net Profit')
                    ]
                )

if __name__ == "__main__":
    main()