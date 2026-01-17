import yaml
import numpy as np
import pandas as pd

with open("generator_config.yaml", "r") as f:
    config = yaml.safe_load(f)

np.random.seed(config["random_seed"])
N = config["num_samples"]

def clip(arr, min_v, max_v):
    return np.clip(arr, min_v, max_v)

salary = clip(
    np.random.lognormal(
        mean=config["salary"]["mean"],
        sigma=config["salary"]["sigma"],
        size=N
    ),
    config["salary"]["min"],
    config["salary"]["max"]
).astype(int)

credit_score = clip(
    np.random.normal(
        loc=config["credit_score"]["mean"],
        scale=config["credit_score"]["std"],
        size=N
    ),
    config["credit_score"]["min"],
    config["credit_score"]["max"]
).astype(int)

employment_years = clip(
    np.random.uniform(
        low=config["employment_years"]["min"],
        high=config["employment_years"]["max"],
        size=N
    ),
    config["employment_years"]["min"],
    config["employment_years"]["max"]
).astype(int)

loan_amount = clip(
    np.random.lognormal(
        mean=config["loan_amount"]["mean"],
        sigma=config["loan_amount"]["sigma"],
        size=N
    ),
    config["loan_amount"]["min"],
    config["loan_amount"]["max"]
).astype(int)

# Simple approval logic (rule-based proxy)
approval = (
    (credit_score >= config["approval_rule"]["credit_score_threshold"]) &
    (loan_amount < salary * config["approval_rule"]["dti_proxy_threshold"])
).astype(int)


df = pd.DataFrame({
    "salary": salary,
    "credit_score": credit_score,
    "employment_years": employment_years,
    "loan_amount": loan_amount,
    "target": approval,
    "source": "SYNTHETIC_GENERATED"
})

df.to_csv("training_data.csv", index=False)

print(f"Generated {len(df)} synthetic borrower records.")