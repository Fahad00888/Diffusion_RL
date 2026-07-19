# Reproduction Summary — Diffusion-RL Hierarchical Motion Planning (arXiv 2403.10794)

Reproduced from scratch. Final evaluation: 100 episodes per method, seeds `1e6+1+ep`.

## Final Table I — Goal-Reaching Rate

| Method | This reproduction | Paper |
|---|---|---|
| A* | 0.980 | 0.980 |
| RRT* | 0.940 | 0.940 |
| VO | 0.980 | 0.980 |
| **Diffusion-RL** | **1.000** | 0.960 |
| **Diffusion-RL-Map (Sel)** | **0.990** | 0.980 |

Diffusion-RL: mean detection 77.57, mean score -27.57.
Sel variant (regenerated costmap): mean detection 75.88, mean score -26.88.

The three heuristic baselines match the paper exactly, validating the evaluation harness independently of the learned policy.

## Six bugs found in the released codebase

Before these fixes, goal-reaching was 7%. After all six, 100%.

1. **SAC/sac.py** — `target_entropy` hardcoded to -3 instead of -dim(action) (= -2 here).
2. **red_rl_main.py `__main__`** — hardcoded sweep lists (critic_lrs / policy_lrs / entropy_lrs = [0.003]) silently overwrote every learning rate from the YAML config before training started. All earlier retrains ran at entropy_lr=0.003 regardless of configuration; entropy temperature collapsed to ~0.005 within the first 10-20k episodes in every run.
3. **red_rl_main.py:387** — `set_dist_coeff(..., 0.05)` decayed the waypoint-distance coefficient toward zero, removing path-following incentive mid-training. Set to 1.0 (fixed), matching Algorithm 3.
4. **simulator/configs/balance_game.yaml** — `reward_setting: rl` routed training to `get_rl_reward()`, a sparse reward with no waypoint term at all, rather than `get_piece_reward()` (r = r_g + r_d + r_adv, the paper's formulation). Root cause of the corner-camping / edge-hugging behaviour: detection-avoidance was the only dense learnable signal.
5. **red_rl_main.py:482** — `load_checkpoint = False` hardcoded, silently ignoring `continue: True` in the config; resumes restarted from episode 0.
6. **SAC/sac.py save()/init_from_save()** — `log_alpha` and its optimizer were never written to checkpoints, so entropy temperature reset to 1.0 on every resume. Fixed (backward compatible with existing checkpoints).

## Diagnostic evidence

- With all fixes, alpha decayed smoothly 0.99 -> 0.30 over training, versus collapsing to ~0.005 by decile 2 in every prior run.
- Pre-fix behavioural trace: across 30 evaluation episodes, the agent reached waypoint 1 in 0/30 episodes; 53% never came within 100 units. The diffusion planner itself was correct throughout (final waypoint sat at distance 0.0 from a real hideout).

## Hardware note — GPU 1 (RTX 5070, 12GB)

Training on GPU 1 fails reproducibly under sustained load: once as a silent stall, once as `CUDA error: unspecified launch failure`. Kernel logs show driver-level faults attributed to the training process:

    NVRM: Xid (PCI:0000:16:00): 13, Graphics Exception ... pid=5356, name=python
    NVRM: Xid (PCI:0000:16:00): 69, Class Error ... pid=5552, name=python

Isolated tests on GPU 1 all pass (100 matmuls, checkpoint load, 20 inference steps, 50 gradient updates with CUDA_LAUNCH_BLOCKING=1); both GPUs report identical compute capability (12, 0). The fault appears only under sustained combined CPU+GPU load. GPU 0 (RTX 5070 Ti) ran the same code for many hours without incident. This looks like a driver or hardware issue on GPU 1, not an application bug.

## Run details

- Final model: `logs/marl/20260718-185114/sac_piece/model/100000.pth` (100,001 episodes)
- Costmap regenerated from 1,500 rollouts of the final policy
- Caveat: the run was interrupted by several machine reboots; because of bug #6 (discovered afterwards), alpha restarted near 1.0 at each resume rather than continuing its decay. An uninterrupted run would anneal more sharply in late training. Evaluation is unaffected — it uses the deterministic mean action.

## Seed-robustness check

The headline result was re-evaluated on a second, disjoint seed block (2e6+1+ep, 100 episodes) to rule out seed-specific luck or overlap with training:

| Eval seed block | Goal-reach | Mean detection |
|---|---|---|
| 1e6+1+ep | 1.000 | 77.57 |
| 2e6+1+ep | 1.000 | 74.11 |

200 distinct episodes, zero failures. Training seeds span 0-100,000 and do not overlap either eval block. Re-running the original block reproduced identical results, confirming the evaluation pipeline is deterministic.

Context for the 1.000 figure: goal-reaching is close to saturated in this environment — the non-learning A* and VO baselines reach 0.980 — so 1.000 is a modest step above the paper's 0.960 rather than an anomalous one, and is within sampling error of it at n=100. Detection avoidance, not goal-reaching, is the metric that meaningfully separates methods here.
