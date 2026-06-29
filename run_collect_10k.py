import os, sys, glob, argparse
sys.path.append(os.getcwd())
import datasets.collect_demonstrations_balance_game as col
col.map_num = 0
OUT = "datasets/balance_game/gnn_map_0_run_10000_RRTStarOnly"
def done(seed):
    return len(glob.glob(os.path.join(OUT, f"seed_{seed}_known_*.npz"))) > 0
ap = argparse.ArgumentParser()
ap.add_argument("--start", type=int, required=True)
ap.add_argument("--end", type=int, required=True)
a = ap.parse_args()
os.makedirs(OUT, exist_ok=True)
for seed in range(a.start, a.end):
    if done(seed):
        continue
    col.collect_waypoints(0, 10000, seed, False, "balance_game",
                          "RRTStarOnly", "heuristic",
                          "simulator/configs/balance_game.yaml",
                          show=False, loop_runs=1)
print(f"WORKER DONE [{a.start},{a.end})")
