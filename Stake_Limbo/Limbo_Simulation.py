import os
import sys
import hmac
import json
import random
import string
import shutil
import hashlib
import traceback
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from typing import Any
from io import BytesIO
from math import floor
from pandas import DataFrame
from fpdf import FPDF,XPos,YPos
from numpy import mean,median,quantile
from datetime import datetime, timedelta
from matplotlib.ticker import FuncFormatter

LOG_FILE = "Limbo_Simulation_Log.xml"
ARCHIVE_FOLDER = "archive"
LOG_RETENTION_DAYS = 30  
BASE_DIR:str = os.path.dirname(os.path.abspath(__file__))

def save_variable_info(locals_dict:dict[str,Any]) -> None:
    # Get the current global and local variables
    globals_dict:dict[str,Any] = globals()
    
    # Combine them, prioritizing locals (to avoid duplicates)
    all_vars:dict[str,Any] = {**globals_dict, **locals_dict}
    
    # Filter out modules, functions, and built-ins
    variable_info:list[dict[str,str|int|float|list|set|dict|bytes]] = []
    for name, value in all_vars.items():
        # Skip special variables, modules, and callables
        if name.startswith('__') and name.endswith('__'):
            continue
        if callable(value):
            continue
        if isinstance(value, type(sys)):  # Skip modules
            continue
            
        # Get variable details
        var_type:str = type(value).__name__
        try:
            var_hash:str = hashlib.sha256(str(value).encode('utf-8')).hexdigest()
        except Exception:
            var_hash:str = "Unhashable"
        
        var_size:int = sys.getsizeof(value)
        
        variable_info.append({
            "Variable Name": name,
            "Type": var_type,
            "Hash": var_hash,
            "Size (bytes)": var_size
        })
    
    # Convert to a DataFrame for nice tabular output
    df:DataFrame = DataFrame(variable_info)
    df.to_json(os.path.join(BASE_DIR,"Boilerplate_Prediction_End_Variables.json"),orient='table',indent=4)

def get_current_log_filename(basepath:str) -> str:
    """Generates a log filename based on the current date."""
    return f"{basepath}/{LOG_FILE}_{datetime.now().strftime('%Y%m%d')}.xml"

def rotate_logs():
    """Checks if the log file date has changed and archives it if needed."""
    current_date = datetime.now().strftime("%Y%m%d")
    
    # Get the last modified date of the existing log file
    if os.path.exists(LOG_FILE):
        modified_time = datetime.fromtimestamp(os.path.getmtime(LOG_FILE)).strftime("%Y%m%d")

        if modified_time != current_date:  # If the log is from a previous day, archive it
            # Ensure archive folder exists
            if not os.path.exists(ARCHIVE_FOLDER):
                os.makedirs(ARCHIVE_FOLDER)

            # Move the old log file to archive with a date-based name
            archive_filename = f"{ARCHIVE_FOLDER}/{LOG_FILE}_{modified_time}.xml"
            shutil.move(LOG_FILE, archive_filename)

            # Perform cleanup of old logs
            delete_old_logs()

def delete_old_logs():
    """Deletes logs that are older than LOG_RETENTION_DAYS."""
    cutoff_date:datetime = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)

    if not os.path.exists(ARCHIVE_FOLDER):
        return  # No logs to delete

    for filename in os.listdir(ARCHIVE_FOLDER):
        if filename.startswith(f"{LOG_FILE}") and filename.endswith(".xml"):
            try:
                # Extract date from filename
                date_str:str = filename.replace(f"{LOG_FILE}", "").replace(".xml", "")
                log_date:datetime = datetime.strptime(date_str, "%Y%m%d")

                # Delete files older than retention period
                if log_date < cutoff_date:
                    file_path:str = os.path.join(ARCHIVE_FOLDER, filename)
                    os.remove(file_path)

            except ValueError:
                # Ignore files that don't match the expected date format
                pass

def log_to_xml(message:str, status="INFO", basepath=os.path.dirname(os.path.realpath(__file__))):
    """
    Logs a message to an XML file, ensuring daily log rotation and old log cleanup.
    """
    rotate_logs()  # Check if the date has changed and archive if necessary

    # Get the correct filename for today's log
    current_log_file = get_current_log_filename(basepath=basepath)

    # Create file if it does not exist
    if not os.path.exists(current_log_file):
        root = ET.Element("logs")
        tree = ET.ElementTree(root)
        tree.write(current_log_file)

    # Load existing XML file
    tree = ET.parse(current_log_file)
    root = tree.getroot()

    # Create log entry
    log_entry = ET.SubElement(root, "log")
    log_entry.set("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_entry.set("status", status)

    message_element = ET.SubElement(log_entry, "message")
    message_element.text = message

    # Write changes back to the file
    tree.write(current_log_file)

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

def _save_plot_to_buffer() -> BytesIO:
    """
    Saves the current matplotlib plot to a BytesIO buffer and resets the figure.
    
    Returns:
        BytesIO: Buffer containing the plot as a PNG image.
    """
    img_buffer:BytesIO = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
    plt.close()  # Free memory
    img_buffer.seek(0)  # Rewind buffer to start
    return img_buffer

def plot_occurrences(occurrence_dict: dict) -> BytesIO:
    """
    Plots the frequency of milestone multipliers and returns the image as a buffer.
    
    Args:
        occurrence_dict: Dictionary of {multiplier: frequency}.
    
    Returns:
        BytesIO: PNG image buffer.
    """
    keys = list(occurrence_dict.keys())
    values = [occurrence_dict[k] for k in keys]
    colors = ["red" if i % 2 == 0 else "blue" for i in range(len(keys))]
    
    # Plot bars
    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(keys)), [(x+2)**1.12 for x in range(len(values))],
                   width=0.6, color=colors, edgecolor='black')
    
    # Add labels and styling
    plt.title('Occurrences of Milestone Multipliers', fontsize=16)
    plt.xticks(ticks=range(len(keys)), labels=[f"{key:,}" for key in keys], rotation=90)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height/2, 
                f'{values[bars.index(bar)]:,.0f}', ha='center', va='center',
                fontsize=12, fontweight='bold', rotation='vertical', color='white')
    
    return _save_plot_to_buffer()

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

def _add_pdf_summary_page(pdf:FPDF, analysis_data:dict):
    # --- Page 1: Summary ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="LIMBO ANALYSIS - SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_xy(10,30)
    pdf.set_font("Helvetica", size=12)
    for text in analysis_data["summary"].split('\n'):
        pdf.cell(0, 10, text=text, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

def _add_milestone_multiplier_frequency(pdf:FPDF, img_buffers:list[BytesIO]):
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

def _statistical_summary_in_winning_losing_streak_page(pdf:FPDF, analysis_data:dict[str,int|float|str], line:str):
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

def _add_pdf_winning_losing_streak_page(pdf:FPDF, analysis_data:dict[str,int|float|str]):
    # --- Page 3: Winning/Losing Streaks ---
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style='B')
    pdf.cell(200, 10, text="WINNING/LOSING STREAKS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=14)
    for line in analysis_data["winning_losing_streaks"].split('\n'):
        if "Statistical Summary of" in line:
            _statistical_summary_in_winning_losing_streak_page(pdf=pdf, analysis_data=analysis_data, line=line)
        elif("|" in line):
            pass
        else:
            pdf.cell(0, 10, text=line, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

def generate_analysis_pdf(analysis_data:dict[str,str], filename:str, img_buffers:list[BytesIO]):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Auto-page-break with margin
    _add_pdf_summary_page(pdf=pdf, analysis_data=analysis_data)
    _add_milestone_multiplier_frequency(pdf=pdf, img_buffers=img_buffers)
    _add_pdf_winning_losing_streak_page(pdf=pdf, analysis_data=analysis_data)
    pdf.output(filename)

def verify_configuration(configuration:dict[str,str|int]) -> bool:
    required_keys:list[str] = ["ServerSeed","ClientSeed","MinimumNonce","MaximumNonce","TargetMultiplier","BetSize"]
    missing_keys:list[str] = []

    for key in required_keys:
        if key not in configuration.keys():
            missing_keys.append(key)

    if len(missing_keys) > 0:
        log_to_xml(message=f"Configuration missing {','.join(missing_keys)} keys. Terminating program.",status='CRITICAL')
        return False
    return True

def load_configuration() -> dict[str,str|int]:
    # Safely construct the full path to Configuration.json
    config_path:str = os.path.join(BASE_DIR, "Configuration.json")
    with open(config_path,"rb") as file:
        configuration:dict[str,str|int] = json.load(file)
    if verify_configuration(configuration=configuration):
        return None
    return configuration

def get_configuration_variables(configuration:dict[str,str|int]) -> tuple[str,str,str,list[int],str|int|float,str|float|int]:
    server:str = configuration["ServerSeed"]
    server_hashed:str = sha256_encrypt(server)
    client:str = configuration["ClientSeed"]
    nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
    target_multiplier:str|int|float = configuration["TargetMultiplier"]
    bet_size:str|int|float = configuration["BetSize"]
    return server,server_hashed,client,nonces,target_multiplier,bet_size

def _initialize_milestone_multipliers(target_multiplier:int) -> dict[int,int]:
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
    return milestone_multiplier

def _get_analysis_data(local_variables:dict):
    try:
        analysis_data:dict[str,int|float|str] = {
            "summary":f"""Server Seed: {local_variables["server"]}
Server Seed (Hashed): {local_variables['server_hashed']}
Client Seed: {local_variables['client']}
Nonces: {local_variables['nonces'][0]:,.0f} - {local_variables['nonces'][-1]:,.0f}
Target Multiplier: {local_variables['target_multiplier']:,.2f}x
{'-'*130}
Total Games Played: {local_variables['total_games_played']:,.0f}
Theoretical Number of Wins: {(local_variables['total_games_played']/local_variables['target_multiplier'])*0.99:,.2f}
Actual Number of Wins: {local_variables['total_number_of_wins']:,.0f}
{'-'*130}
Theoretical Number of Losses: {local_variables['total_games_played'] - ((local_variables['total_games_played']/local_variables['target_multiplier'])*0.99):,.2f}
Actual Number of Losses: {local_variables['total_number_of_losses']:,.0f}
{'-'*130}
Total Money Wagered: ${local_variables['total_money_bet']:,.2f}
Gross Winnings: ${local_variables['money_won']:,.2f}
Net Winnings: ${abs(local_variables['total_money_bet']-local_variables['money_won']):,.2f} {"won" if local_variables['money_won']-local_variables['total_money_bet']>0 else "lost"}
{'-'*130}
Theoretical House Edge: 1.00%
Theoretical Return to Player (RTP): 99.00%
Actual House Edge: {(1-(local_variables['money_won']/local_variables['total_money_bet']))*100:,.2f}%
Return to Player (RTP): {(local_variables['money_won']/local_variables['total_money_bet'])*100:,.2f}%""",

        "winning_losing_streaks":f"""Biggest Winning Streak: {local_variables['biggest_winning_streak'][1]:,.0f}
Starting Nonce of Biggest Winning Streak: {local_variables['biggest_winning_streak'][0]:,.0f}
Mean Winning Streak: {mean(local_variables['winning_streaks']):,.3f}
Median Winning Streak: {median(local_variables['winning_streaks']):,.1f}
Statistical Summary of Winning Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(local_variables['winning_streaks']) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['winning_streaks'],0.25) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{median(local_variables['winning_streaks']) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['winning_streaks'],0.75) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['winning_streaks'],0.95) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['winning_streaks'],0.99) if len(local_variables['winning_streaks'])>0 else 0:,.0f}\t\t|\t\t{max(local_variables['winning_streaks']) if len(local_variables['winning_streaks'])>0 else 0:,.0f}
{'-'*120}
Biggest Losing Streak: {local_variables['biggest_losing_streak'][1]:,.0f}
Starting Nonce of Biggest Losing Streak: {local_variables['biggest_losing_streak'][0]:,.0f}
Mean Losing Streak: {mean(local_variables['losing_streaks']):,.3f}
Median Losing Streak: {median(local_variables['losing_streaks']):,.1f}
Statistical Summary of Losing Streaks:
\tMin\t\t|\t\t25%\t\t|\t\t50%\t\t|\t\t75%\t\t|\t\t95%\t\t|\t\t99%\t\t|\t\tMax
\t{min(local_variables['losing_streaks']) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['losing_streaks'],0.25) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{median(local_variables['losing_streaks']) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['losing_streaks'],0.75) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['losing_streaks'],0.95) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{quantile(local_variables['losing_streaks'],0.99) if len(local_variables['losing_streaks'])>0 else 0:,.0f}\t\t|\t\t{max(local_variables['losing_streaks']) if len(local_variables['losing_streaks'])>0 else 0:,.0f}""",
        }
        return analysis_data
    except Exception as e:
        log_to_xml(message=f"Error getting analysis data. Official error: {traceback.format_exc()}",status="CRITICAL")

class Limbo_Simulation_Tracker:
    def __init__(self):
        self.configuration:dict[str,str|int] = load_configuration()
        if self.configuration is None:
            return
        self.server,self.server_hashed,self.client,self.nonces,self.target_multiplier,self.bet_size = get_configuration_variables(configuration=self.configuration)

        self.results:list[list[float|int]] = []
        self.current_result:list[int] = []
        self.cumulative_profit:list[float] = []

        self.biggest_winning_streak:tuple[int,int] = (0,0)
        self.biggest_losing_streak:tuple[int,int] = (0,0)

        self.current_winning_streak:int = 0
        self.current_losing_streak:int = 0

        self.winning_streaks:list[int] = []
        self.losing_streaks:list[int] = []

        self.total_number_of_wins:int = 0
        self.total_number_of_losses:int = 0

        self.total_games_played:int = 0
        self.total_money_bet:float = 0
        self.cumulative_games:list[int] = []

        self.money_won:float = 0

        self.milestone_multiplier:dict[int,int] = _initialize_milestone_multipliers(target_multiplier=self.target_multiplier)
        self.milestone_multiplier = dict(sorted(self.milestone_multiplier.items(),reverse=True))   

    def run_simulation(self):
        try:
            for nonce in self.nonces:
                self.total_games_played += 1
                self.cumulative_games.append(self.total_games_played)
                self.total_money_bet += self.bet_size
                self.current_result = [self.server,self.server_hashed,self.client,nonce]
                seed_result = seeds_to_results(server_seed=self.server,client_seed=self.client,nonce=nonce)
                for key,item in self.milestone_multiplier.items():
                    if(seed_result>key):
                        self.milestone_multiplier[key] += 1
                        break
                if(seed_result < self.target_multiplier):
                    if(self.current_winning_streak > self.biggest_winning_streak[1]):
                        self.biggest_winning_streak = (nonce-self.current_winning_streak,self.current_winning_streak)
                    if(self.current_winning_streak>0):
                        self.winning_streaks.append(self.current_winning_streak)
                    self.current_winning_streak = 0
                    self.current_losing_streak += 1
                    self.total_number_of_losses +=1
                    self.current_result.extend([self.target_multiplier,seed_result,"NO",self.bet_size,0,round(self.total_money_bet,2),round(self.money_won,2)])
                else:
                    if(self.current_losing_streak > self.biggest_losing_streak[1]):
                        self.biggest_losing_streak = (nonce-self.current_losing_streak,self.current_losing_streak)
                    if(self.current_losing_streak>0):
                        self.losing_streaks.append(self.current_losing_streak)
                    self.current_losing_streak = 0
                    self.current_winning_streak += 1
                    self.total_number_of_wins += 1
                    self.money_won += (self.bet_size*self.target_multiplier)
                    self.current_result.extend([self.target_multiplier,round(seed_result,2),"YES",self.bet_size,round(self.bet_size*self.target_multiplier,2),round(self.total_money_bet,2),round(self.money_won,2)])
                self.results.append(self.current_result)
                self.cumulative_profit.append(self.money_won-self.total_money_bet) 
            self._save_raw_data()
        except Exception as e:
            log_to_xml(message=f"Error running simulation. Official error thrown: {traceback.format_exc()}")

    def _save_raw_data(self):
        try:
            df:DataFrame = DataFrame(self.results,columns=["Server Seed","Server Seed (Hashed)","Client Seed","Nonce","Target","Result","Win","Bet Size","Money Won (Round)","Total Money Wagered","Total Gross Winnings"])
            df.to_csv(os.path.join(BASE_DIR,f"LIMBO_RESULTS_{self.server}_{self.client}_{self.nonces[0]}_to_{self.nonces[-1]}.csv"),index=False)
            df.to_json(os.path.join(BASE_DIR,f"LIMBO_RESULTS_{self.server}_{self.client}_{self.nonces[0]}_to_{self.nonces[-1]}.json"),orient='table',indent=4)    
        except Exception as e:
            log_to_xml(f"Error saving raw data. Official error thrown: {traceback.format_exc()}")

def main():
    tracker:Limbo_Simulation_Tracker = Limbo_Simulation_Tracker()
    if tracker.configuration  is None:
        return
    tracker.run_simulation()
    analysis_data:dict[str,int|float|str] = _get_analysis_data(local_variables=tracker.__dict__)
    generate_analysis_pdf(
                analysis_data,os.path.join(BASE_DIR,"LIMBO_ANALYSIS.pdf"),[
                plot_occurrences(tracker.milestone_multiplier),
                plot_accumulation(tracker.cumulative_games,tracker.cumulative_profit,'Net Profit','Red','Cumulative Net Profit Over Time','Net Profit')
            ]
        )

if __name__ == "__main__":
    main()