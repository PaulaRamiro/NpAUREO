# Load libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import RobustScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import RFE
import category_encoders as ce
import matplotlib.pyplot as plt

# Load your dataset
data = pd.read_csv("manuallycuratedlogsizeupto100onlylog.csv", na_values=np.nan, sep='\t')

# Explore the structure of your dataset, check that everything is correct
print(data.info())

# Extract features and target variable
y = data["PCN"]
X = data.drop(columns=["PCN"])

# Check for missing values
print(X.isnull().values.any())

# Define numerical and categorical features
numerical_features = X.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X.select_dtypes(include=['object']).columns

# Preprocessing pipelines for numerical and categorical data
numeric_transformer = Pipeline(steps=[
    ('scaler', RobustScaler())])

categorical_transformer = Pipeline(steps=[
    ('ordinal', ce.OrdinalEncoder())])

# Combine preprocessing steps
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numerical_features),
        ('cat', categorical_transformer, categorical_features)])

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the model
rf = RandomForestRegressor()

# Create a pipeline that includes preprocessing and the model
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                           ('randomforestregressor', rf)])


#Create a first parameter distribution to perform a randomized search
param_distributions = {
    'randomforestregressor__n_estimators': [int(x) for x in np.linspace(start=100, stop=3000, num=30)],
    'randomforestregressor__max_features': ['sqrt', 'log2', 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    'randomforestregressor__max_depth': [int(x) for x in np.linspace(10, 300, num=30)],
    'randomforestregressor__min_samples_split': [2, 5, 10, 15, 20, 30, 40, 50],
    'randomforestregressor__min_samples_leaf': [1, 2, 4, 6, 8, 10, 20, 30],
    'randomforestregressor__bootstrap': [True, False]
}

# Initialize RandomizedSearchCV with a wide search
random_search = RandomizedSearchCV(estimator=pipeline, param_distributions=param_distributions,
                                   n_iter=500, cv=5, verbose=1, random_state=42, n_jobs=-1)

# Fit RandomizedSearchCV
random_search.fit(X_train, y_train)

# Get the best parameters
print("Best Parameters from Randomized Search:", random_search.best_params_)

# Get the best estimator
best_model_random = random_search.best_estimator_

# Preprocess the data before applying RFE
X_train_preprocessed = preprocessor.fit_transform(X_train)
X_test_preprocessed = preprocessor.transform(X_test)

# Evaluate RFE with different numbers of features
results = []
n_features_range = X_train_preprocessed.shape[1]  # Use the total number of features

for n_features in range(1, n_features_range + 1):
    selector = RFE(estimator=best_model_random.named_steps['randomforestregressor'], n_features_to_select=n_features, step=1)
    selector = selector.fit(X_train_preprocessed, y_train2)
    
    # Get the selected features
    selected_features = [feature for feature, rank in zip(numerical_features.append(categorical_features), selector.ranking_) if rank == 1]
    
    # Transform the dataset to the selected features
    X_train_selected = selector.transform(X_train_preprocessed)
    X_test_selected = selector.transform(X_test_preprocessed)
    
    # Fit the model with selected features
    best_model_random.named_steps['randomforestregressor'].fit(X_train_selected, y_train)
    
    # Predict on the test set
    y_pred_random = best_model_random.named_steps['randomforestregressor'].predict(X_test_selected)
    
    # Calculate evaluation metrics
    mae_random = mean_absolute_error(y_test2, y_pred_random)
    mse_random = mean_squared_error(y_test2, y_pred_random)
    rmse_random = np.sqrt(mse_random)
    r2_random = r2_score(y_test, y_pred_random)
    
    # Store the results
    results.append((n_features, mae_random, mse_random, rmse_random, r2_random, selected_features))

# Find the best number of features based on the evaluation metrics
best_result = min(results, key=lambda x: x[1])  # Using MAE for comparison
best_n_features = best_result[0]
best_selected_features = best_result[5]

print(f"Best number of features: {best_n_features}")
print(f"Evaluation metrics for {best_n_features} features:")
print(f"Mean Absolute Error (MAE): {best_result[1]}")
print(f"Mean Squared Error (MSE): {best_result[2]}")
print(f"Root Mean Squared Error (RMSE): {best_result[3]}")
print(f"R-squared (R²): {best_result[4]}")
print(f"Selected Features: {best_selected_features}")

# Plot actual vs predicted values for the best model
plt.figure(figsize=(10, 6))
plt.scatter(y_test2, y_pred_random2, alpha=0.5)
plt.xlabel("Actual Values")
plt.ylabel("Predicted Values")
plt.title("Actual vs Predicted Values with Selected Features")
plt.plot([min(y_test2), max(y_test2)], [min(y_test2), max(y_test2)], 'r', linestyle='--')
plt.show()


# Get the feature importances
feature_importance = best_model_random.named_steps["randomforestregressor"].feature_importances_

# Get the feature names
numerical_features = X2.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X2.select_dtypes(include=['object']).columns
all_features = list(numerical_features) + list(categorical_features)

# Print the feature importances with their corresponding names
for name, importance in zip(all_features, feature_importance):
    print(f"Feature: {name}, Importance: {importance}")
