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
            row.append(bytes_to_number(bytes_list[index:index+4],37))
            if(len(row)==1):
                return row[0]

if __name__ == "__main__":
    with open("Configuration.json","rb") as file:
        configuration:dict[str,str|int] = json.load(file)

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
    num_black:int = 0

    num_single_number_bets_hit:int = 0

    nonces_with_result_0:list[int] = []

    for nonce in nonces:
        total_games_played += 1
        current_result = [server,client,nonce]
        seed_result = seeds_to_results(server_seed=server,client_seed=client,nonce=nonce)
        
        round_winnings:float = 0
        round_bettings:float = 0
        round_bettings += sum(list(single_number_bets.values()))
        round_bettings += sum(list(vertical_column_bets.values()))
        round_bettings += sum(list(dozen_bets.values()))
        round_bettings += sum(list(one_to_one_bets.values()))
        total_money_bet += round_bettings

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
        elif(roulette_numbers_colors[str(seed_result)]=="Red"):
            num_red += 1
        
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

        current_result.extend([seed_result,round_bettings,round_winnings,roulette_numbers_colors[str(seed_result)]])
        results.append(current_result)
    DataFrame(results,columns=["Server Seed","Client Seed","Nonce","Result","Total Wager (Round)","Gross Winnings (Round)","Color"]).to_csv(f"ROULETTE_RESULTS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.csv",index=False)
    with open(f"ROULETTE_RESULTS_ANALYSIS_{server}_{client}_{nonces[0]}_to_{nonces[-1]}.txt","w") as file:
        file.write(f"""ROULETTE ANALYSIS
Server Seed: {server}
Server Seed (Hashed): {server_hashed}
Client Seed: {client}
Nonces: {nonces[0]:,.0f} - {nonces[-1]:,.0f}
Total Games Played: {total_games_played:,.0f}
Total Money Wagered: ${total_money_bet:,.2f}
Gross Winnings: ${money_won:,.2f}
Net Winnings: ${abs(total_money_bet-money_won):,.2f} {"won" if money_won-total_money_bet>0 else "lost"}
Return to Player (RTP): {round((money_won/total_money_bet)*100,2)}%
Number of Wins: {total_number_of_wins:,.0f}
Number of Partial Losses: {num_games_without_total_loss:,.0f}
Number of Total Losses: {num_games_with_total_loss:,.0f}
Number of Single Bets Won: {num_single_number_bets_hit:,.0f}
Number of Black: {num_black:,.0f}
Number of Red: {num_red:,.0f}
Number of Even: {num_evens:,.0f}
Number of Odds: {num_odds:,.0f}
Number of 1-18: {num_1_to_18:,.0f}
Number of 19-36: {num_19_to_36:,.0f}
Number of 1-12: {num_1_to_12:,.0f}
Number of 13-24: {num_13_to_24:,.0f}
Number of 25-36: {num_25_to_36:,.0f}
Number of Vertical Column 1: {num_column_1:,.0f}
Number of Vertical Column 2: {num_column_2:,.0f}
Number of Vertical Column 3: {num_column_3:,.0f}
Number of 0's: {len(nonces_with_result_0):,.0f}
Nonces Resulting in 0: {"|".join(nonces_with_result_0)}""")