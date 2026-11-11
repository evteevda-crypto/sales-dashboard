import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Дашборд продаж", layout="wide", page_icon="📊")

DEFAULT_FILE = "analytics_report_2026-11-10_18_08.xlsx"

# =========================================================
# Боковая панель: ЗАГРУЗКА ДАННЫХ
# =========================================================
st.sidebar.header("📁 Загрузка данных")
uploaded_file = st.sidebar.file_uploader("Загрузите Excel-файл отчета (Sheet1)", type=["xlsx"])

if uploaded_file is not None:
    st.sidebar.success("✅ Файл успешно загружен!")
    data_source = uploaded_file
    file_key = uploaded_file.name 
else:
    st.sidebar.info("Используется файл по умолчанию.")
    data_source = DEFAULT_FILE
    file_key = "default_file"

@st.cache_data
def load_data(source):
    try:
        if isinstance(source, str):
            df = pd.read_excel(source, sheet_name="Sheet1", skiprows=4)
        else:
            df = pd.read_excel(source, sheet_name="Sheet1", skiprows=4)
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    # Очистка данных
    df = df[df["Название товара"].notna()]
    df = df[df["Название товара"] != "Среднее значение по товарам"]
    
    df = df.rename(columns={
        "Название товара": "Товар",
        "Ссылка на товар": "Ссылка",
        "Продавец": "Продавец",
        "Бренд": "Бренд",
        "Категория 3 уровня": "Категория",
        "Заказано на сумму, ₽": "Сумма_заказов",
        "Заказано, штуки": "Кол_во",
        "Средняя цена, ₽": "Средняя_цена",
        "Минимальная цена, ₽": "Мин_цена",
        "Доля выкупа, %": "Доля_выкупа",
        "Конверсия из показа в заказ, %": "Конверсия"
    })
    
    # Заполняем пустые значения
    df["Бренд"] = (df["Бренд"].fillna("Без бренда").replace("", "Без бренда").replace("без бренда", "Без бренда"))
    df["Продавец"] = df["Продавец"].fillna("Неизвестный продавец")
    
    # Приводим типы данных
    for col in ["Сумма_заказов", "Кол_во", "Средняя_цена", "Мин_цена"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["Доля_выкупа", "Конверсия"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
        
    cols = ["Товар", "Ссылка", "Продавец", "Бренд", "Категория", "Сумма_заказов", "Кол_во", "Средняя_цена", "Мин_цена", "Доля_выкупа", "Конверсия"]
    return df[cols].sort_values("Сумма_заказов", ascending=False).reset_index(drop=True)

df_full = load_data(data_source)

# =========================================================
# Боковая панель: ФИЛЬТРЫ
# =========================================================
st.sidebar.divider()
st.sidebar.header("🔍 Фильтры")

all_brands = sorted(df_full["Бренд"].unique())
all_sellers = sorted(df_full["Продавец"].unique())

selected_brands = st.sidebar.multiselect(
    "Выберите бренды:",
    options=all_brands,
    default=all_brands,
    key=f"brands_{file_key}",
    help="Начните вводить название для быстрого поиска"
)

selected_sellers = st.sidebar.multiselect(
    "Выберите продавцов:",
    options=all_sellers,
    default=all_sellers,
    key=f"sellers_{file_key}",
    help="Начните вводить название для быстрого поиска"
)

df = df_full[
    (df_full["Бренд"].isin(selected_brands)) & 
    (df_full["Продавец"].isin(selected_sellers))
]

if df.empty:
    st.warning("⚠️ По выбранным фильтрам нет данных. Пожалуйста, выберите другие бренды или продавцов.")
    st.stop()

# =========================================================
# KPI
# =========================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Общая сумма продаж", f"{df['Сумма_заказов'].sum():,.0f} ₽".replace(",", " "))
c2.metric("Товаров", f"{len(df):,}".replace(",", " "))
c3.metric("Продавцов", df["Продавец"].nunique())
c4.metric("Средняя цена", f"{df['Средняя_цена'].mean():,.0f} ₽".replace(",", " "))

# =========================================================
# Функция для рендера HTML-таблицы
# =========================================================
def render_html_table(data):
    html = '<table style="width:100%; border-collapse: collapse; font-size: 14px; font-family: sans-serif;">'
    html += '<thead><tr style="background-color: #f8f9fa; text-align: left; border-bottom: 2px solid #dee2e6;">'
    
    headers = {
        "Товар": "Название товара",
        "Продавец": "Продавец",
        "Бренд": "Бренд",
        "Категория": "Категория",
        "Сумма_заказов": "Заказано на сумму, ₽",
        "Кол_во": "Заказано, шт",
        "Средняя_цена": "Средняя цена, ₽",
        "Мин_цена": "Мин. цена, ₽",
        "Доля_выкупа": "Доля выкупа, %",
        "Конверсия": "Конверсия в заказ, %"
    }
    
    for col in headers:
        html += f'<th style="padding: 10px; border-bottom: 2px solid #dee2e6;">{headers[col]}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in data.iterrows():
        html += '<tr style="border-bottom: 1px solid #eee;">'
        for col in headers:
            val = row[col]
            if col == "Товар":
                html += f'<td style="padding: 10px;"><a href="{row["Ссылка"]}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: 500;">{val}</a></td>'
            elif col in ["Сумма_заказов", "Средняя_цена", "Мин_цена"]:
                html += f'<td style="padding: 10px; text-align: right;">{val:,.0f} ₽</td>'.replace(",", " ")
            elif col == "Кол_во":
                html += f'<td style="padding: 10px; text-align: right;">{val:,.0f}</td>'
            elif col == "Доля_выкупа":
                html += f'<td style="padding: 10px; text-align: right;">{val:.1f}%</td>'
            elif col == "Конверсия":
                html += f'<td style="padding: 10px; text-align: right;">{val:.2f}%</td>'
            else:
                html += f'<td style="padding: 10px;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# =========================================================
# БЛОК 1: ТОП ТОВАРОВ
# =========================================================
st.divider()
st.subheader("🔥 Топ товаров по сумме продаж")

col_tp, _ = st.columns([1, 2])
with col_tp:
    st.caption("**Сколько товаров показать:**")
    product_top_limit = st.radio("Топ товаров", ["Топ-10", "Топ-30", "Топ-50", "Все"], index=0, horizontal=True, label_visibility="collapsed", key="product_top_limit")

pt_limit_map = {"Топ-10": 10, "Топ-30": 30, "Топ-50": 50, "Все": len(df)}
n_top_products = pt_limit_map[product_top_limit]

top_products_df = df.head(n_top_products).copy().reset_index(drop=True)

top_products_df['Label'] = top_products_df.apply(
    lambda row: f"{row.name + 1}. {row['Товар'][:40]}..." if len(row['Товар']) > 40 else f"{row.name + 1}. {row['Товар']}", 
    axis=1
)

# Предварительно форматируем текст с пробелами для графика
top_products_df['Сумма_текст'] = top_products_df['Сумма_заказов'].apply(lambda x: f"{x:,.0f}".replace(",", " ") + " ₽")

chart_height_products = max(500, len(top_products_df) * 30)
fig_products = px.bar(
    top_products_df, x="Сумма_заказов", y="Label", orientation="h", text="Сумма_текст"
)
fig_products.update_traces(
    marker_color='#4a90e2', # Единый синий цвет
    texttemplate="%{text}", # Берем уже готовый текст
    textposition="auto", 
    insidetextanchor="middle"
)
fig_products.update_layout(
    title=f"{product_top_limit} товаров по сумме продаж",
    yaxis={"categoryorder": "total ascending", "tickfont": {"size": 10}},
    xaxis={"tickfont": {"size": 10}}, showlegend=False, height=chart_height_products, 
    coloraxis_showscale=False, margin=dict(l=10, r=120, t=50, b=10), # r=120 для запаса под текст снаружи
)
st.plotly_chart(fig_products, width='stretch')

with st.expander(f"📋 Подборка: {product_top_limit} товаров (детали)"):
    st.markdown(render_html_table(top_products_df), unsafe_allow_html=True)


# =========================================================
# БЛОК 2: ПРОДАВЦЫ И ИХ ТОВАРЫ
# =========================================================
st.divider()
st.subheader("🏆 Продавцы по сумме продаж")

sellers_agg = (df.groupby("Продавец", as_index=False)["Сумма_заказов"].sum()
               .sort_values("Сумма_заказов", ascending=False).reset_index(drop=True))
sellers_agg["Рейтинг"] = sellers_agg.index + 1

col_s, col_p = st.columns(2)

with col_s:
    st.caption("**Сколько продавцов показать:**")
    seller_limit = st.radio("Продавцы", ["Топ-10", "Топ-30", "Топ-50", "Все"], index=3, horizontal=True, label_visibility="collapsed", key="seller_limit")

with col_p:
    st.caption("**Сколько товаров внутри каждого продавца:**")
    product_limit = st.radio("Товары внутри продавца", ["Топ-10", "Топ-30", "Топ-50", "Все"], index=3, horizontal=True, label_visibility="collapsed", key="product_limit")

seller_limit_map = {"Топ-10": 10, "Топ-30": 30, "Топ-50": 50, "Все": len(sellers_agg)}
product_limit_map = {"Топ-10": 10, "Топ-30": 30, "Топ-50": 50, "Все": None}

n_sellers = seller_limit_map[seller_limit]
n_products = product_limit_map[product_limit]
shown_sellers = sellers_agg.head(n_sellers).reset_index(drop=True)

# Предварительно форматируем текст с пробелами для графика
shown_sellers['Сумма_текст'] = shown_sellers['Сумма_заказов'].apply(lambda x: f"{x:,.0f}".replace(",", " ") + " ₽")

chart_height_sellers = max(500, len(shown_sellers) * 26)
fig_sellers = px.bar(
    shown_sellers, x="Сумма_заказов", y="Продавец", orientation="h", text="Сумма_текст"
    # Убрали color="Сумма_заказов", чтобы не было градиента
)
fig_sellers.update_traces(
    marker_color='#8e44ad', # Единый фиолетовый цвет
    texttemplate="%{text}", 
    textposition="auto", 
    insidetextanchor="middle"
)
fig_sellers.update_layout(
    title=f"{seller_limit} продавцов по сумме продаж",
    yaxis={"categoryorder": "total ascending", "tickfont": {"size": 11 if len(shown_sellers) <= 30 else 9}},
    xaxis={"tickfont": {"size": 11}}, showlegend=False, height=chart_height_sellers, coloraxis_showscale=False,
    margin=dict(l=10, r=120, t=50, b=10),
)
st.plotly_chart(fig_sellers, width='stretch')

st.caption(f"Продавцы: **{seller_limit}** • Товары в каждом: **{product_limit}** • сортировка по сумме заказов ↓")

for _, seller_row in shown_sellers.iterrows():
    seller = seller_row["Продавец"]
    items = df[df["Продавец"] == seller].sort_values("Сумма_заказов", ascending=False)
    total_items = len(items)
    items_shown = items.head(n_products) if n_products else items

    suffix = f" • показано {len(items_shown)} из {total_items}" if (n_products and total_items > n_products) else ""
    header = f"#{seller_row['Рейтинг']} **{seller}** — {seller_row['Сумма_заказов']:,.0f} ₽ • {total_items} тов.{suffix}".replace(",", " ")
    
    with st.expander(header):
        st.markdown(render_html_table(items_shown), unsafe_allow_html=True)
