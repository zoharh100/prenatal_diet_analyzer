# Prenatal Diet Analyzer

## Project Description
This project is a Streamlit application that analyzes the nutritional values of foods using the **USDA FoodData Central API**.

The user can add one or more foods eaten during the day, and the application retrieves nutritional data for each food.  
The app displays:
- A table with nutritional values per food
- A macronutrients summary chart
- A micronutrients chart comparing intake to daily pregnancy recommendations

The project demonstrates API integration, data processing with Pandas, and data visualization using Seaborn and Matplotlib.

---

## How to Use the Project
1. Choose the woman’s age group from the sidebar.
2. Type a food name in English and click **Add food**.
3. Repeat to add more foods.
4. Click **Analyze** to retrieve nutritional data and display the results.

---

## Files
- **main.py** – the main file used to run the Streamlit application.
- **.streamlit/secrets.toml** – stores the USDA API key (not uploaded to GitHub).
- **pyproject.toml / poetry.lock** – project dependencies.

---

## Running the Project
To run the application locally, execute the following command from the project directory:

```bash
python -m streamlit run main.py

