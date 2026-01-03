import zipfile
import re
import time
import os
from collections import Counter
from io import BytesIO

import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import emoji
import nltk
from nltk.corpus import stopwords
from dateutil.relativedelta import relativedelta

# ================== CONFIG STREAMLIT ==================
st.set_page_config(
    page_title="WhatsApp Metrics",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Aplicativo para análise de métricas de conversas do WhatsApp.",
    },
)

st.title("📊 Análise de Métricas de WhatsApp")

# ================== STOPWORDS (SAFE CLOUD) ==================
try:
    STOPWORDS = set(stopwords.words("portuguese"))
except LookupError:
    nltk.download("stopwords")
    STOPWORDS = set(stopwords.words("portuguese"))

# ================== METRICS (SAFE PARA CLOUD) ==================
ENABLE_METRICS = os.getenv("STREAMLIT_SERVER_HEADLESS") != "true"

if ENABLE_METRICS:
    from metrics import PrometheusMetrics

    metrics = PrometheusMetrics(port=8000)
    processing_duration = metrics.create_histogram(
        "whatsapp_processing_duration_seconds",
        "Duração do processamento em segundos",
        ["step"],
    )

    def track(step: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                with processing_duration.labels(step=step).time():
                    return func(*args, **kwargs)
            return wrapper
        return decorator
else:
    def track(step: str):
        def decorator(func):
            return func
        return decorator

# ================== FUNÇÕES AUXILIARES ==================


def extract_txt_from_zip(zip_file):
    with zipfile.ZipFile(zip_file, "r") as z:
        txt_files = [f for f in z.namelist() if f.endswith(".txt")]
        if not txt_files:
            raise ValueError("Nenhum arquivo .txt encontrado no ZIP")
        with z.open(txt_files[0]) as f:
            return f.read().decode("utf-8"), txt_files[0]


@st.cache_data(show_spinner=False)
@track("parse_messages")
def parse_messages(text):
    pattern = (
        r"(\d{1,2}/\d{1,2}/\d{2,4}, "
        r"\d{1,2}:\d{2}\s?[APap][Mm]) - "
        r"([^:]+): (.+?)(?=\n\d{1,2}/\d{1,2}/\d{2,4},|\Z)"
    )
    matches = re.findall(pattern, text, flags=re.DOTALL)

    df = pd.DataFrame(matches, columns=["timestamp", "author", "message"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["message"] = df["message"].str.strip()

    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["year_month"] = df["timestamp"].dt.to_period("M")
    df["hour"] = df["timestamp"].dt.hour

    weekday_map = {
        "Monday": "Segunda-feira",
        "Tuesday": "Terça-feira",
        "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira",
        "Friday": "Sexta-feira",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    df["weekday"] = df["timestamp"].dt.day_name().map(weekday_map)

    return df.dropna(subset=["timestamp"])


def count_unique_emojis(text):
    return list({char for char in text if char in emoji.EMOJI_DATA})


def clean_word(word):
    word = "".join(c for c in word if c not in emoji.EMOJI_DATA)
    word = re.sub(r"[^\w\s]", "", word)
    return word.strip().lower()

# ================== PLOTS ==================


@track("plot_hour_author")
def plot_messages_by_hour_author(df):
    df_counts = df.groupby(["author", "hour"]).size().reset_index(name="count")
    fig = px.bar(
        df_counts,
        x="hour",
        y="count",
        color="author",
        barmode="group",
        title="🌙 Mensagens por Hora",
    )
    st.plotly_chart(fig, use_container_width=True)


@track("plot_day_author")
def plot_messages_by_day_author(df):
    df["date"] = df["timestamp"].dt.date
    fig = px.histogram(
        df,
        x="date",
        color="author",
        barmode="group",
        title="📅 Mensagens por Dia",
    )
    st.plotly_chart(fig, use_container_width=True)


@track("plot_weekday")
def plot_messages_by_weekday(df):
    counts = df["weekday"].value_counts()
    fig = px.bar(
        x=counts.index,
        y=counts.values,
        title="📆 Mensagens por Dia da Semana",
        labels={"x": "Dia", "y": "Mensagens"},
    )
    st.plotly_chart(fig, use_container_width=True)


@track("plot_periods")
def plot_periods_of_day(df):
    def categorize(hour):
        if 6 <= hour < 12:
            return "Manhã"
        if 12 <= hour < 18:
            return "Tarde"
        if 18 <= hour < 24:
            return "Noite"
        return "Madrugada"

    df["period"] = df["hour"].apply(categorize)

    fig = px.histogram(
        df,
        x="period",
        color="author",
        barmode="group",
        category_orders={
            "period": ["Madrugada", "Manhã", "Tarde", "Noite"]
        },
        title="🌞 Mensagens por Período do Dia",
    )
    st.plotly_chart(fig, use_container_width=True)


@track("plot_emojis")
def plot_top_emojis(df):
    emojis = df["message"].apply(count_unique_emojis).sum()
    if not emojis:
        st.info("Nenhum emoji encontrado.")
        return

    freq = pd.Series(emojis).value_counts().head(15)
    fig = px.bar(freq, x=freq.index, y=freq.values, title="😀 Top Emojis")
    st.plotly_chart(fig, use_container_width=True)


@track("plot_wordcloud")
def plot_wordcloud(df):
    text = " ".join(df["message"].dropna())
    if len(text) < 20:
        st.info("Pouco texto para gerar nuvem de palavras.")
        return

    wc = WordCloud(width=900, height=400,
                   background_color="white").generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

# ================== MINI-BIOGRAFIAS ==================


@track("generate_bios")
def generate_mini_biographies(df):
    bios = {}

    start_date = df["timestamp"].min()
    end_date = df["timestamp"].max()
    duration = relativedelta(end_date, start_date)

    for author in df["author"].unique():
        msgs = df[df["author"] == author]["message"].dropna()
        text = " ".join(msgs)

        emojis_used = count_unique_emojis(text)

        words = [
            clean_word(w)
            for w in text.split()
            if clean_word(w) and len(w) >= 4 and clean_word(w) not in STOPWORDS
        ]

        common_words = [w for w, _ in Counter(words).most_common(10)]

        duration_str = []
        if duration.years:
            duration_str.append(f"{duration.years} ano(s)")
        if duration.months:
            duration_str.append(f"{duration.months} mês(es)")
        if duration.days:
            duration_str.append(f"{duration.days} dia(s)")

        bios[author] = (
            f"**Participante {author}**  \n"
            f"- Total de mensagens: {len(msgs)}  \n"
            f"- Emojis mais usados: {', '.join(emojis_used[:10]) or 'nenhum'}  \n"
            f"- Palavras frequentes: {', '.join(common_words) or 'nenhuma'}  \n"
            f"- Tempo de conversa: {', '.join(duration_str) or 'menos de 1 dia'}"
        )

    return bios

# ================== MAIN ==================


def main():
    uploaded_file = st.file_uploader(
        "📥 Faça upload do arquivo ZIP do WhatsApp", type="zip"
    )

    if uploaded_file:
        try:
            start = time.time()
            text, filename = extract_txt_from_zip(uploaded_file)

            st.success(f"Arquivo **{filename}** carregado com sucesso!")

            df = parse_messages(text)

            if df.empty:
                st.warning("Nenhuma mensagem encontrada.")
                return

            st.subheader("📊 Distribuições e Insights")
            plot_messages_by_hour_author(df)
            plot_messages_by_day_author(df)
            plot_messages_by_weekday(df)
            plot_periods_of_day(df)
            plot_top_emojis(df)
            plot_wordcloud(df)

            st.subheader("✨ Mini-Biografias")
            bios = generate_mini_biographies(df)
            for bio in bios.values():
                st.markdown(bio)

            st.success(
                f"Processamento concluído em {time.time() - start:.2f}s")

        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    st.markdown("---")
    st.markdown(
        """
        ### 🙋 Sobre o Autor
        - 📧 Email: **felipperodrigues00@gmail.com**
        - 🔗 LinkedIn: https://www.linkedin.com/in/felippe-santos-54058111a/
        - ✍️ Medium: https://medium.com/@felipperodrigues00
        """
    )


# ================== EXEC ==================
if __name__ == "__main__":
    main()
