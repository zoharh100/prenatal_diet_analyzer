import streamlit as st
import pandas as pd
import requests
import seaborn as sns
import matplotlib.pyplot as plt

#  כותרת הדף
st.set_page_config(page_title="Prenatal Diet Analyzer")

# (API)

def get_food_info(food_name, api_key):
    """
    פונקציה שמקבלת שם מאכל, מחפשת אותו ב-USDA API
    ומחזירה מילון עם הערכים התזונתיים ל-100 גרם.
    כוללת טיפול בשגיאות ו-timeout.
    """
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    search_params = {
        "query": food_name,
        "pageSize": 1,
        "api_key": api_key
    }

    try:
        # שלב 1: חיפוש המאכל (timeout=30 שניות כדי למנוע תקיעה)
        response = requests.get(search_url, params=search_params, timeout=30)
        response.raise_for_status()  # בדיקה אם חזרה שגיאה מהשרת
        data = response.json()

        if not data.get("foods"):
            return "not_found"  # סימון מיוחד אם לא נמצא מאכל

        # לוקחים את ה-ID של התוצאה הראשונה
        fdc_id = data["foods"][0]["fdcId"]
        found_name = data["foods"][0]["description"]

        # שלב 2: קבלת פרטים מלאים לפי fdcId
        details_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
        details_params = {"api_key": api_key}

        details_response = requests.get(details_url, params=details_params, timeout=30)
        details_response.raise_for_status()
        details_data = details_response.json()

        # הכנת מילון לתוצאות
        nutrients = {
            "Food Name": found_name,
            # הוספתי הבהרה שהערכים הם ל-100 גרם
            "Energy (kcal)": 0, "Protein (g)": 0, "Total Fat (g)": 0,
            "Fiber (g)": 0, "Sugars (g)": 0, "Calcium (mg)": 0,
            "Iron (mg)": 0, "Magnesium (mg)": 0, "Vitamin D (mcg)": 0,
            "Vitamin B12 (mcg)": 0
        }

        nutrient_map = {
            1008: "Energy (kcal)",
            1003: "Protein (g)",
            1004: "Total Fat (g)",
            1079: "Fiber (g)",
            2000: "Sugars (g)",
            1087: "Calcium (mg)",
            1089: "Iron (mg)",
            1090: "Magnesium (mg)",
            1114: "Vitamin D (mcg)",
            1178: "Vitamin B12 (mcg)"
        }

        for item in details_data.get("foodNutrients", []):
            n_id = item.get("nutrient", {}).get("id")
            amount = item.get("amount", 0)

            if n_id in nutrient_map:
                nutrients[nutrient_map[n_id]] = amount

        return nutrients

    except requests.exceptions.Timeout:
        return "timeout"
    except requests.exceptions.RequestException:
        return "error"


# --- תצוגת Streamlit ---

st.title("Prenatal Diet Analyzer 🤰")
st.write("This app analyzes the nutritional value of foods using USDA data.")

# --- סרגל צד (Sidebar) ---
st.sidebar.header("User Details & Food List")

age_group = st.sidebar.selectbox("Age group of the woman (years)", ["18-30", "31-47"])

if 'food_list' not in st.session_state:
    st.session_state['food_list'] = []

food_input = st.sidebar.text_input("Type a food name (English):")

if st.sidebar.button("Add food"):
    if food_input:
        # בדיקת כפילויות
        exists = False
        for f in st.session_state['food_list']:
            if f.lower() == food_input.lower():
                exists = True
                break

        if exists:
            st.sidebar.warning("Food already in list!")
        else:
            st.session_state['food_list'].append(food_input)
    else:
        st.sidebar.warning("Please type a food name.")

st.sidebar.markdown("### Your List:")
for i, food in enumerate(st.session_state['food_list']):
    st.sidebar.text(f"{i + 1}. {food}")

if st.sidebar.button("Clear foods"):
    st.session_state['food_list'] = []
    st.experimental_rerun()

# --- לוגיקה ראשית (כפתור Analyze) ---

if st.sidebar.button("Analyze"):
    # וידוא שיש לפחות מאכל אחד (הלוגיקה עובדת גם עבור 1 וגם עבור 10)
    if not st.session_state['food_list']:
        st.error("Please add at least one food to the list.")
    else:
        try:
            api_key = st.secrets["USDA_API_KEY"]
        except:
            st.error("API Key missing in .streamlit/secrets.toml")
            st.stop()

        all_foods_data = []

        with st.spinner('Fetching data from USDA API...'):
            for food_name in st.session_state['food_list']:
                result = get_food_info(food_name, api_key)

                # טיפול במצבי שגיאה שונים
                if result == "not_found":
                    st.warning(f"⚠️ Food not found: '{food_name}' - Skipping.")
                elif result == "timeout":
                    st.warning(f"⏳ Timeout: '{food_name}' took too long - Skipping.")
                elif result == "error":
                    st.warning(f"❌ Connection error for: '{food_name}' - Skipping.")
                elif isinstance(result, dict):
                    all_foods_data.append(result)

        # אם יש נתונים (אפילו של מאכל אחד)
        if all_foods_data:
            df = pd.DataFrame(all_foods_data)
            df.index = range(1, len(df) + 1)

            # --- תיקון: הצגה ברורה שהכמות היא ל-100 גרם ---
            st.markdown("### Nutritional Values Table")
            st.info("ℹ️ All values are per **100g** of the food product.")
            st.dataframe(df)

            # חישוב סה"כ (עבור מאכל אחד, הסכום הוא פשוט הערכים שלו)
            numeric_df = df.drop(columns=["Food Name"])
            total_nutrients = numeric_df.sum()

            # --- גרף 1: מאקרו ---
            st.subheader("1. Macronutrients Analysis (Total Amount)")
            macros = ["Energy (kcal)", "Protein (g)", "Total Fat (g)", "Fiber (g)", "Sugars (g)"]
            macro_data = total_nutrients[macros].reset_index()
            macro_data.columns = ["Nutrient", "Amount"]

            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=macro_data, x="Amount", y="Nutrient", ax=ax1, palette="viridis")

            for p in ax1.patches:
                width = p.get_width()
                if width > 0:  # מציג מספר רק אם יש ערך
                    ax1.text(width + 0.5, p.get_y() + p.get_height() / 2,
                             f'{width:.1f}', va='center')
            st.pyplot(fig1)

            # --- גרף 2: מיקרו ---
            st.subheader("2. Micronutrients vs. Daily Recommendation")
            magnesium_target = 350 if age_group == "18-30" else 360
            targets = {
                "Calcium (mg)": 1000,
                "Iron (mg)": 27,
                "Magnesium (mg)": magnesium_target,
                "Vitamin D (mcg)": 15,
                "Vitamin B12 (mcg)": 2.6
            }

            micro_stats = []
            for nutrient, target in targets.items():
                total_val = total_nutrients.get(nutrient, 0)
                percent = (total_val / target) * 100
                micro_stats.append({
                    "Nutrient": nutrient,
                    "Percent": percent,
                    "Target": target
                })

            micro_df = pd.DataFrame(micro_stats)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=micro_df, x="Nutrient", y="Percent", ax=ax2, palette="coolwarm")

            ax2.axhline(100, color='red', linestyle='--', linewidth=1.5, label="100% Target")
            ax2.legend()
            ax2.set_ylabel("% of Daily Recommendation")

            for i, p in enumerate(ax2.patches):
                height = p.get_height()
                target_val = micro_df.loc[i, "Target"]
                # הצגת הטקסט מעל העמודה
                label_text = f"{height:.1f}%\n(Rec: {target_val})"
                ax2.text(p.get_x() + p.get_width() / 2, height + 1,
                         label_text, ha='center', va='bottom', fontsize=9)

            st.pyplot(fig2)

        elif not all_foods_data and st.session_state['food_list']:
            st.error("Could not retrieve data. Please check spelling or internet connection.")