import hmac
import hashlib
import random
import string
from math import floor
import json
from pandas import DataFrame

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

if __name__ == "__main__":
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

    biggest_winning_streak:tuple[int,int] = (0,0)
    biggest_losing_streak:tuple[int,int] = (0,0)
    current_winning_streak:int = 0
    current_losing_streak:int = 0
    total_number_of_wins:int = 0
    total_number_of_losses:int = 0
    total_games_played:int = 0
    money_won:float = 0
    nonces_with_result_100000:list[int] = []
    nonces_with_result_10000:list[int] = []
    nonces_with_result_1000:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
        if(seed_result < target_multiplier):
            if(current_winning_streak > biggest_winning_streak[1]):
                biggest_winning_streak = (nonce-current_winning_streak,current_winning_streak)
            current_winning_streak = 0
            current_losing_streak += 1
            total_number_of_losses +=1
            current_result.extend([seed_result,"NO"])
        else:
            if(current_losing_streak > biggest_losing_streak[1]):
                biggest_losing_streak = (nonce-current_losing_streak,current_losing_streak)
            current_losing_streak = 0
            current_winning_streak += 1
            total_number_of_wins += 1
            money_won += (bet_size*target_multiplier)
            current_result.extend([seed_result,"YES"])
        if(seed_result >= 100000):
            nonces_with_result_100000.append(f"{nonce:,.0f}")
        elif(seed_result >= 10000):
            nonces_with_result_10000.append(f"{nonce:,.0f}")
        elif(seed_result >= 1000):
            nonces_with_result_1000.append(f"{nonce:,.0f}")
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Win"]).to_csv(f"LIMBO_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    with open(f"LIMBO_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""LIMBO TARGET MULTIPLIER {target_multiplier:,.2f} ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Target Multiplier: {target_multiplier:,.2f}
Win Chance: {win_chance:.7f}%
Bet Size: ${bet_size:,.2f}
Gross Gain on Win: ${bet_size*target_multiplier:,.2f}
Net Gain on Win: ${(bet_size*target_multiplier)-(bet_size):,.2f}
Number of games simulated: {total_games_played:,.0f}
Number of wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-(bet_size*total_games_played)):,.2f} {"won" if money_won-(bet_size*total_games_played)>0 else "lost"}.
Number of 100,000x+ rolls: {len(nonces_with_result_100000):,.0f}
Number of 10,000x+ rolls: {len(nonces_with_result_10000):,.0f}
Number of 1,000x+ rolls: {len(nonces_with_result_1000):,.0f}""")