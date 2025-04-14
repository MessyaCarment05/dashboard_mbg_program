# IMPORT LIBRARY
import streamlit as st
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
import altair as alt
import plotly.express as px
import ast
from matplotlib import pyplot as plt
import plotly.graph_objects as go
# Config page
st.set_page_config(page_title="MBG Program Dashboard", page_icon="", layout="wide")

# Load data
df_sentiment=pd.read_csv("dashboard_mbg_program/data/MBG_withSentiment.csv")
df_topics=pd.read_csv("dashboard_mbg_program/data/MBG_topics.csv")


df_sentiment=df_sentiment.drop(["Unnamed: 0.1", "Unnamed: 0"], axis=1)
df_sentiment=df_sentiment.rename(columns={"Unnamed: 0.2" : "No"})

df_topics=df_topics.rename(columns={"sentiment": "sentiment_topic"})

# st.write(df_sentiment)
# st.write(df_topics)


def home_page():
    if "view" not in st.session_state:
        st.session_state.view="sentiment"
    def sentiment_part():
        st.subheader("Sentiment Analysis On MBG Program in Indonesia")
         

        sentiment_options=df_sentiment["sentiment"].unique().tolist()
        day_options=df_sentiment["created_at"].str[:3].unique().tolist()

        selected_sentiment=st.multiselect("Choose Sentiment : " , sentiment_options, default=sentiment_options)
        selected_day =st.multiselect("Choose Day : ", day_options, default=day_options)

        
        filtered_df_sentiment = df_sentiment[
            (df_sentiment["sentiment"].isin(selected_sentiment)) &
            (df_sentiment["created_at"].str[:3].isin(selected_day))
        ]
       
        t11, t22, t33,t44, t55,t66,t77=st.columns(7)  # ini supaya bisa ditengah
        t44.metric(label="Tweets", value=len(filtered_df_sentiment))
        style_metric_cards(background_color="#071021", border_left_color="#1f66bd")

        b1, b2=st.columns(2)
        sentiment_source=filtered_df_sentiment
        sentiment_source["created_at"]=pd.to_datetime(sentiment_source["created_at"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce")
        sentiment_source["Day"]=sentiment_source["created_at"].dt.strftime('%a')

        with b1:
            st.subheader("Tweet Sentiment Distribution", divider="rainbow")
            sentiment_count = sentiment_source.groupby(["Day", "sentiment"]).size().reset_index(name="TweetCount")
            bar_chart = alt.Chart(sentiment_count).mark_bar().encode(
                x=alt.X("Day:N", title="Day of the Week",sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
                y=alt.Y("TweetCount:Q", title="Total Tweets per Day"),
                color=alt.Color("sentiment:N", title="Sentiment"), 
                tooltip=["Day", "sentiment", "TweetCount"]  
            ).properties(width=600, height=400)
            st.altair_chart(bar_chart)
      
        with b2:
            st.subheader("Tweet Sentiment Distribution per Day", divider="rainbow")
   
            tweet_per_day = sentiment_source.groupby("Day").size().reset_index(name="TweetCountDay")

          
            total_tweets = tweet_per_day["TweetCountDay"].sum()
            tweet_per_day["Percentage"] = (tweet_per_day["TweetCountDay"] / total_tweets) * 100

           
            fig = px.pie(
                tweet_per_day, 
                names="Day", 
                values="TweetCountDay", 
                category_orders={"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
                color_discrete_sequence=px.colors.qualitative.Set2  
            )

    
            fig.update_traces(textinfo="percent+label", textposition="inside", textfont_size=14)

            st.plotly_chart(fig, use_container_width=True)


        # metric total sentiment_value

        st.subheader("Top 3 Most Liked Tweet", divider="rainbow")

        df_top_3 = filtered_df_sentiment.sort_values(by="favorite_count", ascending=False).head(3)
        df_top_3=df_top_3.reset_index(drop=True)
        df_top_3["rank"]=df_top_3.index + 1
        df_top_3 =df_top_3[["rank","full_text", "favorite_count"]]

        styled_table = df_top_3.style.background_gradient(subset=["favorite_count"], cmap="turbo")
        st.dataframe(styled_table,use_container_width=True)

        if st.button("Switch to Topic Analysis"):
            st.session_state.view = "topic"
            st.rerun()
  
    def topic_part():
        st.subheader("Popular Topic Analysis on MBG Program in Indonesia")
        topic_options = df_topics["topic_name"].unique().tolist()
        selected_topic=st.multiselect("Choose Topic : ", topic_options, default=topic_options)

        filtered_df_topic=df_topics[
            df_topics["topic_name"].isin(selected_topic) 
        ]

        new_filtered_df_topic= filtered_df_topic

        new_filtered_df_topic["docs_list"]=new_filtered_df_topic["docs_list"].apply(lambda x:ast.literal_eval(x) if isinstance(x, str) else x)

        new_filtered_df_topic=new_filtered_df_topic.explode("docs_list").reset_index(drop=True)

        new_filtered_df_topic["docs_list"]=new_filtered_df_topic["docs_list"].astype(int)

        filtered_topic_result=new_filtered_df_topic.merge(df_sentiment, left_on="docs_list", right_index=True)

        final_df_topic = filtered_topic_result.groupby(['topic_id','topic_name'])['sentiment'].agg(
            neutral_count=lambda x: (x == "Neutral").sum(),
            positive_count=lambda x: (x=="Positive").sum(),
            negative_count=lambda x: (x=="Negative").sum(),
        ).reset_index()

        final_df_topic=final_df_topic[['topic_id', 'topic_name', 'negative_count', 'neutral_count', 'positive_count']]
        sentiment_topic_value_df=filtered_topic_result[['topic_id', 'sentiment_value']].drop_duplicates(subset='topic_id')

        final_df_topic=final_df_topic.merge(sentiment_topic_value_df, on='topic_id', how="left")
        s11,s22,s33,s44,s55,s66,s77=st.columns(7) # ini buat atur posisi 
        s11.metric(label="sentiment_value", value=final_df_topic['sentiment_value'].sum())
        style_metric_cards(background_color="#071021", border_left_color="#1f66bd")

        #  Bar Chart
        st.subheader("Sentiment Distribution of 10 Most Relevant Topics", divider="rainbow")
        fig = go.Figure()

        # Tambah masing-masing bar
        fig.add_trace(go.Bar(
            y=final_df_topic['topic_name'],
            x=final_df_topic['negative_count'],
            name='negative_count',
            orientation='h',
            marker=dict(color='red')
        ))

        fig.add_trace(go.Bar(
            y=final_df_topic['topic_name'],
            x=final_df_topic['neutral_count'],
            name='neutral_count',
            orientation='h',
            marker=dict(color='gold'),
        ))

        fig.add_trace(go.Bar(
            y=final_df_topic['topic_name'],
            x=final_df_topic['positive_count'],
            name='positive_count',
            orientation='h',
            marker=dict(color='lightgreen'),
        ))
        fig.update_layout(
            barmode='stack',
            xaxis_title='Total Tweet',
            yaxis_title='Topic',    
        )   
            
        st.plotly_chart(fig, use_container_width=True)

        # sample tweet
        st.subheader("Tweet Preview from Selected Topic", divider="rainbow")
        view_tweet_topic=filtered_topic_result[["full_text", "sentiment", "topic_name","favorite_count", ]]     
        st.dataframe(view_tweet_topic,use_container_width=True)
        if st.button("Switch to Sentiment Analysis"):
            st.session_state.view = "sentiment"
            st.rerun()
    if st.session_state.view=="sentiment":
        sentiment_part()
    else:
        topic_part()


home_page()




