# 🔍 Scopus RecSys Explorer

An interactive Streamlit application for exploring and visualizing recommender systems algorithms and their applications in academic literature from Scopus.

## 🌟 Features

- **Statistics Dashboard**: View key metrics about algorithms and applications in the dataset
- **Interactive Heatmap**: Explore the relationships between algorithms and applications with adjustable occurrence thresholds
- **Algorithm Explorer**: Discover applications associated with specific algorithms through interactive word clouds
- **Application Explorer**: Find algorithms commonly used in specific application domains

## 🚀 Getting Started

### Prerequisites

- Python 3.6+
- pip (Python package installer)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/scopus-recsys.git
   cd scopus-recsys
   ```

2. Install the required dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application
   ```bash
   streamlit run streamlit_app.py
   ```

The application will open in your default web browser at `http://localhost:8501`.

## 📊 Data

The application uses a DuckDB database (`data/db.duckdb`) containing:
- Algorithm similarity metrics
- Application domain relationships
- Algorithm-Application occurrence links

## 🛠️ Tech Stack

- **Streamlit**: Web application framework
- **DuckDB**: Database engine
- **Pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **WordCloud**: Text visualization

## 📝 License

This project is licensed under the Apache License - see the LICENSE file for details.
