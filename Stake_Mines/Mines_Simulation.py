import hmac
import hashlib
import random
import string
from math import floor
from pandas import DataFrame
import json
from Multipliers import mines_multipliers

def sha256_encrypt(input_string: str) -> str:
    # Create a sha256 hash object
    sha256_hash = hashlib.sha256()
    
    # Update the hash object with the bytes of the input string
    sha256_hash.update(input_string.encode('utf-8'))
    
    # Return the hexadecimal representation of the hash
    return sha256_hash.hexdigest()

def seeds_to_hexadecimals(server_seed:str,client_seed:str,nonce:int) -> list[str]:
    messages:list[str] = [f"{client_seed}:{nonce}:{x}" for x in range(3)]
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
    
    number:int = floor(number*multiplier)
    return number

def number_to_shuffle(number:int,row:list[int]):
    return row[number]

def seeds_to_results(server_seed:str,client_seed:str,nonce:int,num_mines:str,prediction_configuration:list[list[int]],bet_size:float) -> tuple[float,list[list[str]],list[list[str]]]:
    shuffle:list[int] = list(range(25))
    hexs = seeds_to_hexadecimals(server_seed=server_seed,client_seed=client_seed,nonce=nonce)
    bytes_lists:list[list[int]] = [hexadecimal_to_bytes(current_hex) for current_hex in hexs]
    row:list[list[int]] = []
    final_shuffle:list[int] = []
    multiplier:int = 25
    for bytes_list in bytes_lists:
        for index in range(0,len(bytes_list),4):
            row.append(bytes_to_number(bytes_list[index:index+4],(multiplier)))
            multiplier -= 1

    for index,number in enumerate(row):
        final_shuffle.append(shuffle[number])
        shuffle.remove(shuffle[number])
    final_shuffle.append(shuffle[0])
    mines_locations:list[int] = final_shuffle[:num_mines]
    final_mines_coordinates:list[tuple[int,int]] = []
    for location in mines_locations:
        final_mines_coordinates.append(((location%5)+1,5-floor(location/5)))

    count:int = 0
    final_grid:list[list[str]] = [[" 💎 "]*5,[" 💎 "]*5,[" 💎 "]*5,[" 💎 "]*5,[" 💎 "]*5]
    final_clicks_grid:list[list[str]] = [[" 🟡 "]*5,[" 🟡 "]*5,[" 🟡 "]*5,[" 🟡 "]*5,[" 🟡 "]*5]
    payout_multiplier:float = round(bet_size*mines_multipliers[num_mines][sum(1 for sublist in prediction_configuration for item in sublist if item == 1)-1],2)
    row_reverse:int = 0
    for row in range(5,0,-1):
        for col in range(5):
            if(len(mines_locations)>0):
                if(((row,col+1) in final_mines_coordinates) and (prediction_configuration[row-1][col]==1)):
                    payout_multiplier = 0
                    final_grid[4-col][row-1] = f" 💣 "
                    final_clicks_grid[4-col][row-1] = f" 🔴 "
                    mines_locations.pop(0)
                elif(((row,col+1) in final_mines_coordinates)):
                    mines_locations.pop(0)
                    final_grid[4-col][row-1] = " 💣 "
                    final_clicks_grid[4-col][row-1] = " 🟡 "
                elif(prediction_configuration[row-1][col]==1):
                    final_grid[4-col][row-1] = " 💎 "
                    final_clicks_grid[4-col][row-1] = " 🟢 "
                else:
                    final_grid[4-col][row-1] = " 💎 "
                    final_clicks_grid[4-col][row-1] = " 🟡 "
            else:
                if(prediction_configuration[row-1][col]==1):
                    final_grid[4-col][row-1] = " 💎 "
                    final_clicks_grid[col][row-1] = " 🟢 "
                else:
                    final_grid[4-col][row-1] = " 💎 "
                    final_clicks_grid[4-col][row-1] = " 🟡 "
            count += 1
        row_reverse += 1
    return payout_multiplier,final_grid,final_clicks_grid

def generate_server_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(64)])
    return seed

def generate_client_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(20)])
    return seed

def seed_result_to_string(results:list[list[str]]) -> str:
    final_string:str = ""
    for row in results[:-1]:
        final_string += f"\t\t\t{'|'.join(row)}\n"
    final_string += f"\t\t\t{'|'.join(results[-1])}"
    return final_string

if __name__ == "__main__":
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    server:str = configuration["ServerSeed"]
    server_hashed:str = sha256_encrypt(server)
    client:str = configuration["ClientSeed"]
    nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1)) 
    num_mines:int = configuration["NumberOfMines"]
    prediction_configuration:list[list[int]] = configuration["BoxesToClick"]
    bet_size:float = configuration["BetSize"]
    winning_multiplier:float = mines_multipliers[num_mines][sum(1 for sublist in prediction_configuration for item in sublist if item == 1)-1]

    results:list[str] = []
    current_result:list[int] = []

    biggest_winning_streak:tuple[int,int] = (0,0)
    biggest_losing_streak:tuple[int,int] = (0,0)
    current_winning_streak:int = 0
    current_losing_streak:int = 0
    total_number_of_wins:int = 0
    total_number_of_losses:int = 0
    total_games_played:int = 0
    money_won:float = 0

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        current_winnings,seed_result,clicks_results = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce,num_mines=num_mines,prediction_configuration=prediction_configuration,bet_size=bet_size)
        money_won += current_winnings
        if(current_winnings == 0):
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            current_winning_streak = 0
            current_losing_streak += 1
            total_number_of_losses +=1
        else:
            if(current_losing_streak > biggest_losing_streak[1]):
                biggest_losing_streak = (nonce-current_losing_streak,current_losing_streak)
            current_losing_streak = 0
            current_winning_streak += 1
            total_number_of_wins += 1
        current_result.extend([current_winnings,seed_result_to_string(seed_result),seed_result_to_string(clicks_results)])
        results.append(current_result.copy())
    with open(f"MINES_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w",encoding='utf-8') as file:
        file.write("[\n")
        for result in results:
            file.write("\t{\n")
            file.write(f"""     Server Seed: {result[0]},
        Client Seed: {result[1]},
        Nonce: {result[2]},
        Amount Won: {result[3]},
        Mine Configuration: 
{result[4]}
        Clicks Results:
{result[5]}""")
            file.write("\n\t},\n")
        file.write("]")
            
    # DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Amount Won","Mine Configuration","Clicks Results"]).to_excel(f"MINES_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.xlsx",index=False)
    with open(f"MINES_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""MINES {num_mines} MINES ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Number of mines placed: {num_mines:,.0f}
Number of boxes clicked: {sum(1 for sublist in prediction_configuration for item in sublist if item == 1)}
Winning Multiplier: {winning_multiplier:,.2f}
Gross Winnings on win: ${bet_size*winning_multiplier:,.2f}
Net Profit on Win: ${(bet_size*winning_multiplier)-(bet_size):,.2f}
Number of games simulated: {total_games_played:,.0f}
Number of wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-(bet_size*total_games_played)):,.2f} {"won" if money_won-(bet_size*total_games_played)>0 else "lost"}.""")