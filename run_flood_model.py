import os

os.system("python scripts/fetch_historical_rainfall.py")
os.system("python models/evt/extract_extremes.py")
os.system("python models/evt/gumbel_fit.py")
os.system("python models/evt/return_levels.py")
os.system("python models/flow/node_runoff.py")
os.system("python models/flow/accumulate_flow.py")
os.system("python models/flow/compute_slope.py")
os.system("python models/flow/design_pipes.py")
os.system("python models/clogging/p_clog_model.py")
os.system("python models/clogging/map_floods.py")

print("\n[FULL FLOOD SIMULATION COMPLETE]")
