import os
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
            row.append(bytes_to_number(bytes_list[index:index+4],37))
            if(len(row)==1):
                return row[0]

def generate_analysis_pdf(analysis_data:dict[str,str], filename:str, img_buffers:list[BytesIO]):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Auto-page-break with margin

    # --- Page 1: Summary ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="ROULETTE ANALYSIS - SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["summary"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 2: Winning/Losing Streaks ---
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
    
    # --- Page 3: Color Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="RED/BLACK ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=16)
    for text in analysis_data["colors"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 4: Color Trend ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="RED/BLACK/GREEN TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[0], x=8, y=30, w=190, h=160)  # No filename needed!

    # --- Page 5: Zero Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="ZERO ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=16)
    for text in analysis_data["zeros"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 6: Individual Number Frequencies ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="INDIVIDUAL NUMBER FREQUENCY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[1], x=8, y=30, w=190)  # No filename needed!

    # --- Page 7: Balance Trend ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="BALANCE OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[2], x=8, y=30, w=190)  # No filename needed!

    # --- Page 8: 1-18 and 19-36 Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="1-18 & 19-36 ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=16)
    for text in analysis_data["half_the_numbers"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 9: 1-18 / 19-36 Analysis ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="1-18 vs 19-36 TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[3], x=8, y=30, w=190, h=160)  # No filename needed!

    # --- Page 10: Even/Odd Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="EVEN/ODD ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=16)
    for text in analysis_data["even_odd"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 11: Even/Odd Analysis ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="EVEN/ODD TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[4], x=8, y=30, w=190, h=160)  # No filename needed!

    # --- Page 12: Dozens Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=20, style='B')
    pdf.cell(200, 10, text="DOZENS ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["dozens"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 13: Dozens Analysis ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="DOZENS TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[5], x=8, y=30, w=190, h=160)  # No filename needed!

    # --- Page 14: Vertical Columns Analysis ---
    pdf.add_page()  # Force new page
    pdf.set_font("Helvetica", size=20, style='B')
    pdf.cell(200, 10, text="VERTICAL COLUMNS ANALYSIS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["vertical_columns"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # --- Page 15: Vertical Columns Analysis ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="VERTICAL COLUMNS TRENDS OVER TIME", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image(img_buffers[6], x=8, y=30, w=190, h=160)  # No filename needed!
    
    # Add more pages as needed...
    
    pdf.output(filename)

def thousands_formatter(x, pos):
    return f"{x:,.0f}"

def plot_occurrences(occurrence_dict:dict[int,int],roulette_numbers_colors:dict[str,str]) -> BytesIO:
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

def plot_one_to_one_accumulation(cumulative_games:list[int],cumulative_one_to_one_1:list[int],cumulative_one_to_one_2:list[int],label_1:str,label_2:str,color_1:str,color_2:str,cumulative_0=None,title='Red vs Black Over Time'):
    plt.figure(figsize=(10, 6))
    plt.plot(cumulative_games, cumulative_one_to_one_1, label=label_1, color=color_1, linewidth=2)
    plt.plot(cumulative_games, cumulative_one_to_one_2, label=label_2, color=color_2, linewidth=2)
    if(cumulative_0):
        plt.plot(cumulative_games, cumulative_0, label='Zeros', color='green', linewidth=2)
    plt.xlabel("Total Games Played")
    plt.ylabel("Cumulative Count")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    # Apply formatter to both axes
    plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

    # Save the plot to a bytes buffer (instead of a file)
    img_buffer:BytesIO = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
    plt.close()  # Free memory
    img_buffer.seek(0)  # Rewind buffer to start
    return img_buffer

def plot_dozen_accumulation(cumulative_games:list[int],cumulative_dozen_1:list[int],cumulative_dozen_2:list[int],cumulative_dozen_3:list[int],label_1:str,label_2:str,label_3:str,color_1:str,color_2:str,color_3:str,title='Dozen Number Outcomes Over Time'):
    plt.figure(figsize=(10, 6))
    plt.plot(cumulative_games, cumulative_dozen_1, label=label_1, color=color_1, linewidth=2)
    plt.plot(cumulative_games, cumulative_dozen_2, label=label_2, color=color_2, linewidth=2)
    plt.plot(cumulative_games, cumulative_dozen_3, label=label_3, color=color_3, linewidth=2)
    plt.xlabel("Total Games Played")
    plt.ylabel("Cumulative Count")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    # Apply formatter to both axes
    plt.gca().xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

    # Save the plot to a bytes buffer (instead of a file)
    img_buffer:BytesIO = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
    plt.close()  # Free memory
    img_buffer.seek(0)  # Rewind buffer to start
    return img_buffer

def main():
    # Get the path to the folder this script is in
    BASE_DIR:str = os.path.dirname(os.path.abspath(__file__))

    # Safely construct the full path to Configuration.json
    config_path:str = os.path.join(BASE_DIR, "Configuration.json")
    with open(config_path,"rb") as file:
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

        winning_streaks:list[int] = []
        losing_streaks:list[int] = []

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

        num_0:int = 0
        biggest_0_streak:int = 0
        current_0_streak:int = 0
        cumulative_0:list[int] = []

        num_1_to_12:int = 0
        biggest_1_to_12_streak:int = 0
        current_1_to_12_streak:int = 0
        cumulative_1_to_12:list[int] = []

        num_13_to_24:int = 0
        biggest_13_to_24_streak:int = 0
        current_13_to_24_streak:int = 0
        cumulative_13_to_24:list[int] = []
        
        num_25_to_36:int = 0
        biggest_25_to_36_streak:int = 0
        current_25_to_36_streak:int = 0
        cumulative_25_to_36:list[int] = []

        num_column_1:int = 0
        biggest_column_1_streak:int = 0
        current_column_1_streak:int = 0
        cumulative_column_1:list[int] = []

        num_column_2:int = 0
        biggest_column_2_streak:int = 0
        current_column_2_streak:int = 0
        cumulative_column_2:list[int] = []

        num_column_3:int = 0
        biggest_column_3_streak:int = 0
        current_column_3_streak:int = 0
        cumulative_column_3:list[int] = []

        num_1_to_18:int = 0
        biggest_1_to_18_streak:int = 0
        current_1_to_18_streak:int = 0
        cumulative_1_to_18:list[int] = []

        num_19_to_36:int = 0
        biggest_19_to_36_streak:int = 0
        current_19_to_36_streak:int = 0
        cumulative_19_to_36:list[int] = []

        num_evens:int = 0
        biggest_even_streak:int = 0
        current_even_streak:int = 0
        cumulative_evens:list[int] = []

        num_odds:int = 0
        biggest_odd_streak:int = 0
        current_odd_streak:int = 0
        cumulative_odds:list[int] = []

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
            current_column_1_streak += 1
            if(current_column_2_streak > biggest_column_2_streak):
                biggest_column_2_streak = current_column_2_streak
            current_column_2_streak = 0
            if(current_column_3_streak > biggest_column_3_streak):
                biggest_column_3_streak = current_column_3_streak
            current_column_3_streak = 0
        elif(seed_result%3==2):
            num_column_2 += 1
            current_column_2_streak += 1
            if(current_column_1_streak > biggest_column_1_streak):
                biggest_column_1_streak = current_column_1_streak
            current_column_1_streak = 0
            if(current_column_3_streak > biggest_column_3_streak):
                biggest_column_3_streak = current_column_3_streak
            current_column_3_streak = 0
        elif((seed_result%3==0)and(seed_result>0)):
            num_column_3 += 1
            current_column_3_streak += 1
            if(current_column_2_streak > biggest_column_2_streak):
                biggest_column_2_streak = current_column_2_streak
            current_column_2_streak = 0
            if(current_column_1_streak > biggest_column_1_streak):
                biggest_column_1_streak = current_column_1_streak
            current_column_1_streak = 0
        cumulative_column_1.append(num_column_1)
        cumulative_column_2.append(num_column_2)
        cumulative_column_3.append(num_column_3)

        # Declare which dozen the result lies (Zero Excluded)
        if(seed_result>=1 and seed_result<=12):
            num_1_to_12 += 1
            current_1_to_12_streak += 1
            if(current_13_to_24_streak > biggest_13_to_24_streak):
                biggest_13_to_24_streak = current_13_to_24_streak
            current_13_to_24_streak = 0
            if(current_25_to_36_streak > biggest_25_to_36_streak):
                biggest_25_to_36_streak = current_25_to_36_streak
            current_25_to_36_streak = 0
        elif(seed_result>=13 and seed_result<=24):
            num_13_to_24 += 1
            current_13_to_24_streak += 1
            if(current_1_to_12_streak > biggest_1_to_12_streak):
                biggest_1_to_12_streak = current_1_to_12_streak
            current_1_to_12_streak = 0
            if(current_25_to_36_streak > biggest_25_to_36_streak):
                biggest_25_to_36_streak = current_25_to_36_streak
            current_25_to_36_streak = 0
        elif(seed_result>=25 and seed_result<=36):
            num_25_to_36 += 1
            current_25_to_36_streak += 1
            if(current_13_to_24_streak > biggest_13_to_24_streak):
                biggest_13_to_24_streak = current_13_to_24_streak
            current_13_to_24_streak = 0
            if(current_1_to_12_streak > biggest_1_to_12_streak):
                biggest_1_to_12_streak = current_1_to_12_streak
            current_1_to_12_streak = 0
        cumulative_1_to_12.append(num_1_to_12)
        cumulative_13_to_24.append(num_13_to_24)
        cumulative_25_to_36.append(num_25_to_36)

        # Declare which half of numbers the result lies (Zero excluded)
        if(seed_result>=1 and seed_result<=18):
            num_1_to_18 += 1
            current_1_to_18_streak += 1
            if(current_19_to_36_streak > biggest_19_to_36_streak):
                biggest_19_to_36_streak = current_19_to_36_streak
            current_19_to_36_streak = 0
        elif(seed_result>=19 and seed_result<=36):
            num_19_to_36 += 1
            current_19_to_36_streak += 1
            if(current_1_to_18_streak > biggest_1_to_18_streak):
                biggest_1_to_18_streak = current_1_to_18_streak
            current_1_to_18_streak = 0
        cumulative_1_to_18.append(num_1_to_18)
        cumulative_19_to_36.append(num_19_to_36)

        # Declare if the result is even or odd (Zero is excluded)
        if((seed_result>0)and(seed_result%2==0)):
            num_evens += 1
            current_even_streak += 1
            if(current_odd_streak > biggest_odd_streak):
                biggest_odd_streak = current_odd_streak
            current_odd_streak = 0
        elif(seed_result%2==1):
            num_odds += 1
            current_odd_streak += 1
            if(current_even_streak > biggest_even_streak):
                biggest_even_streak = current_even_streak
            current_even_streak = 0
        cumulative_evens.append(num_evens)
        cumulative_odds.append(num_odds)

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
            num_0 += 1
            current_0_streak += 1
            nonces_with_result_0.append(f"{nonce:,.0f}")
        else:
            if(current_0_streak > biggest_0_streak):
                biggest_0_streak = current_0_streak
            current_0_streak = 0
        cumulative_0.append(num_0)

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
            current_winning_streak += 1
            if(current_losing_streak > biggest_losing_streak[1]):
                biggest_losing_streak = (nonce-current_losing_streak,current_losing_streak)
            if(current_losing_streak>0):
                losing_streaks.append(current_losing_streak)
            current_losing_streak = 0
        # Check if player lost some money on the table, but not everything
        elif((round_bettings >= round_winnings) and (round_winnings>0)):
            num_games_without_total_loss += 1
            total_number_of_losses += 1
            current_losing_streak += 1
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            if(current_winning_streak>0):
                winning_streaks.append(current_winning_streak)
            current_winning_streak = 0
        # Player did not win any of their bets placed
        else:
            current_losing_streak += 1
            num_games_with_total_loss += 1
            total_number_of_losses += 1
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            if(current_winning_streak>0):
                winning_streaks.append(current_winning_streak)
            current_winning_streak = 0
        
        money_won += round_winnings
        balance += round_winnings

        cumulative_balance.append(balance)
        current_result.extend([seed_result,balance,round_bettings,round_winnings,roulette_numbers_colors[str(seed_result)]])
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Balance","Total Wager (Round)","Gross Winnings (Round)","Color"]).to_csv(os.path.join(BASE_DIR,f"ROULETTE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv"),index=False)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Balance","Total Wager (Round)","Gross Winnings (Round)","Color"]).to_json(os.path.join(BASE_DIR,f"ROULETTE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.json"),orient='table',indent=4)
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

        "winning_losing_streaks":f"""Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Mean Winning Streak: {mean(winning_streaks):,.3f}
Median Winning Streak: {median(winning_streaks):,.1f}
Statistical Summary of Winning Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(winning_streaks):,.0f}\t\t|\t\t{quantile(winning_streaks,0.25):,.0f}\t\t|\t\t{median(winning_streaks):,.0f}\t\t|\t\t{quantile(winning_streaks,0.75):,.0f}\t\t|\t\t{quantile(winning_streaks,0.95):,.0f}\t\t|\t\t{quantile(winning_streaks,0.99):,.0f}\t\t|\t\t{max(winning_streaks):,.0f}
{'-'*120}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
Mean Losing Streak: {mean(losing_streaks):,.3f}
Median Losing Streak: {median(losing_streaks):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(losing_streaks):,.0f}\t\t|\t\t{quantile(losing_streaks,0.25):,.0f}\t\t|\t\t{median(losing_streaks):,.0f}\t\t|\t\t{quantile(losing_streaks,0.75):,.0f}\t\t|\t\t{quantile(losing_streaks,0.95):,.0f}\t\t|\t\t{quantile(losing_streaks,0.99):,.0f}\t\t|\t\t{max(losing_streaks):,.0f}""",

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

        "half_the_numbers":f"""Theoretical Number of 1-18: {((18/37)*total_games_played):,.2f}
Actual Number of 1-18: {num_1_to_18:,.0f}
Theoretical Percent of 1-18: {(18/37)*100:,.2f}%
Actual Percent of 1-18: {(num_1_to_18/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_1_to_18])/max([((18/37)*total_games_played),num_1_to_18])))*100:,.3f}%
Largest Streak of 1-18: {biggest_1_to_18_streak:,.0f}
Money Wagered on 1-18: ${one_to_one_bets['1-18']*total_games_played:,.2f}
Gross Winnings on 1-18: ${one_to_one_bets['1-18']*num_1_to_18*2:,.2f}
Net Winnings on 1-18: ${abs((one_to_one_bets['1-18']*total_games_played)-(one_to_one_bets['1-18']*num_1_to_18*2)):,.2f} {"won" if (one_to_one_bets['1-18']*num_1_to_18*2)-(one_to_one_bets['1-18']*total_games_played)>0 else "lost"}
{'-'*130}
Theoretical Number of 19-36: {((18/37)*total_games_played):,.2f}
Actual Number of 19-36: {num_19_to_36:,.0f}
Theoretical Percent of 19-36: {(18/37)*100:,.2f}%
Actual Percent of 19-36: {(num_19_to_36/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_19_to_36])/max([((18/37)*total_games_played),num_19_to_36])))*100:,.3f}%
Largest Streak of 19-36: {biggest_19_to_36_streak:,.0f}
Money Wagered on 19-36: ${one_to_one_bets['19-36']*total_games_played:,.2f}
Gross Winnings on 19-36: ${one_to_one_bets['19-36']*num_19_to_36*2:,.2f}
Net Winnings on 19-36: ${abs((one_to_one_bets['19-36']*total_games_played)-(one_to_one_bets['19-36']*num_19_to_36*2)):,.2f} {"won" if (one_to_one_bets['19-36']*num_19_to_36*2)-(one_to_one_bets['19-36']*total_games_played)>0 else "lost"}""",

        "even_odd":f"""Theoretical Number of Even: {((18/37)*total_games_played):,.2f}
Actual Number of Even: {num_evens:,.0f}
Theoretical Percent of Even: {(18/37)*100:,.2f}%
Actual Percent of Even: {(num_evens/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_evens])/max([((18/37)*total_games_played),num_evens])))*100:,.3f}%
Largest Streak of Even: {biggest_even_streak:,.0f}
Money Wagered on Even: ${one_to_one_bets['Even']*total_games_played:,.2f}
Gross Winnings on Even: ${one_to_one_bets['Even']*num_evens*2:,.2f}
Net Winnings on Even: ${abs((one_to_one_bets['Even']*total_games_played)-(one_to_one_bets['Even']*num_evens*2)):,.2f} {"won" if (one_to_one_bets['Even']*num_evens*2)-(one_to_one_bets['Even']*total_games_played)>0 else "lost"}
{'-'*130}
Theoretical Number of Odd: {((18/37)*total_games_played):,.2f}
Actual Number of Odd: {num_odds:,.0f}
Theoretical Percent of Odd: {(18/37)*100:,.2f}%
Actual Percent of Odd: {(num_odds/total_games_played)*100:,.2f}%
Error: {(1-(min([((18/37)*total_games_played),num_odds])/max([((18/37)*total_games_played),num_odds])))*100:,.3f}%
Largest Streak of Odd: {biggest_odd_streak:,.0f}
Money Wagered on Odd: ${one_to_one_bets['Odd']*total_games_played:,.2f}
Gross Winnings on Odd: ${one_to_one_bets['Odd']*num_odds*2:,.2f}
Net Winnings on Odd: ${abs((one_to_one_bets['Odd']*total_games_played)-(one_to_one_bets['Odd']*num_odds*2)):,.2f} {"won" if (one_to_one_bets['Odd']*num_odds*2)-(one_to_one_bets['Odd']*total_games_played)>0 else "lost"}""",

        "dozens":f"""Theoretical Number of 1-12: {((12/37)*total_games_played):,.2f}
Actual Number of 1-12: {num_1_to_12:,.0f}
Theoretical Percent of 1-12: {(12/37)*100:,.2f}%
Actual Percent of 1-12: {(num_1_to_12/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_1_to_12])/max([((12/37)*total_games_played),num_1_to_12])))*100:,.3f}%
Largest Streak of 1-12: {biggest_1_to_12_streak:,.0f}
Money Wagered on 1-12: ${dozen_bets['1-12']*total_games_played:,.2f}
Gross Winnings on 1-12: ${dozen_bets['1-12']*num_1_to_12*3:,.2f}
Net Winnings on 1-12: ${abs((dozen_bets['1-12']*total_games_played)-(dozen_bets['1-12']*num_1_to_12*3)):,.2f} {"won" if (dozen_bets['1-12']*num_1_to_12*3)-(dozen_bets['1-12']*total_games_played)>0 else "lost"}
{'-'*120}
Theoretical Number of 13-24: {((12/37)*total_games_played):,.2f}
Actual Number of 13-24: {num_13_to_24:,.0f}
Theoretical Percent of 13-24: {(12/37)*100:,.2f}%
Actual Percent of 13-24: {(num_13_to_24/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_13_to_24])/max([((12/37)*total_games_played),num_13_to_24])))*100:,.3f}%
Largest Streak of 13-24: {biggest_13_to_24_streak:,.0f}
Money Wagered on 13-24: ${dozen_bets['13-24']*total_games_played:,.2f}
Gross Winnings on 13-24: ${dozen_bets['13-24']*num_13_to_24*3:,.2f}
Net Winnings on 13-24: ${abs((dozen_bets['13-24']*total_games_played)-(dozen_bets['13-24']*num_13_to_24*3)):,.2f} {"won" if (dozen_bets['13-24']*num_13_to_24*3)-(dozen_bets['13-24']*total_games_played)>0 else "lost"}
{'-'*120}
Theoretical Number of 25-36: {((12/37)*total_games_played):,.2f}
Actual Number of 25-36: {num_25_to_36:,.0f}
Theoretical Percent of 25-36: {(12/37)*100:,.2f}%
Actual Percent of 25-36: {(num_25_to_36/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_25_to_36])/max([((12/37)*total_games_played),num_25_to_36])))*100:,.3f}%
Largest Streak of 25-36: {biggest_25_to_36_streak:,.0f}
Money Wagered on 25-36: ${dozen_bets['25-36']*total_games_played:,.2f}
Gross Winnings on 25-36: ${dozen_bets['25-36']*num_25_to_36*3:,.2f}
Net Winnings on 25-36: ${abs((dozen_bets['25-36']*total_games_played)-(dozen_bets['25-36']*num_25_to_36*3)):,.2f} {"won" if (dozen_bets['25-36']*num_25_to_36*3)-(dozen_bets['25-36']*total_games_played)>0 else "lost"}""",

        "vertical_columns":f"""Theoretical Number of Vertical Column 1: {((12/37)*total_games_played):,.2f}
Actual Number of Vertical Column 1: {num_column_1:,.0f}
Theoretical Percent of Vertical Column 1: {(12/37)*100:,.2f}%
Actual Percent of Vertical Column 1: {(num_column_1/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_column_1])/max([((12/37)*total_games_played),num_column_1])))*100:,.3f}%
Largest Streak of Vertical Column 1: {biggest_column_1_streak:,.0f}
Money Wagered on Vertical Column 1: ${vertical_column_bets['1']*total_games_played:,.2f}
Gross Winnings on Vertical Column 1: ${vertical_column_bets['1']*num_column_1*3:,.2f}
Net Winnings on Vertical Column 1: ${abs((vertical_column_bets['1']*total_games_played)-(vertical_column_bets['1']*num_column_1*3)):,.2f} {"won" if (vertical_column_bets['1']*num_column_1*3)-(vertical_column_bets['1']*total_games_played)>0 else "lost"}
{'-'*120}
Theoretical Number of Vertical Column 2: {((12/37)*total_games_played):,.2f}
Actual Number of Vertical Column 2: {num_column_2:,.0f}
Theoretical Percent of Vertical Column 2: {(12/37)*100:,.2f}%
Actual Percent of Vertical Column 2: {(num_column_2/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_column_2])/max([((12/37)*total_games_played),num_column_2])))*100:,.3f}%
Largest Streak of Vertical Column 2: {biggest_column_2_streak:,.0f}
Money Wagered on Vertical Column 2: ${vertical_column_bets['2']*total_games_played:,.2f}
Gross Winnings on Vertical Column 2: ${vertical_column_bets['2']*num_column_2*3:,.2f}
Net Winnings on Vertical Column 2: ${abs((vertical_column_bets['2']*total_games_played)-(vertical_column_bets['2']*num_column_2*3)):,.2f} {"won" if (vertical_column_bets['2']*num_column_2*3)-(vertical_column_bets['2']*total_games_played)>0 else "lost"}
{'-'*120}
Theoretical Number of Vertical Column 3: {((12/37)*total_games_played):,.2f}
Actual Number of Vertical Column 3: {num_column_3:,.0f}
Theoretical Percent of Vertical Column 3: {(12/37)*100:,.2f}%
Actual Percent of Vertical Column 3: {(num_column_3/total_games_played)*100:,.2f}%
Error: {(1-(min([((12/37)*total_games_played),num_column_3])/max([((12/37)*total_games_played),num_column_3])))*100:,.3f}%
Largest Streak of Vertical Column 3: {biggest_column_3_streak:,.0f}
Money Wagered on Vertical Column 3: ${vertical_column_bets['0']*total_games_played:,.2f}
Gross Winnings on Vertical Column 3: ${vertical_column_bets['0']*num_column_3*3:,.2f}
Net Winnings on Vertical Column 3: ${abs((vertical_column_bets['0']*total_games_played)-(vertical_column_bets['0']*num_column_3*3)):,.2f} {"won" if (vertical_column_bets['0']*num_column_3*3)-(vertical_column_bets['0']*total_games_played)>0 else "lost"}""",

        "zeros":f"""Theoretical Number of Zeros: {((1/37)*total_games_played):,.2f}
Actual Number of Zeros: {num_0:,.0f}
Theoretical Percent of Zeros: {(1/37)*100:,.2f}%
Actual Percent of Zeros: {(num_0/total_games_played)*100:,.2f}%
Error: {(1-(min([((1/37)*total_games_played),num_0])/max([((1/37)*total_games_played),num_0])))*100:,.3f}%
Largest Streak of Zeros: {biggest_0_streak:,.0f}
Money Wagered on Zeros: ${single_number_bets['0']*total_games_played:,.2f}
Gross Winnings on Zeros: ${single_number_bets['0']*num_0*36:,.2f}
Net Winnings on Zeros: ${abs((single_number_bets['0']*total_games_played)-(single_number_bets['0']*num_0*36)):,.2f} {"won" if (single_number_bets['0']*num_0*36)-(single_number_bets['0']*total_games_played)>0 else "lost"}
Number of 0's: {len(nonces_with_result_0):,.0f}
First 10 Nonces Resulting in 0: {"|".join(nonces_with_result_0[:10])}"""
    }

    img_buffer_red_black:BytesIO = plot_one_to_one_accumulation(cumulative_games,cumulative_reds,cumulative_blacks,'Reds','Blacks','red','black',cumulative_0)
    img_buffer_1_to_18_19_to_36:BytesIO = plot_one_to_one_accumulation(cumulative_games,cumulative_1_to_18,cumulative_19_to_36,'1-18','19-36','blue','orange',title='1-18 vs 19-36 Outcomes Over Time')
    img_buffer_even_odd:BytesIO = plot_one_to_one_accumulation(cumulative_games,cumulative_evens,cumulative_odds,'Evens','Odds','purple','green', title='Even vs Odd Outcomes Over Time')
    img_buffer_1_to_12_13_to_24_25_to_36:BytesIO = plot_dozen_accumulation(cumulative_games,cumulative_1_to_12,cumulative_13_to_24,cumulative_25_to_36,'1-12','13-24','25-36','red','blue','black')
    img_buffer_vertical_columns:BytesIO = plot_dozen_accumulation(cumulative_games,cumulative_column_1,cumulative_column_2,cumulative_column_3,'Column 1','Column 2','Column 3','pink','blue','green',title='Vertical Outcomes Over Time')
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

    generate_analysis_pdf(analysis_data,os.path.join(BASE_DIR,"ROULETTE_ANALYSIS.pdf"),[
                img_buffer_red_black,
                plot_occurrences(single_number_occurrences,roulette_numbers_colors=roulette_numbers_colors),
                img_buffer_balance,
                img_buffer_1_to_18_19_to_36,
                img_buffer_even_odd,
                img_buffer_1_to_12_13_to_24_25_to_36,
                img_buffer_vertical_columns
            ]
        )

if __name__ == "__main__":
    main()