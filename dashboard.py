import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Дашборд продаж", layout="wide", page_icon="📊")

FILE = "analytics_report_2026-11-10_18_08.xlsx"

@st.cache_data
def load_data(path):
    df = pd.read_excel(path, sheet_name="Sheet1", skiprows=4)
    df = df[df["Название товара"].notna()]
    df = df[df["Название товара"] != "Среднее значение по товарам"]
    
    df = df.rename(columns={
        "Название товара": "Товар",
        "Ссылка на товар": "Ссылка",
        "Категория 3 уровня": "Категория",
        "Заказано на сумму, ₽": "Сумма_заказов",
        "Заказано, штуки": "Кол_во",
        "Средняя цена, ₽": "Средняя_цена",
        "Минимальная цена, ₽": "Мин_цена",
        "Доля выкупа, %": "Доля_выкупа",
        "Конверсия из показа в заказ, %": "Конверсия"
    })
    
    df["Бренд"] = (df["Бренд"].fillna("Без бренда").replace("", "Без бренда").replace("без бренда", "Без бренда"))
    
    for col in ["Сумма_заказов", "Кол_во", "Средняя_цена", "Мин_цена"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["Доля_выкупа", "Конверсия"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
        
    cols = ["Товар", "Ссылка", "Бренд", "Категория", "Сумма_заказов", "Кол_во", "Средняя_цена", "Мин_цена", "Доля_выкупа", "Конверсия"]
    return df[cols].sort_values("Сумма_заказов", ascending=False).reset_index(drop=True)

df = load_data(FILE)

# =========================================================
# KPI
# =========================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Общая сумма продаж", f"{df['Сумма_заказов'].sum():,.0f} ₽".replace(",", " "))
c2.metric("Товаров", f"{len(df):,}".replace(",", " "))
c3.metric("Брендов", df["Бренд"].nunique())
c4.metric("Средняя цена", f"{df['Средняя_цена'].mean():,.0f} ₽".replace(",", " "))

# =========================================================
# Агрегация и переключатели
# =========================================================
brands_agg = (df.groupby("Бренд", as_index=False)["Сумма_заказов"].sum()
              .sort_values("Сумма_заказов", ascending=False).reset_index(drop=True))
brands_agg["Рейтинг"] = brands_agg.index + 1

st.subheader("🏆 Бренды по сумме продаж")
col_b, col_p = st.columns(2)

with col_b:
    st.caption("**Сколько брендов показать:**")
    brand_limit = st.radio("Бренды", ["Топ-10", "Топ-30", "Топ-50", "Все"], index=3, horizontal=True, label_visibility="collapsed", key="brand_limit")

with col_p:
    st.caption("**Сколько товаров внутри каждого бренда:**")
    product_limit = st.radio("Товары", ["Топ-10", "Топ-30", "Топ-50", "Все"], index=3, horizontal=True, label_visibility="collapsed", key="product_limit")

brand_limit_map = {"Топ-10": 10, "Топ-30": 30, "Топ-50": 50, "Все": len(brands_agg)}
product_limit_map = {"Топ-10": 10, "Топ-30": 30, "Топ-50": 50, "Все": None}

n_brands = brand_limit_map[brand_limit]
n_products = product_limit_map[product_limit]
shown_brands = brands_agg.head(n_brands).reset_index(drop=True)

# =========================================================
# График
# =========================================================
chart_height = max(500, len(shown_brands) * 26)
fig = px.bar(
    shown_brands, x="Сумма_заказов", y="Бренд", orientation="h", text="Сумма_заказов",
    color="Сумма_заказов", color_continuous_scale="Purples",
)
fig.update_traces(texttemplate="%{text:,.0f} ₽".replace(",", " "), textposition="outside")
fig.update_layout(
    title=f"{brand_limit} брендов по сумме продаж",
    yaxis={"categoryorder": "total ascending", "tickfont": {"size": 11 if len(shown_brands) <= 30 else 9}},
    xaxis={"tickfont": {"size": 11}}, showlegend=False, height=chart_height, coloraxis_showscale=False,
    margin=dict(l=10, r=90, t=50, b=10),
)
st.plotly_chart(fig, width='stretch')

# =========================================================
# Функция для рендера HTML-таблицы
# =========================================================
def render_html_table(data):
    html = '<table style="width:100%; border-collapse: collapse; font-size: 14px; font-family: sans-serif;">'
    html += '<thead><tr style="background-color: #f8f9fa; text-align: left; border-bottom: 2px solid #dee2e6;">'
    
    headers = {
        "Товар": "Название товара",
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
                # ИСПРАВЛЕНИЕ: два знака после запятой для конверсии
                html += f'<td style="padding: 10px; text-align: right;">{val:.2f}%</td>'
            else:
                html += f'<td style="padding: 10px;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# =========================================================
# Таблицы товаров по брендам
# =========================================================
st.subheader("🏷️ Бренды и товары")
st.caption(f"Бренды: **{brand_limit}** • Товары в каждом бренде: **{product_limit}** • сортировка по сумме заказов ↓")

for _, brand_row in shown_brands.iterrows():
    brand = brand_row["Бренд"]
    items = df[df["Бренд"] == brand].sort_values("Сумма_заказов", ascending=False)
    total_items = len(items)
    items_shown = items.head(n_products) if n_products else items

    suffix = f" • показано {len(items_shown)} из {total_items}" if (n_products and total_items > n_products) else ""
    header = f"#{brand_row['Рейтинг']} **{brand}** — {brand_row['Сумма_заказов']:,.0f} ₽ • {total_items} тов.{suffix}".replace(",", " ")
    
    with st.expander(header):
        html_table = render_html_table(items_shown)
        st.markdown(html_table, unsafe_allow_html=True)
