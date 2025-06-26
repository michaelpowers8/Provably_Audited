import os
import hmac
import hashlib
import random
import string
from math import floor
import json
from pandas import DataFrame
from Multipliers import plinko_multipliers

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
    number = number*multiplier
    return floor(number)

def seeds_to_results(server_seed:str,client_seed:str,nonce:int,risk:str,rows:int) -> tuple[int,int|float]:
    hexs = seeds_to_hexadecimals(server_seed=server_seed,client_seed=client_seed,nonce=nonce)
    bytes_lists:list[list[int]] = [hexadecimal_to_bytes(current_hex) for current_hex in hexs]
    row:list[list[int]] = []
    for bytes_list in bytes_lists:
        for index in range(0,len(bytes_list),4):
            row.append(bytes_to_number(bytes_list[index:index+4],2))
            if(len(row)==rows):
                return [sum(row),plinko_multipliers[f"{risk}{rows}"][sum(row)]]

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
    risk:str = configuration["Risk"]
    num_rows:int = configuration["Rows"]
    bet_size:float = configuration["BetSize"]

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
    nonces_with_largest_prize:list[int] = []
    nonces_with_second_largest_prize:list[int] = []
    nonces_with_third_largest_prize:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce,risk=risk,rows=num_rows)
        money_won += (bet_size*seed_result[1])
        if(seed_result[1] < 1):
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
        if(seed_result[0] in [0,num_rows+1]):
            nonces_with_largest_prize.append(f"{nonce:,.0f}")
        elif(seed_result[0] in [1,num_rows]):
            nonces_with_second_largest_prize.append(f"{nonce:,.0f}")
        elif(seed_result[0] in [2,num_rows-1]):
            nonces_with_third_largest_prize.append(f"{nonce:,.0f}")
        current_result.extend(seed_result)
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Prize Index","Multiplier"]).to_csv(f"PLINKO_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    with open(f"PLINKO_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""PLINKO BALL {risk.upper()} RISK {num_rows} ROWS ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Number of games simulated: {total_games_played:,.0f}
Number of Wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-(bet_size*total_games_played)):,.2f} {"won" if money_won-(bet_size*total_games_played)>0 else "lost"}.
Number of {plinko_multipliers[f"{risk}{num_rows}"][0]}x multipliers: {len(nonces_with_largest_prize):,.0f}
Nonces with {plinko_multipliers[f"{risk}{num_rows}"][0]}x multipliers: {"|".join(nonces_with_largest_prize)}
Number of {plinko_multipliers[f"{risk}{num_rows}"][1]}x multipliers: {len(nonces_with_second_largest_prize):,.0f}
Nonces with {plinko_multipliers[f"{risk}{num_rows}"][1]}x multipliers: {"|".join(nonces_with_second_largest_prize)}
Number of {plinko_multipliers[f"{risk}{num_rows}"][2]}x multipliers: {len(nonces_with_third_largest_prize):,.0f}
Nonces with {plinko_multipliers[f"{risk}{num_rows}"][2]}x multipliers: {"|".join(nonces_with_third_largest_prize)}""")
