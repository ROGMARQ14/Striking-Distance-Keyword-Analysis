# Striking Distance Keyword Report Tool

A Streamlit application that identifies and analyzes keywords ranking in positions 3-20 (striking distance) to help prioritize SEO optimization efforts.

## Features

- **Keyword Analysis**: Identifies keywords in striking distance (positions 3-20)
- **Content Optimization Check**: Verifies if keywords appear in:
  - Page titles
  - H1 tags
  - Page content
- **Opportunity Scoring**: Prioritizes keywords based on optimization potential
- **Multi-Sheet Excel Export**: Comprehensive reports with:
  - Main striking distance report
  - Fully optimized keywords
  - Blocked keywords
  - URLs not found
  - Raw keyword data
- **Interactive Analytics**: Visual dashboards showing position distribution and optimization gaps
- **Flexible Data Sources**: Supports Google Search Console, Ahrefs, SEMrush exports

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd striking-distance-report
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

## Deployment on Streamlit Cloud

1. **Fork or upload this repository to GitHub**

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"**

4. **Connect your GitHub account and select:**
   - Repository: Your forked/uploaded repo
   - Branch: main
   - Main file path: app.py

5. **Click "Deploy"**

The app will be automatically deployed and you'll get a public URL.

## Usage

### 1. Upload Keyword Data

The tool accepts CSV files with the following columns:
- `url` (required): The page URL
- `keyword` (required): The search keyword
- `position` (required): Current ranking position
- `impressions` (optional): Search impressions
- `clicks` (optional): Number of clicks
- `ctr` (optional): Click-through rate

### 2. Configure Settings

- **Position Range**: Default is 3-20 (striking distance)
- **Crawl Method**: Choose automatic crawling or use sample content
- **Blocklist**: Add keywords to exclude (e.g., brand names, competitors)
- **Minimum Impressions**: Filter out low-volume keywords

### 3. Generate Report

Click "Generate Striking Distance Report" to:
1. Filter keywords based on your criteria
2. Crawl URLs to extract SEO elements
3. Check keyword presence in titles, H1s, and content
4. Calculate opportunity scores
5. Generate downloadable Excel report

### 4. Review Results

- **Striking Distance Report**: Keywords needing optimization
- **Analytics**: Visual insights into your data
- **Fully Optimized**: Keywords already well-optimized
- **Additional Info**: Blocked keywords and crawl issues

## Input File Format

### Google Search Console Export
```csv
url,keyword,position,impressions,clicks,ctr
https://example.com/page1,best running shoes,5,1200,45,3.75
https://example.com/page2,running shoe reviews,8,800,20,2.50
```

### Ahrefs/SEMrush Format
The tool is flexible and will work with most CSV exports containing the required columns.

## Optimization Recommendations

The tool provides specific recommendations for each keyword:
- Add keyword to title tag
- Add keyword to H1 tag
- Include keyword naturally in content
- Priority based on current position
- High search volume indicators

## Performance Considerations

- **Crawling**: The tool crawls URLs in batches with concurrent requests
- **Rate Limiting**: Includes delays to avoid overwhelming target servers
- **Max URLs**: Configurable limit (default: 50) to manage processing time
- **Content Limits**: Analyzes first 5000 characters of page content

## Troubleshooting

### Common Issues

1. **"Missing required columns" error**
   - Ensure your CSV has `url`, `keyword`, and `position` columns
   - Column names are case-sensitive

2. **URLs not found in crawl**
   - Check if URLs are accessible
   - Verify no authentication is required
   - Some sites may block automated crawling

3. **Slow processing**
   - Reduce the number of URLs to crawl
   - Use sample content option for testing

## Advanced Configuration

### Environment Variables (for production)

Create a `.streamlit/secrets.toml` file for sensitive configurations:
```toml
[general]
max_concurrent_requests = 5
request_timeout = 10
user_agent = "Your Custom User Agent"
```

### Custom Blocklists

Create a text file with blocked terms (one per line) and upload through the UI:
```
competitor brand
near me
cheap
[your city]
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use this tool for your SEO projects.

## Credits

Inspired by Lee Foot's Striking Distance Keyword Report concept.
