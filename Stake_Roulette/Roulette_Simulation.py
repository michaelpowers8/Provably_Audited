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
            row.append(bytes_to_number(bytes_list[index:index+4],37))
            if(len(row)==1):
                return row[0]

def generate_analysis_pdf(analysis_data:dict[str,str], filename:str, img_buffers:list[BytesIO]):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Auto-page-break with margin
    
    # --- Page 1: Summary ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="ROULETTE ANALYSIS - SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["summary"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 2: Color Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="RED/BLACK ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["colors"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 3: Color Trend ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="RED/BLACK TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[0], x=8, y=30, w=190, h=160)  # No filename needed!

    # --- Page 4: Individual Number Frequencies ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="INDIVIDUAL NUMBER FREQUENCY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[1], x=8, y=30, w=190)  # No filename needed!

    # --- Page 5: Balance Trend ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="BALANCE OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[2], x=8, y=30, w=190)  # No filename needed!
    
    # --- Page 3: 1-18 / 19-36 Analysis ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=18, style='B')
    pdf.cell(200, 10, text="NUMBER RANGE ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text=analysis_data["dozens"])
    
    # Add more pages as needed...
    
    pdf.output(filename)

def thousands_formatter(x, pos):
    return f"{x:,.0f}"

def plot_occurrences(occurrence_dict:dict[int,int]) -> BytesIO:
    """
    Creates a bar chart from a dictionary of occurrences.
    
    Parameters:
    occurrence_dict (dict): Dictionary with keys 0-36 and integer values
    """
    # Validate input
    if not all(isinstance(k, int) and 0 <= k <= 36 for k in occurrence_dict.keys()):
        raise ValueError("All keys must be integers between 0 and 36 inclusive")
    if not all(isinstance(v, int) and v >= 0 for v in occurrence_dict.values()):
        raise ValueError("All values must be non-negative integers")
    
    # Prepare data
    keys = sorted(occurrence_dict.keys())
    values = [occurrence_dict[k] for k in keys]
    colors = list(roulette_numbers_colors.values())
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    
    # Create bar chart
    bars:BarContainer = plt.bar(keys, values, color=colors, edgecolor='black')
    
    # Customize the plot
    plt.title('Occurrences of Numbers 0-36', fontsize=16)
    plt.xlabel('Number', fontsize=14)
    plt.ylabel('Occurrences', fontsize=14)
    plt.xticks(keys, rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    # Apply formatter to both axes
    plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    
    # Add value labels - vertical, centered, bold, and formatted
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2.,  # x-position: center of bar
                    height/2,  # y-position: middle of bar height
                    f'{height:,.0f}',  # Formatted number with thousand separators
                    ha='center', va='center',  # centered both horizontally and vertically
                    fontsize=9,
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

if __name__ == "__main__":
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    if(True):
        # Configuration Variables
        server:str = configuration["ServerSeed"]
        server_hashed:str = sha256_encrypt(server)
        client:str = configuration["ClientSeed"]
        nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
        single_number_bets:dict[str,float|int] = configuration["SingleNumberBets"]
        vertical_column_bets:dict[str,float|int] = configuration["VerticalColumnBets"]
        dozen_bets:dict[str,float|int] = configuration["DozenBets"]
        one_to_one_bets:dict[str,float|int] = configuration["OnetoOneBets"]
        roulette_numbers_colors:dict[str,str] = configuration["RouletteColors"]
        balance:float = 1_000_000
        cumulative_balance:list[float] = []

        results:list[list[float|int]] = []
        current_result:list[int] = []

        biggest_winning_streak:tuple[int,int] = (0,0)
        biggest_losing_streak:tuple[int,int] = (0,0)

        current_winning_streak:int = 0
        current_losing_streak:int = 0

        total_number_of_wins:int = 0
        total_number_of_losses:int = 0

        total_games_played:int = 0
        total_money_bet:float = 0
        cumulative_games:list[int] = []

        money_won:float = 0
        round_winnings:float = 0
        round_bettings:float = 0
        num_games_with_net_profit:int = 0
        num_games_without_total_loss:int = 0
        num_games_with_total_loss:int = 0

        num_1_to_12:int = 0
        num_13_to_24:int = 0
        num_25_to_36:int = 0

        num_column_1:int = 0
        num_column_2:int = 0
        num_column_3:int = 0

        num_1_to_18:int = 0
        num_19_to_36:int = 0

        num_evens:int = 0
        num_odds:int = 0

        num_red:int = 0
        biggest_red_streak:int = 0
        current_red_streak:int = 0
        num_black:int = 0
        cumulative_reds:list[int] = []

        biggest_black_streak:int = 0
        current_black_streak:int = 0
        cumulative_blacks:list[int] = []

        num_single_number_bets_hit:int = 0
        single_number_occurrences:dict[int,int] = {}
        for key in range(37):
            single_number_occurrences[key] = 0

        nonces_with_result_0:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        cumulative_games.append(total_games_played)
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
        single_number_occurrences[seed_result] += 1
        
        round_winnings:float = 0
        round_bettings:float = 0
        round_bettings += sum(list(single_number_bets.values()))
        round_bettings += sum(list(vertical_column_bets.values()))
        round_bettings += sum(list(dozen_bets.values()))
        round_bettings += sum(list(one_to_one_bets.values()))
        total_money_bet += round_bettings
        balance -= round_bettings

        # Declaring which column of the roulette table the result lies (Zero Excluded)
        if(seed_result%3==1):
            num_column_1 += 1
        elif(seed_result%3==2):
            num_column_2 += 1
        elif((seed_result%3==0)and(seed_result>0)):
            num_column_3 += 1

        # Declare which dozen the result lies (Zero Excluded)
        if(seed_result>=1 and seed_result<=12):
            num_1_to_12 += 1
        elif(seed_result>=13 and seed_result<=24):
            num_13_to_24 += 1
        elif(seed_result>=25 and seed_result<=36):
            num_25_to_36 += 1

        # Declare which half of numbers the result lies (Zero excluded)
        if(seed_result>=1 and seed_result<=18):
            num_1_to_18 += 1
        elif(seed_result>=19 and seed_result<=36):
            num_19_to_36 += 1

        # Declare if the result is even or odd (Zero is excluded)
        if((seed_result>0)and(seed_result%2==0)):
            num_evens += 1
        elif(seed_result%2==1):
            num_odds += 1

        # Declare which color the result is (Green Zero Excluded)
        if(roulette_numbers_colors[str(seed_result)]=='Black'):
            num_black += 1
            current_black_streak += 1
            if(current_red_streak > biggest_red_streak):
                biggest_red_streak = current_red_streak
            current_red_streak = 0
        elif(roulette_numbers_colors[str(seed_result)]=="Red"):
            num_red += 1
            current_red_streak += 1
            if(current_black_streak > biggest_black_streak):
                biggest_black_streak = current_black_streak
            current_black_streak = 0
        cumulative_blacks.append(num_black)
        cumulative_reds.append(num_red)
        
        # Checking if result is 0 and adding it to analysis statistics
        if(seed_result==0):
            nonces_with_result_0.append(f"{nonce:,.0f}")

        # Check if a single number bet was placed and won
        round_winnings += single_number_bets[str(seed_result)]*36 # Multiplier is 36 since initial bet is deducted from the balance and then reimbursed. Net gains is still x35 bet size. Same rule applies to all future bets and multipliers below
        if(round_winnings>0):
            num_single_number_bets_hit += 1

        # Run conditions and add winnings for any result that is not zero
        if(seed_result > 0):
            # Add winnings for betting on the column the result lies
            round_winnings += vertical_column_bets[str(seed_result%3)]*3

            # Add winnings for betting on the correct dozen the result lies
            if((seed_result >= 1)and(seed_result <= 12)):
                round_winnings += dozen_bets["1-12"]*3
            elif((seed_result >= 13)and(seed_result <= 25)):
                round_winnings += dozen_bets["13-24"]*3
            else:
                round_winnings += dozen_bets["25-36"]*3

            # Add winnings for betting 1-18 or 19-36 and winning
            if(seed_result<=18):
                round_winnings += one_to_one_bets["1-18"]*2
            else:
                round_winnings += one_to_one_bets["19-36"]*2

            # Add winnings for betting even or odd and winning
            if(seed_result%2==0):
                round_winnings += one_to_one_bets["Even"]*2
            else:
                round_winnings += one_to_one_bets["Odd"]*2

            # Add winnings for betting red or black and winning. "Else" works because we checked at the top if the result is greater than 0
            if(roulette_numbers_colors[str(seed_result)]=='Red'):
                round_winnings += one_to_one_bets["Red"]*2
            else:
                round_winnings += one_to_one_bets["Black"]*2

        # Begin analyzing this round's winnings
        # Check if player won more than they bet on the table
        if(round_winnings > round_bettings):
            num_games_with_net_profit += 1
            total_number_of_wins += 1
        # Check if player lost some money on the table, but not everything
        elif((round_bettings >= round_winnings) and (round_winnings>0)):
            num_games_without_total_loss += 1
            total_number_of_losses += 1
        # Player did not win any of their bets placed
        else:
            num_games_with_total_loss += 1
            total_number_of_losses += 1
        
        money_won += round_winnings
        balance += round_winnings

        cumulative_balance.append(balance)
        current_result.extend([seed_result,balance,round_bettings,round_winnings,roulette_numbers_colors[str(seed_result)]])
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Balance","Total Wager (Round)","Gross Winnings (Round)","Color"]).to_csv(f"ROULETTE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    analysis_data:dict[str,int|float|str] = {
        "summary":f"""Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Total Games Played: {total_games_played:,.0f}
Number of Wins: {total_number_of_wins:,.0f}
Number of Partial Losses: {num_games_without_total_loss:,.0f}
Number of Total Losses: {num_games_with_total_loss:,.0f}
Total Money Wagered: ${total_money_bet:,.2f}
Gross Winnings: ${money_won:,.2f}
Net Winnings: ${abs(total_money_bet-money_won):,.2f} {"won" if money_won-total_money_bet>0 else "lost"}
Theoretical House Edge: 2.70%
Theoretical Return to Player (RTP): 97.30%
Actual House Edge: {(1-(money_won/total_money_bet))*100:,.2f}%
Return to Player (RTP): {(money_won/total_money_bet)*100:,.2f}%""",

        "single_bets":f"""Number of Single Bets Won: {num_single_number_bets_hit:,.0f}""",

        "colors":f"""Theoretical Number of Blacks: {((18/37)*total_games_played):,.2f}
Actual Number of Blacks: {num_black:,.0f}
Theoretical Percent of Blacks: {(18/37)*100:,.2f}%
Actual Percent of Blacks: {(num_black/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_black])/max([((18/37)*total_games_played),num_black])))*100:,.3f}%
Largest Streak of Blacks: {biggest_black_streak:,.0f}
Money Wagered on Black: ${one_to_one_bets['Black']*total_games_played:,.2f}
Gross Winnings on Black: ${one_to_one_bets['Black']*num_black*2:,.2f}
Net Winnings on Black: ${abs((one_to_one_bets['Black']*total_games_played)-(one_to_one_bets['Black']*num_black*2)):,.2f} {"won" if (one_to_one_bets['Black']*num_black*2)-(one_to_one_bets['Black']*total_games_played)>0 else "lost"}
{'-'*130}
Theoretical Number of Reds: {((18/37)*total_games_played):,.2f}
Actual Number of Reds: {num_red:,.0f}
Theoretical Percent of Reds: {(18/37)*100:,.2f}%
Actual Percent of Reds: {(num_red/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_red])/max([((18/37)*total_games_played),num_red])))*100:,.3f}%
Largest Streak of Reds: {biggest_red_streak:,.0f}
Money Wagered on Red: ${one_to_one_bets['Red']*total_games_played:,.2f}
Gross Winnings on Red: ${one_to_one_bets['Red']*num_red*2:,.2f}
Net Winnings on Red: ${abs((one_to_one_bets['Red']*total_games_played)-(one_to_one_bets['Red']*num_red*2)):,.2f} {"won" if (one_to_one_bets['Red']*num_red*2)-(one_to_one_bets['Red']*total_games_played)>0 else "lost"}""",

        "even_odd":f"""Number of Even: {num_evens:,.0f}\nNumber of Odds: {num_odds:,.0f}""",

        "half_the_numbers":f"""Number of 1-18: {num_1_to_18:,.0f}\nNumber of 19-36: {num_19_to_36:,.0f}""",

        "dozens":f"""Number of 1-12: {num_1_to_12:,.0f}
Number of 13-24: {num_13_to_24:,.0f}
Number of 25-36: {num_25_to_36:,.0f}""",

        "vertical_columns":f"""Number of Vertical Column 1: {num_column_1:,.0f}
Number of Vertical Column 2: {num_column_2:,.0f}
Number of Vertical Column 3: {num_column_3:,.0f}""",

        "zeros":f"""Number of 0's: {len(nonces_with_result_0):,.0f}\nNonces Resulting in 0: {"|".join(nonces_with_result_0)}"""
    }

    if(True): # Red vs Black Analysis
        plt.figure(figsize=(10, 6))
        plt.plot(cumulative_games, cumulative_reds, label="Reds", color="red", linewidth=2)
        plt.plot(cumulative_games, cumulative_blacks, label="Blacks", color="black", linewidth=2)
        plt.xlabel("Total Games Played")
        plt.ylabel("Cumulative Count")
        plt.title("Red vs Black Outcomes Over Time")
        plt.legend()
        plt.grid(True)
        # Apply formatter to both axes
        plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
        plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

        # Save the plot to a bytes buffer (instead of a file)
        img_buffer_red_black:BytesIO = BytesIO()
        plt.savefig(img_buffer_red_black, format='png', dpi=300, bbox_inches="tight")
        plt.close()  # Free memory
        img_buffer_red_black.seek(0)  # Rewind buffer to start

    if(True): # Cumulative Balance Over Time
        plt.figure(figsize=(10, 6))
        plt.plot(cumulative_games, cumulative_balance, label="Balance", color="blue", linewidth=2)
        plt.xlabel("Total Games Played")
        plt.ylabel("Cumulative Balance")
        plt.title("Cumulative Balance Over Time")
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
        plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

        # Save the plot to a bytes buffer (instead of a file)
        img_buffer_balance:BytesIO = BytesIO()
        plt.savefig(img_buffer_balance, format='png', dpi=300, bbox_inches="tight")
        plt.close()  # Free memory
        img_buffer_balance.seek(0)  # Rewind buffer to start

    generate_analysis_pdf(analysis_data,"ROULETTE_ANALYSIS.pdf",[img_buffer_red_black,plot_occurrences(single_number_occurrences),img_buffer_balance])