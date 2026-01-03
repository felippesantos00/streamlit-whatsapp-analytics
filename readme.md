# 📊 WhatsApp Metrics

Uma aplicação interativa em **Streamlit** para analisar conversas exportadas do **WhatsApp**.  
O projeto gera gráficos e insights a partir de arquivos `.zip` exportados diretamente do aplicativo.

## ✨ Funcionalidades

- 📅 **Mensagens por dia e autor** (histograma interativo)
- 🌙 **Mensagens por hora (gráfico circular 24h)**
- 📆 **Mensagens por dia da semana**
- 🌞 **Mensagens por período do dia (manhã, tarde, noite, madrugada)**
- 😀 **Top 15 Emojis mais usados**
- ☁️ **Nuvem de palavras** com as mensagens
- 📥 **Download dos dados em CSV**

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) — interface interativa
- [Pandas](https://pandas.pydata.org/) — tratamento dos dados
- [Plotly](https://plotly.com/python/) — gráficos interativos
- [Matplotlib](https://matplotlib.org/) — suporte à wordcloud
- [WordCloud](https://amueller.github.io/word_cloud/) — nuvem de palavras
- [Emoji](https://pypi.org/project/emoji/) — identificação de emojis

## 📦 Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/felippesantos00/portfolio_streamlit/tree/master/whatsapp_metricas_app
cd portfolio_streamlit/whatsapp_metricas_app/scripts
./install.sh # bash
source env_whatsapp_metricas_app/Scripts/activate
```

## ▶️ Como Usar

1. Exporte uma conversa do WhatsApp:

2. Abra o WhatsApp

3. Vá até a conversa desejada

4. Clique em Mais > Exportar conversa > Sem mídia

5. Será gerado um arquivo .zip

6. Rode a aplicação:
7. ```
   cd whatsapp_metricas_app/scripts/
   ./start.sh
   ```

8. Faça upload do arquivo .zip no aplicativo.

## Explore os gráficos, insights e baixe os dados processados em .csv.

📊 Exemplos de Gráficos

- Distribuição circular de mensagens por hora (24 setores fixos)

- Mensagens agrupadas por autor e dia

- Frequência por dia da semana

- Top emojis mais usados

- Nuvem de palavras

## 📝 Estrutura do Projeto

📂whatsapp_metricas_app <br>
┣ 📜 projeto_metricas_whatsapp.py # Código principal da aplicação<br>
┗ 📂 scripts # Scripts para execução do projeto e instalação de dependencias <br>
┣ 📜 requirements.txt # Dependências do projeto <br>
┣ 📜 start.sh
┗ 📜 install.sh
┗ 📜 README.md # Documentação <br>

## 🚀 Melhorias Futuras

- [ ] 📈 Análises de tempo médio de resposta
- [ ] 🔍 Detecção de tópicos por mensagens
- [ ] 🌍 Dashboard multilíngue (pt/en)
