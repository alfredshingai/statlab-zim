# StatLab Zim

StatLab Zim is a web application for learning and applying basic statistics.
It allows users to upload a CSV dataset, explore its structure, run descriptive
analyses, visualize distributions and relationships, and perform common
statistical tests.

## Features (Version 1)

- Upload and preview CSV datasets.
- Dataset overview: rows, columns, data types, missing values.
- Descriptive statistics for numeric and categorical variables.
- Basic visualizations (histograms, boxplots, scatter plots, etc.).
- Core statistical tests with plain-language interpretations.
- Export results as CSV.

## Tech stack

- Python 3.12
- Streamlit
- pandas, numpy, scipy, statsmodels, matplotlib, seaborn

## Installation

1. Clone the repository:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd statlab-zim
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Open the app in your browser (usually http://localhost:8501).
2. Upload a CSV file.
3. Explore the dataset using the sidebar navigation.

## License

MIT
