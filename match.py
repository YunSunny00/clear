import pandas as pd
import random
from collections import defaultdict

db = pd.read_csv('db.csv')
user = pd.read_csv('user.csv')

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

def create_balanced_matches(group):
    players = group['name'].tolist()
    n_players = len(players)
    total_slots = 8 * 4 # 8 games, 4 players each

    base_count = total_slots // n_players
    extra_slots = total_slots % n_players
    participation_targets = [base_count] * n_players
    for i in range(extra_slots):
        participation_targets[i] += 1

    player_target = {player: participation_targets[i] for i, player in enumerate(players)}
    participation_counts = {p: 0 for p in players}
    player_streak = {p: 0 for p in players}
    pair_counts = defaultdict(int)  # (A, B): number of times played together

    used_teams = set()
    used_opponents = set()
    matches = []

    remaining_slots = total_slots
    while remaining_slots > 0:
        num_players_in_game = min(4, remaining_slots)

        eligible_players = [
            p for p in players
            if participation_counts[p] < player_target[p] and player_streak[p] < 2
        ]
        if len(eligible_players) < num_players_in_game:
            eligible_players = [
                p for p in players if participation_counts[p] < player_target[p]
            ]
        if len(eligible_players) < num_players_in_game:
            eligible_players = players 

        best_selection = None
        min_pair_score = float('inf')

        for _ in range(50):
            try_sample = random.sample(eligible_players, num_players_in_game)

            if num_players_in_game == 4:
                team1 = tuple((try_sample[:2]))
                team2 = tuple((try_sample[2:]))

                pair_score = (
                    pair_counts[tuple(((team1[0], team1[1])))] +
                    pair_counts[tuple(((team2[0], team2[1])))]
                )

                if (team1, team2) in used_opponents or team1 == team2:
                    continue

                if pair_score < min_pair_score:
                    best_selection = try_sample
                    min_pair_score = pair_score

            else:
                best_selection = try_sample
                break

        if best_selection is None:
            best_selection = random.sample(eligible_players, num_players_in_game)

        selected = best_selection
        if num_players_in_game == 4:
            team1 = tuple((selected[:2]))
            team2 = tuple((selected[2:]))
            matches.append((list(team1), list(team2)))
            used_teams.add(team1)
            used_teams.add(team2)
            used_opponents.add((team1, team2))
            pair_counts[tuple(((team1[0], team1[1])))] += 1
            pair_counts[tuple(((team2[0], team2[1])))] += 1
        else:
            matches.append((list(selected), []))
        for p in players:
            if p in selected:
                participation_counts[p] += 1
                player_streak[p] += 1
            else:
                player_streak[p] = 0
        remaining_slots -= num_players_in_game

    return matches

group_matches = {}
group_members = {}
for idx, group in enumerate(groups, start=1):
    matches = create_balanced_matches(group)
    group_name = f'Group {idx}'
    group_matches[group_name] = matches
    group_members[group_name] = group['name'].tolist()

with pd.ExcelWriter('matching_results.xlsx') as writer:
    summary_data = []
    for group, members in group_members.items():
        summary_data.append({
            'Group': group,
            'Number of Members': len(members),
            'Members': ', '.join(members)
        })
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

    # Each group in its own sheet
    for group, matches in group_matches.items():
        match_data = []
        for i, match in enumerate(matches, 1):
            team1 = ', '.join(match[0])
            team2 = ', '.join(match[1])
            match_data.append({
                'Game': i,
                'Team 1': team1,
                'Team 2': team2
            })
            # print
            print(f"{group} - Game {i}: {team1} vs {team2}")
        match_df = pd.DataFrame(match_data)
        sheet_name = group[:31]
        match_df.to_excel(writer, sheet_name=sheet_name, index=False)
