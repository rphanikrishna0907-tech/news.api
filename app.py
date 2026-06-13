import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Advanced News Headlines App",
    page_icon="📰",
    layout="wide"
)

# -------------------------------------------------
# App Title
# -------------------------------------------------
st.title("📰 Advanced News Headlines Application")
st.caption("Fetch and filter live news headlines using NewsAPI")

# -------------------------------------------------
# API Configuration
# -------------------------------------------------
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Recommended: store your API key in .streamlit/secrets.toml
# NEWS_API_KEY = st.secrets["NEWSAPI_KEY"]

# Temporary fallback: enter API key in sidebar
st.sidebar.header("🔐 API Settings")
api_key = st.sidebar.text_input(
    "Enter NewsAPI Key",
    type="password",
    help="Paste your NewsAPI key here. For production, use Streamlit secrets."
)

# -------------------------------------------------
# Country / Location Options
# -------------------------------------------------
country_options = {
    "India": "in",
    "United States": "us",
    "United Kingdom": "gb",
    "Australia": "au",
    "Canada": "ca",
    "Germany": "de",
    "France": "fr",
    "Japan": "jp",
    "China": "cn",
    "Russia": "ru",
    "United Arab Emirates": "ae",
    "Singapore": "sg",
    "South Africa": "za"
}

category_options = [
    "general",
    "business",
    "entertainment",
    "health",
    "science",
    "sports",
    "technology"
]

# -------------------------------------------------
# Sidebar Filters
# -------------------------------------------------
st.sidebar.header("🔎 News Filters")

selected_country_name = st.sidebar.selectbox(
    "Select Location / Country",
    list(country_options.keys()),
    index=0
)

selected_country = country_options[selected_country_name]

selected_category = st.sidebar.selectbox(
    "Select Topic / Category",
    category_options,
    index=0
)

keyword = st.sidebar.text_input(
    "Search Keyword",
    placeholder="Example: railway, economy, cricket, AI"
)

article_count = st.sidebar.slider(
    "Number of Articles",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

show_only_with_images = st.sidebar.checkbox(
    "Show only articles with images",
    value=False
)

show_only_with_description = st.sidebar.checkbox(
    "Show only articles with description",
    value=False
)

fetch_button = st.sidebar.button("Fetch News", type="primary")

# -------------------------------------------------
# Helper Function
# -------------------------------------------------
@st.cache_data(ttl=300)
def fetch_news(api_key, country, category, keyword, page_size):
    params = {
        "apiKey": api_key,
        "country": country,
        "category": category,
        "pageSize": page_size
    }

    if keyword:
        params["q"] = keyword

    response = requests.get(NEWS_API_URL, params=params, timeout=15)

    if response.status_code != 200:
        try:
            error_data = response.json()
            return None, error_data.get("message", "Unable to fetch news.")
        except Exception:
            return None, "Unable to fetch news."

    data = response.json()

    if data.get("status") != "ok":
        return None, data.get("message", "NewsAPI returned an error.")

    return data.get("articles", []), None


def format_date(date_string):
    if not date_string:
        return "N/A"

    try:
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d-%m-%Y %I:%M %p")
    except Exception:
        return date_string


# -------------------------------------------------
# Main Content
# -------------------------------------------------
if not api_key:
    st.warning("Please enter your NewsAPI key in the sidebar to fetch news.")

else:
    if fetch_button:
        with st.spinner("Fetching latest headlines..."):
            articles, error = fetch_news(
                api_key=api_key,
                country=selected_country,
                category=selected_category,
                keyword=keyword,
                page_size=article_count
            )

        if error:
            st.error(error)

        elif not articles:
            st.info("No articles found for the selected filters.")

        else:
            # Apply additional local filters
            filtered_articles = articles

            if show_only_with_images:
                filtered_articles = [
                    article for article in filtered_articles
                    if article.get("urlToImage")
                ]

            if show_only_with_description:
                filtered_articles = [
                    article for article in filtered_articles
                    if article.get("description")
                ]

            st.success(f"Found {len(filtered_articles)} articles")

            # Summary Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Country", selected_country_name)

            with col2:
                st.metric("Topic", selected_category.title())

            with col3:
                st.metric("Articles", len(filtered_articles))

            with col4:
                st.metric("Keyword", keyword if keyword else "None")

            st.divider()

            # Convert to DataFrame for table view
            table_data = []

            for article in filtered_articles:
                table_data.append({
                    "Title": article.get("title"),
                    "Source": article.get("source", {}).get("name"),
                    "Author": article.get("author"),
                    "Published At": format_date(article.get("publishedAt")),
                    "URL": article.get("url")
                })

            df = pd.DataFrame(table_data)

            tab1, tab2 = st.tabs(["📰 Article Cards", "📊 Table View"])

            # -------------------------------------------------
            # Article Card View
            # -------------------------------------------------
            with tab1:
                for index, article in enumerate(filtered_articles, start=1):
                    title = article.get("title", "No title available")
                    description = article.get("description", "No description available")
                    content = article.get("content")
                    source = article.get("source", {}).get("name", "Unknown Source")
                    author = article.get("author", "Unknown Author")
                    published_at = format_date(article.get("publishedAt"))
                    article_url = article.get("url")
                    image_url = article.get("urlToImage")

                    with st.container(border=True):
                        col_img, col_text = st.columns([1, 2])

                        with col_img:
                            if image_url:
                                st.image(image_url, use_container_width=True)
                            else:
                                st.info("No image available")

                        with col_text:
                            st.subheader(f"{index}. {title}")

                            st.write(f"**Source:** {source}")
                            st.write(f"**Author:** {author}")
                            st.write(f"**Published:** {published_at}")

                            st.write(description)

                            if content:
                                with st.expander("Read preview"):
                                    st.write(content)

                            if article_url:
                                st.link_button("Read Full Article", article_url)

            # -------------------------------------------------
            # Table View
            # -------------------------------------------------
            with tab2:
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download Results as CSV",
                    data=csv,
                    file_name="news_headlines.csv",
                    mime="text/csv"
                )

    else:
        st.info("Select filters from the sidebar and click **Fetch News**.")