import os
import hmac
import hashlib
import random
import string
from math import floor
import json
from Multipliers import pump_multipliers
from pandas import DataFrame

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

def seeds_to_results(server_seed:str,client_seed:str,nonce:int,difficulty:str) -> list[list[str]]:
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
        final_shuffle.append(shuffle[number]+1)
        shuffle.remove(shuffle[number])
    final_shuffle.append(shuffle[0])
    if(difficulty=="Easy"):
        return min(final_shuffle[:1])-1
    if(difficulty=="Medium"):
        return min(final_shuffle[:3])-1
    if(difficulty=="Hard"):
        return min(final_shuffle[:5])-1
    if(difficulty=="Expert"):
        return min(final_shuffle[:10])-1

def calculate_winnings(bet:float,num_pumps:int,result:int,difficulty:str):
    if(num_pumps>pump_multipliers[difficulty].index(pump_multipliers[difficulty][result-1])):
        return 0
    return bet*pump_multipliers[difficulty][num_pumps]

def generate_server_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(64)])
    return seed

def generate_client_seed():
    possible_characters:str = string.hexdigits
    seed:str = "".join([random.choice(possible_characters) for _ in range(20)])
    return seed

if __name__ == "__main__":
    # Get the path to the folder this script is in
    BASE_DIR:str = os.path.dirname(os.path.abspath(__file__))

    # Safely construct the full path to Configuration.json
    config_path:str = os.path.join(BASE_DIR, "Configuration.json")
    with open(config_path,"rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    server:str = configuration["ServerSeed"]
    server_hashed:str = sha256_encrypt(server)
    client:str = configuration["ClientSeed"]
    nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
    difficulty:str = configuration["Difficulty"]
    num_pumps:int = configuration["NumberOfPumps"]
    bet_size:float = configuration["BetSize"]
    if(num_pumps < 1):
        num_pumps = 1
    elif(num_pumps >= len(pump_multipliers[difficulty])):
        num_pumps = len(pump_multipliers[difficulty])-1

    results:list[list[float|int]] = []
    current_result:list[int] = []

    biggest_winning_streak:tuple[int,int] = (0,0)
    biggest_losing_streak:tuple[int,int] = (0,0)
    current_winning_streak:int = 0
    current_losing_streak:int = 0
    total_number_of_wins:int = 0
    total_number_of_losses:int = 0
    total_games_played:int = 0
    money_won:float = 0
    nonces_with_max_multiplier:list[int] = []
    nonces_with_second_biggest_multiplier:list[int] = []
    nonces_with_third_largest_multiplier:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce,difficulty=difficulty)
        current_winnings:float = calculate_winnings(bet_size,num_pumps,seed_result,difficulty)
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
        if(seed_result == (len(pump_multipliers[difficulty]))):
            nonces_with_max_multiplier.append(f"{nonce:,.0f}")
        elif(seed_result == (len(pump_multipliers[difficulty])-1)):
            nonces_with_second_biggest_multiplier.append(f"{nonce:,.0f}")
        elif(seed_result == (len(pump_multipliers[difficulty])-2)):
            nonces_with_third_largest_multiplier.append(f"{nonce:,.0f}")
        current_result.extend([f"{pump_multipliers[difficulty][seed_result]:,.2f}",f"${current_winnings:,.2f}"])
        results.append(current_result)

    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Max Result","Amount Won"]).to_csv(f"PUMP_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    with open(f"PUMP_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""PUMP {difficulty} DIFFICULTY {num_pumps} PUMPS ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Bet Size: {bet_size:,.2f}
Difficulty: {difficulty}
Number of Pumps Attempted per Game: {num_pumps}
Winning Multiplier: {pump_multipliers[difficulty][num_pumps]:,.2f}
Gross Gain on Win: {(bet_size*pump_multipliers[difficulty][num_pumps]):,.2f}
Net Gain on Win: {((bet_size*pump_multipliers[difficulty][num_pumps])-(bet_size)):,.2f}
Number of games simulated: {total_games_played:,.0f}
Number of wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-(bet_size*total_games_played)):,.2f} {"won" if money_won-(bet_size*total_games_played)>0 else "lost"}.
Number of {pump_multipliers[difficulty][-1]:,.2f}x multipliers: {len(nonces_with_max_multiplier):,.0f}
Nonces with {pump_multipliers[difficulty][-1]:,.2f}x multipliers: {"|".join(nonces_with_max_multiplier)}
Number of {pump_multipliers[difficulty][-2]:,.2f}x multipliers: {len(nonces_with_second_biggest_multiplier):,.0f}
Nonces with {pump_multipliers[difficulty][-2]:,.2f}x multipliers: {"|".join(nonces_with_second_biggest_multiplier)}
Number of {pump_multipliers[difficulty][-3]:,.2f}x multipliers: {len(nonces_with_third_largest_multiplier):,.0f}
Nonces with {pump_multipliers[difficulty][-3]:,.2f}x multipliers: {"|".join(nonces_with_third_largest_multiplier)}""")