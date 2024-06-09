import csv
from web3 import Web3
import math
from collections import defaultdict
import json

total_token_testnet  = 20000000 #  5% of total supply
total_token_loopring = 40000000 # 10% of total supply

w3 = Web3()

def read_csv(file_path, address_index, value_index, value_type, score_func=None):
    """
    Read a CSV file and return a dictionary where the keys are addresses and the values are scores.
    """
    data_dict = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            address = w3.to_checksum_address(row[address_index])
            value = value_type(row[value_index])
            score = score_func(value) if score_func else value
            if address in data_dict:
                data_dict[address] += score
            else:
                data_dict[address] = score
    return data_dict

def exclude_team_addresses(data_dict, team_addresses):
    """
    Exclude team addresses from the data dictionary.
    """
    return {address: score for address, score in data_dict.items() if address not in team_addresses}

def add_to_address_dict(address_dict, data_dict):
    """
    Add the scores from the data dictionary to the address dictionary.
    """
    for address, score in data_dict.items():
        if address not in address_dict:
            address_dict[address] = 0
        address_dict[address] += score

# Initialize the set of team addresses
team_addresses = set(read_csv('./snapshot/testnet/address_to_exclude.list', 0, 0, str).keys())

# Read the data files
bribe = read_csv('./snapshot/testnet/bribe.list', 0, 1, int, lambda x: 1)
balance = read_csv('./snapshot/testnet/veKDO_balance.list', 0, 1, float, lambda x: math.floor(max(0, math.log(max(x, 1e-10)) / 2)))
stake = read_csv('./snapshot/testnet/stake.list', 0, 1, float, lambda x: 1)
vote = read_csv('./snapshot/testnet/vote.list', 0, 2, float, lambda x: x)
reward = read_csv('./snapshot/testnet/emission_reward.list', 0, 1, float, lambda x: 1)
galxe = read_csv('./snapshot/testnet/galxe_leaderboard.csv', 0, 2, float, lambda x: int(x / 50) + 1)
loopring = read_csv('./snapshot/loopring/transfer.csv', 2, 3, float, lambda x: int( x * 16)) # factor: 40000000(kodo) / 2500000(loopring's taiko airdrop) = 16

# Exclude team addresses
bribe = exclude_team_addresses(bribe, team_addresses)
balance = exclude_team_addresses(balance, team_addresses)
stake = exclude_team_addresses(stake, team_addresses)
vote = exclude_team_addresses(vote, team_addresses)
reward = exclude_team_addresses(reward, team_addresses)
galxe = exclude_team_addresses(galxe, team_addresses)
loopring = exclude_team_addresses(loopring, team_addresses)

# Initialize the address dictionary
address_dict_testnet = {}

# Add the scores to the address dictionary
add_to_address_dict(address_dict_testnet, bribe)
add_to_address_dict(address_dict_testnet, balance)
add_to_address_dict(address_dict_testnet, stake)
add_to_address_dict(address_dict_testnet, vote)
add_to_address_dict(address_dict_testnet, reward)
add_to_address_dict(address_dict_testnet, galxe)

# Calculate the total sum of the scores
total_sum_testnet = sum(address_dict_testnet.values())

# Calculate the proportion of each score and distribute the total token accordingly
distributed_dict_testnet = {address: (score / total_sum_testnet) * total_token_testnet for address, score in address_dict_testnet.items()}

# Initialize a defaultdict with int
merged_dict = defaultdict(int)

# Add the scores from the testnet dictionary
for address, score in distributed_dict_testnet.items():
    merged_dict[address] += score

# Add the scores from the loopring dictionary
for address, score in loopring.items():
    merged_dict[address] += score

# Convert the defaultdict back to a regular dict
merged_dict = {address: int(score) for address, score in merged_dict.items() if int(score) > 0}

# Sort the distributed dictionary by its values in descending order
sorted_distributed_dict = sorted(merged_dict.items(), key=lambda item: item[1], reverse=True)

# # Print the sorted dictionary
# for item in sorted_distributed_dict:
#     print(f"{item[0]}: {item[1]}")

# Create the final dictionary
final_dict = {
    "decimals": 18,
    "airdrop": dict(sorted_distributed_dict)
}

json_str = json.dumps(final_dict, indent=2)

# print(json_str)

with open('config.json', 'w') as file:
    file.write(json_str)
