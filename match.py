import pandas as pd
import random
import itertools
import argparse

args = argparse.ArgumentParser()
args.add_argument('--user', type=str, default='user.csv', help='Participants CSV file path')
args = args.parse_args()
part_path = args.user

db = pd.read_csv('db.csv')
user = pd.read_csv(part_path)

participants = user.iloc[:, 0].tolist()

filtered_db = db[db['name'].isin(participants)].copy()

filtered_db['rating'] = filtered_db['rating'].astype(int)

# rating sorting
filtered_db = filtered_db.sort_values(by='rating', ascending=False).reset_index(drop=True)

print(filtered_db)

def make_groups(df, min_size=6, max_size=8):
    total = len(df)
    for num_groups in range(total // max_size, total // min_size + 1):
        if num_groups == 0:
            continue
        avg = total / num_groups
        if min_size <= avg <= max_size:
            break
    else:
        raise ValueError("Cannot make groups evenly")
    
    group_sizes = [total // num_groups] * num_groups
    for i in range(total % num_groups):
        group_sizes[i] += 1

    groups = []
    idx = 0
    for size in group_sizes:
        groups.append(df.iloc[idx:idx+size].reset_index(drop=True))
        idx += size
    return groups

groups = make_groups(filtered_db)

def create_unique_matches(group, num_games=8):
    players = group['name'].tolist()
    all_pairs = list(itertools.combinations(players, 2))
    random.shuffle(all_pairs)
    
    used_pairs = set()
    matches = []
    
    for _ in range(num_games):
        valid_found = False
        attempts = 0
        
        while not valid_found and attempts < 1000:
            selected = random.sample(players, 4)
            team1 = tuple(sorted(selected[:2]))
            team2 = tuple(sorted(selected[2:]))
            if team1 not in used_pairs and team2 not in used_pairs and team1 != team2:
                used_pairs.add(team1)
                used_pairs.add(team2)
                matches.append((list(team1), list(team2)))
                valid_found = True
            attempts += 1
        
        if not valid_found:
            selected = random.sample(players, 4)
            matches.append((selected[:2], selected[2:]))
            
    return matches

group_matches = {}
group_members = {}
for idx, group in enumerate(groups, start=1):
    matches = create_unique_matches(group)
    group_name = f'Group {idx}'
    group_matches[group_name] = matches
    group_members[group_name] = group['name'].tolist()

for group, members in group_members.items():
    print(f"=== {group} ===")
    print(f"Members ({len(members)}명): {members}")
    print("Games:")
    for i, match in enumerate(group_matches[group], 1):
        print(f"  Game {i}: {match[0]} vs {match[1]}")
    print()
