import zipfile
import re
import pandas as pd
import emoji
import streamlit as st
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from metrics import PrometheusMetrics
import time
import nltk
from nltk.corpus import stopwords
from collections import Counter
from dateutil.relativedelta import relativedelta
# ================== CONFIG STREAMLIT ==================
st.set_page_config(page_title="WhatsApp Metrics", layout="wide")
st.title("📊 Análise de Métricas de WhatsApp")

# ================== CONSTANTES ==================
CHUNK_SIZE = 150  # mensagens por chunk
nltk.download("stopwords")
STOPWORDS = set(stopwords.words("portuguese"))

# ================== METRICS ==================
metrics = PrometheusMetrics(port=8000)
processing_duration = metrics.create_histogram(
    "whatsapp_processing_duration_seconds",
    "Duração do processamento em segundos",
    ["step"]
)


def track(step: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with processing_duration.labels(step=step).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator

# ================== FUNÇÕES AUXILIARES ==================


def extract_txt_from_zip(zip_file):
    with zipfile.ZipFile(zip_file, "r") as z:
        txt_files = [f for f in z.namelist() if f.endswith(".txt")]
        if not txt_files:
            raise ValueError("Nenhum arquivo .txt encontrado no ZIP")
        with z.open(txt_files[0]) as f:
            return f.read().decode("utf-8"), txt_files[0]


@track("parse_messages")
def parse_messages(text):
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}\s?[APap][Mm]) - ([^:]+): (.+?)(?=\n\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}|$)'
    matches = re.findall(pattern, text, flags=re.DOTALL)
    df = pd.DataFrame(matches, columns=["timestamp", "author", "message"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["message"] = df["message"].str.strip()
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["year_month"] = df["timestamp"].dt.to_period("M")
    # Dias da semana em inglês → português
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
    df["hour"] = df["timestamp"].dt.hour
    return df


def count_unique_emojis(text):
    return list(set([char for char in text if char in emoji.EMOJI_DATA]))

# ================== PLOTS ==================


@track("plot_hour_author")
def plot_messages_by_hour_author(df):
    df_counts = df.groupby(["author", "hour"]).size().reset_index(name="count")
    fig = px.bar(df_counts, x="hour", y="count", color="author",
                 barmode="group", title="🌙 Mensagens por Hora")
    st.plotly_chart(fig, use_container_width=True)


@track("plot_day_author")
def plot_messages_by_day_author(df):
    df["date"] = df["timestamp"].dt.date
    fig = px.histogram(df, x="date", color="author",
                       barmode="group", title="📅 Mensagens por Dia e Autor")
    st.plotly_chart(fig, use_container_width=True)


@track("plot_weekday")
def plot_messages_by_weekday(df):
    counts = df["weekday"].value_counts()
    fig = px.bar(counts, x=counts.index, y=counts.values, title="📆 Mensagens por Dia da Semana", labels={
        "x": "Dia da semana", "y": "Mensagens"})
    st.plotly_chart(fig, use_container_width=True)


@track("plot_periods")
def plot_periods_of_day(df):

    def categorize_period(hour):
        if 6 <= hour < 12:
            return "Manhã"
        elif 12 <= hour < 18:
            return "Tarde"
        elif 18 <= hour < 24:
            return "Noite"
        else:
            return "Madrugada"
    df["period"] = df["hour"].apply(categorize_period)
    fig = px.histogram(df, x="period", color="author", barmode="group", category_orders={
                       "period": ["Madrugada", "Manhã", "Tarde", "Noite"]}, title="🌞 Mensagens por Período do Dia")
    st.plotly_chart(fig, use_container_width=True)


@track("plot_emojis")
def plot_top_emojis(df):
    emojis = df["message"].apply(count_unique_emojis).sum()
    if emojis:
        freq = pd.Series(emojis).value_counts().head(15)
        fig = px.bar(freq, x=freq.index, y=freq.values,
                     title="😀 Top 15 Emojis")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum emoji encontrado.")


@track("plot_wordcloud")
def plot_wordcloud(df):
    text = " ".join(df["message"].dropna().tolist())
    if len(text) > 10:
        wc = WordCloud(width=800, height=400,
                       background_color="white").generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.info("Pouco texto para gerar nuvem de palavras.")

# ================== MINI-BIOGRAFIAS ==================


def clean_word(word):
    """Remove emojis e caracteres especiais de uma palavra."""
    # remove emojis
    word = ''.join(c for c in word if c not in emoji.EMOJI_DATA)
    # mantém só letras/números
    word = re.sub(r'[^\w\s]', '', word)
    return word.strip().lower()


@track("generate_bios")
def generate_mini_biographies(df):
    bios = {}
    # calcula duração total da conversa
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    duration = relativedelta(end_date, start_date)
    for author in df["author"].unique():
        messages = df[df["author"] == author]["message"].dropna().tolist()
        if not messages:
            bios[author] = "Sem mensagens"
            continue

        text = " ".join(messages)
        emojis_used = count_unique_emojis(text)

        words = []
        for w in text.split():
            w = clean_word(w)
            if w and len(w) >= 4 and w not in STOPWORDS:
                words.append(w)
                # formata duração
        duration_str = []
        if duration.years > 0:
            duration_str.append(
                f"{duration.years} ano{'s' if duration.years > 1 else ''}")
        if duration.months > 0:
            duration_str.append(
                f"{duration.months} mês{'es' if duration.months > 1 else ''}")
        if duration.days > 0:
            duration_str.append(
                f"{duration.days} dia{'s' if duration.days > 1 else ''}")
        if not duration_str:
            duration_str = ["menos de 1 dia"]
        most_common_words = [w for w, _ in Counter(words).most_common(10)]

        bios[author] = (
            f"**Participante {author}**  \n"
            f"- Total de mensagens: {len(messages)}  \n"
            f"- Emojis mais usados: {', '.join(emojis_used[:10]) if emojis_used else 'nenhum'}  \n"
            f"- Palavras frequentes: {', '.join(most_common_words) if most_common_words else 'nenhuma'}\n"
            f"- Quanto tempo se conhecem: {', '.join(duration_str)}\n"
        )
    return bios

# ================== FUNÇÃO PRINCIPAL ==================


def main():
    uploaded_file = st.file_uploader(
        "📥 Faça upload do arquivo ZIP do WhatsApp", type="zip")

    if uploaded_file:
        try:
            start_time = time.time()
            text, txt_filename = extract_txt_from_zip(uploaded_file)
            st.success(f"Arquivo '{txt_filename}' extraído com sucesso! ✅")
            df = parse_messages(text)
            if df.empty:
                st.warning("Nenhuma mensagem encontrada.")
                return
            # Plots
            st.subheader("📊 Distribuições e Insights")
            plot_messages_by_hour_author(df)
            plot_messages_by_day_author(df)
            plot_messages_by_weekday(df)
            plot_periods_of_day(df)
            plot_top_emojis(df)
            plot_wordcloud(df)
            # Mini-biografias
            st.subheader("✨ Mini-Biografias")
            bios = generate_mini_biographies(df)
            for bio in bios.values():
                st.markdown(bio)

            st.success(
                f"Processamento completo em {time.time()-start_time:.2f} segundos.")

        except Exception as e:
            st.error(f"Erro: {e}")
    st.markdown("---")
    st.markdown(
        """
        # 🙋 Sobre o Autor
        ## 📫 Contato

        - Email: felipperodrigues00@gmail.com
        - LinkedIn: https://www.linkedin.com/in/felippe-santos-54058111a/
        - Medium: https://medium.com/@felipperodrigues00
        """
    )


# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    main()
