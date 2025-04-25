import hmac
import hashlib
import random
import string
from math import floor
import json
from pandas import DataFrame
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

if __name__ == "__main__":
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

    server:str = configuration["ServerSeed"]
    server_hashed:str = sha256_encrypt(server)
    client:str = configuration["ClientSeed"]
    nonces:list[int] = list(range(configuration["MinimumNonce"],configuration["MaximumNonce"]+1))
    over_under:str = configuration["OverUnder"]
    threshold:float = round(configuration["Threshold"],2)
    win_chance:float = round(configuration["WinChance"],2)
    bet_size:float = configuration["BetSize"]

    if(confirm_threshold_with_win_chance(over_under=over_under, threshold=threshold, win_chance=win_chance)):
        pass
    else:
        if(over_under == "Over"):
            threshold = 100-win_chance
        else:
            threshold = win_chance

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
    nonces_with_perfect_rolls:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
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
            money_won += (bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")])
            current_result.extend([seed_result,"YES"])
        if(
            (
                (seed_result > 99.99)and
                (over_under == "Over")
            )
            or
            (
                (seed_result < 0.01)and
                (over_under == "Under")
            )
          ):
            nonces_with_perfect_rolls.append(f"{nonce:,.0f}")
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Win"]).to_csv(f"DICE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    with open(f"DICE_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""DICE {over_under.upper()} {threshold} ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Bet Size: ${bet_size:,.2f}
Winning Multiplier: {dice_multipliers[over_under][float(f"{threshold:.2f}")]:,.4f}
Net Profit per Win: ${bet_size*dice_multipliers[over_under][float(f"{threshold:.2f}")] - bet_size:,.2f}
Number of games simulated: {total_games_played:,.0f}
Number of wins: {total_number_of_wins:,.0f}
Number of Losses: {total_number_of_losses:,.0f}
Biggest Winning Streak: {biggest_winning_streak[1]:,.0f}
Starting Nonce of Biggest Winning Streak: {biggest_winning_streak[0]:,.0f}
Biggest Losing Streak: {biggest_losing_streak[1]:,.0f}
Starting Nonce of Biggest Losing Streak: {biggest_losing_streak[0]:,.0f}
With ${bet_size:,.2f} bets, gross winnings: ${money_won:,.2f}
With ${bet_size:,.2f} bets, net result: ${abs(money_won-(bet_size*total_games_played)):,.2f} {"won" if money_won-(bet_size*total_games_played)>0 else "lost"}.
Number of perfect {100 if over_under=="Over" else 0} rolls: {len(nonces_with_perfect_rolls):,.0f}""")