import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def train_regression_model(X, y, test_size=0.2, random_state=42):
    """
    Train a gradient boosting regression model for energy forecasting.
    
    Parameters:
    -----------
    X : pd.DataFrame
        Features
    y : pd.Series
        Target variable
    test_size : float
        Proportion of dataset to use as test set
    random_state : int
        Random seed for reproducibility
    
    Returns:
    --------
    model : GradientBoostingRegressor
        Trained model
    metrics : dict
        Performance metrics on test set
    X_train, X_test, y_train, y_test : splits for further analysis
    """
    # Split data (no shuffle for time series)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, shuffle=False
    )
    # Initialize model
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=random_state,
        verbose=1
    )
    
    # Train model
    print(f"\n{'='*50}")
    print(f"TRAINING MODEL")
    print(f"{'='*50}")
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'train': {
            'mae': mean_absolute_error(y_train, y_pred_train),
            'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'r2': r2_score(y_train, y_pred_train)
        },
        'test': {
            'mae': mean_absolute_error(y_test, y_pred_test),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'r2': r2_score(y_test, y_pred_test)
        }
    }
    
    return model, metrics, X_train, X_test, y_train, y_test

# Example usage:
if __name__ == "__main__":
    # Prepare training data
    X, y, df = prepare_training_data('solar_energy_data.csv')
    
    # Train model
    model, metrics, X_train, X_test, y_train, y_test = train_regression_model(X, y)
    
    # Save model (optional)
    import joblib
    joblib.dump(model, 'energy_forecast_model.pkl')
    print(f"\n{'='*50}")
    print("Model saved to 'energy_forecast_model.pkl'")
    print(f"{'='*50}")