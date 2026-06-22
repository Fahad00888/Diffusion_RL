import os, sys
sys.path.append(os.getcwd())
import datasets.collect_demonstrations_balance_game as col

# The function uses a module-level `map_num` that's normally set in __main__.
# Since we call the function directly, define it ourselves:
col.map_num = 0

col.collect_waypoints(
    epsilon=0,
    num_runs=3,                # tiny smoke test
    starting_seed=0,
    random_cameras=False,
    folder_name="balance_game_test",
    heuristic_type="RRTStarOnly",
    blue_type="heuristic",
    env_path="simulator/configs/balance_game.yaml",
    show=False,
)
print("SMOKE TEST DONE")
