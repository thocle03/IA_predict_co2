import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_and_optimize():
    print("Loading dataset...")
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run extract_features.py first.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Loaded {len(df)} samples.")
    
    # Features (X) and Target (y)
    # X: Graph topology metrics
    feature_cols = ['n_nodes', 'n_edges', 'density', 'spectral_radius', 'kreiss_constant']
    # y: Pollution (Total CO2)
    target_col = 'total_co2_kg'
    
    X = df[feature_cols]
    y = df[target_col]
    
    print("Features:", feature_cols)
    print("Target:", target_col)
    
    # Split (Very small dataset, so we use Leave-One-Out or simple Train/Test with high ratio)
    # For 5 samples, standard splitting is shaky, but we implement the logic for N > 50.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Pipeline: Scale features -> Neural Net
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('mlp', MLPRegressor(max_iter=2000, random_state=42))
    ])
    
    # Hyperparameter Optimization (Grid Search)
    # Finding "Optimal Parameters" as requested
    param_grid = {
        'mlp__hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
        'mlp__activation': ['relu', 'tanh'],
        'mlp__learning_rate_init': [0.001, 0.01],
        'mlp__alpha': [0.0001, 0.001] # Regularization
    }
    
    print("Starting Grid Search for Optimal Parameters...")
    grid = GridSearchCV(pipeline, param_grid, cv=2, verbose=1, scoring='r2') # cv=2 because min samples=5
    grid.fit(X, y) # Fit on all data for this PoC
    
    print("\nBest Parameters found:")
    print(grid.best_params_)
    print(f"Best Score (R2): {grid.best_score_:.4f}")
    
    # Save Best Model
    best_model = grid.best_estimator_
    model_path = os.path.join(MODEL_DIR, "pollution_predictor_v1.pkl")
    joblib.dump(best_model, model_path)
    print(f"Model saved to {model_path}")
    
    # Generate "Optimal Parameters" Report
    with open(os.path.join(MODEL_DIR, "optimal_params.txt"), "w") as f:
        f.write("Optimal Hyperparameters found via GridSearch:\n")
        for k, v in grid.best_params_.items():
            f.write(f"{k}: {v}\n")
        f.write(f"\nBest Cross-Validation R2 Score: {grid.best_score_:.4f}")

if __name__ == "__main__":
    train_and_optimize()
