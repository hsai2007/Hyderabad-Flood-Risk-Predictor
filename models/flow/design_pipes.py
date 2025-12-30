import pandas as pd
import numpy as np
from scipy.optimize import fsolve

n = 0.013   # concrete roughness

pipes = pd.read_csv("data/pipe_flows.csv")
edges = pd.read_csv("data/drain_edges_with_slope.csv")

# Join slope
pipes = pipes.merge(edges, on=["from","to"])

def manning_Q(D, S):
    A = np.pi * (D/2)**2
    R = D / 4
    return (1/n) * A * (R**(2/3)) * (S**0.5)

def solve_D(Q, S):
    if Q < 0.001:
        return 0.1
    f = lambda D: manning_Q(D, S) - Q
    return fsolve(f, 1.0)[0]

pipes["required_diameter_m"] = pipes.apply(
    lambda r: solve_D(r["flow_m3s"], r["slope"]),
    axis=1
)

pipes.to_csv("data/drain_design.csv", index=False)

print("[SUCCESS] Hydraulically correct drain sizes computed")
print(pipes[["from","to","flow_m3s","required_diameter_m"]].head())
