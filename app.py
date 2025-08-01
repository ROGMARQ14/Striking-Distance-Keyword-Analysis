import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import plotly.express as px
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Page configuration
st.set_page_config(
    page_title="Striking Distance Keyword Report",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: 600;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'crawl_data' not in st.session_state:
    st.session_state.crawl_data = None
if 'keyword_data' not in st.session_state:
    st.session_state.keyword_data = None
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False

# Helper functions
def extract_domain(url):
    """Extract domain from URL"""
    parsed = urlparse(url)
    return parsed.netloc

def crawl_url(url, timeout=10):
    """Crawl a single URL and extract SEO elements"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else ''
        
        # Extract H1s
        h1_tags = soup.find_all('h1')
        h1_text = ' '.join([h1.text.strip() for h1 in h1_tags])
        
        # Extract main content (simplified approach)
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text from body
        body = soup.find('body')
        if body:
            content = body.get_text(separator=' ', strip=True)
            # Clean up excessive whitespace
            content = ' '.join(content.split())
        else:
            content = ''
        
        return {
            'url': url,
            'title': title,
            'h1': h1_text,
            'content': content[:5000],  # Limit content length
            'status': 'success'
        }
    
    except requests.RequestException as e:
        return {
            'url': url,
            'title': '',
            'h1': '',
            'content': '',
            'status': f'error: {str(e)}'
        }

def check_keyword_presence(keyword, text):
    """Check if keyword is present in text (case-insensitive)"""
    if not text or not keyword:
        return False
    return keyword.lower() in text.lower()

def calculate_striking_distance_opportunities(df):
    """Calculate opportunities based on keyword positions and optimization status"""
    opportunities = []
    
    for idx, row in df.iterrows():
        score = 0
        recommendations = []
        
        # Position-based scoring
        position = row['position']
        if 3 <= position <= 5:
            score += 30
            recommendations.append("Very close to top 3 - high priority")
        elif 6 <= position <= 10:
            score += 20
            recommendations.append("On page 1 - good opportunity")
        elif 11 <= position <= 20:
            score += 10
            recommendations.append("On page 2 - worth optimizing")
        
        # Check optimization gaps
        if not row['in_title']:
            score += 15
            recommendations.append("Add keyword to title tag")
        if not row['in_h1']:
            score += 10
            recommendations.append("Add keyword to H1 tag")
        if not row['in_content']:
            score += 5
            recommendations.append("Include keyword naturally in content")
        
        # Search volume impact
        if row.get('impressions', 0) > 1000:
            score += 10
            recommendations.append("High search volume keyword")
        
        opportunities.append({
            'url': row['url'],
            'keyword': row['keyword'],
            'position': row['position'],
            'opportunity_score': score,
            'recommendations': ' | '.join(recommendations)
        })
    
    return pd.DataFrame(opportunities)

def generate_excel_report(striking_distance_df, all_checks_passed_df, 
                         blocklist_removed_df, urls_not_found_df, all_data_df):
    """Generate Excel report with multiple sheets"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write each dataframe to a separate sheet
        striking_distance_df.to_excel(writer, sheet_name='Striking Distance', index=False)
        all_checks_passed_df.to_excel(writer, sheet_name='All Checks Passed', index=False)
        blocklist_removed_df.to_excel(writer, sheet_name='Keywords Blocked', index=False)
        urls_not_found_df.to_excel(writer, sheet_name='URLs Not Found', index=False)
        all_data_df.to_excel(writer, sheet_name='All Keyword Data', index=False)
        
        # Format the Excel file
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Format each worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)  # Freeze header row
            
            # Auto-fit columns (approximate)
            for i, col in enumerate(striking_distance_df.columns):
                column_width = max(len(str(col)), 15)
                worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    return output

# Main app
def main():
    st.markdown('<h1 class="main-header">🎯 Striking Distance Keyword Report</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Find and optimize keywords ranking in positions 3-20 for quick SEO wins</p>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("1. Upload Keyword Data")
        data_source = st.radio(
            "Select data source:",
            ["Google Search Console Export", "Ahrefs/SEMrush Export", "Sample Data"]
        )
        
        if data_source == "Sample Data":
            if st.button("Load Sample Data"):
                # Generate sample data
                sample_data = pd.DataFrame({
                    'url': [
                        'https://example.com/page1',
                        'https://example.com/page2',
                        'https://example.com/page3',
                        'https://example.com/page4',
                        'https://example.com/page5'
                    ] * 4,
                    'keyword': [
                        'best running shoes', 'running shoes review', 'marathon training tips',
                        'beginner running guide', 'running shoe brands'
                    ] * 4,
                    'position': [4, 7, 12, 15, 8, 5, 9, 18, 3, 11, 6, 14, 19, 4, 10, 13, 16, 5, 9, 20],
                    'impressions': [1200, 800, 500, 300, 1500] * 4,
                    'clicks': [45, 20, 10, 5, 55] * 4,
                    'ctr': [3.75, 2.5, 2.0, 1.67, 3.67] * 4
                })
                st.session_state.keyword_data = sample_data
                st.success("Sample data loaded!")
        else:
            uploaded_file = st.file_uploader(
                "Upload CSV file",
                type=['csv'],
                help="File should contain: url, keyword, position, impressions, clicks"
            )
            
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    required_cols = ['url', 'keyword', 'position']
                    if all(col in df.columns for col in required_cols):
                        st.session_state.keyword_data = df
                        st.success(f"Loaded {len(df)} keywords from {len(df['url'].unique())} URLs")
                    else:
                        st.error(f"Missing required columns. Found: {list(df.columns)}")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        st.divider()
        
        st.subheader("2. Crawl Settings")
        crawl_option = st.radio(
            "Content extraction method:",
            ["Crawl URLs automatically", "Use sample content"]
        )
        
        max_urls = st.slider("Max URLs to crawl", 10, 100, 50)
        
        st.divider()
        
        st.subheader("3. Filters & Blocklist")
        
        position_range = st.slider(
            "Position range",
            min_value=1,
            max_value=50,
            value=(3, 20),
            help="Focus on keywords in striking distance"
        )
        
        blocklist_input = st.text_area(
            "Keyword blocklist (one per line)",
            placeholder="brand names\ncompetitor names\nnear me",
            help="Keywords containing these terms will be excluded"
        )
        
        min_impressions = st.number_input(
            "Minimum impressions",
            min_value=0,
            value=10,
            help="Filter out low-volume keywords"
        )
    
    # Main content area
    if st.session_state.keyword_data is not None:
        df = st.session_state.keyword_data.copy()
        
        # Display data overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Keywords", len(df))
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Unique URLs", df['url'].nunique())
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            striking_distance = len(df[(df['position'] >= position_range[0]) & 
                                     (df['position'] <= position_range[1])])
            st.metric("In Striking Distance", striking_distance)
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            avg_position = df['position'].mean()
            st.metric("Avg. Position", f"{avg_position:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Generate Report Button
        if st.button("🚀 Generate Striking Distance Report", type="primary"):
            with st.spinner("Processing your data..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Filter keywords
                status_text.text("Filtering keywords...")
                progress_bar.progress(20)
                
                # Apply position filter
                filtered_df = df[(df['position'] >= position_range[0]) & 
                               (df['position'] <= position_range[1])].copy()
                
                # Apply impressions filter
                if 'impressions' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['impressions'] >= min_impressions]
                
                # Apply blocklist
                blocklist_removed = []
                if blocklist_input:
                    blocklist = [term.strip().lower() for term in blocklist_input.split('\n') if term.strip()]
                    for term in blocklist:
                        removed = filtered_df[filtered_df['keyword'].str.lower().str.contains(term, na=False)]
                        blocklist_removed.extend(removed.to_dict('records'))
                        filtered_df = filtered_df[~filtered_df['keyword'].str.lower().str.contains(term, na=False)]
                
                # Step 2: Crawl URLs or use sample content
                status_text.text("Analyzing page content...")
                progress_bar.progress(40)
                
                unique_urls = filtered_df['url'].unique()[:max_urls]
                crawl_results = {}
                
                if crawl_option == "Use sample content":
                    # Generate sample content for demo
                    for url in unique_urls:
                        crawl_results[url] = {
                            'url': url,
                            'title': f"Sample Title for {url.split('/')[-1]}",
                            'h1': f"Sample H1 Header for {url.split('/')[-1]}",
                            'content': f"This is sample content for {url}. It contains various keywords and text.",
                            'status': 'success'
                        }
                else:
                    # Real crawling with progress
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_url = {executor.submit(crawl_url, url): url for url in unique_urls}
                        completed = 0
                        
                        for future in as_completed(future_to_url):
                            url = future_to_url[future]
                            try:
                                result = future.result()
                                crawl_results[url] = result
                            except Exception as e:
                                crawl_results[url] = {
                                    'url': url,
                                    'title': '',
                                    'h1': '',
                                    'content': '',
                                    'status': f'error: {str(e)}'
                                }
                            
                            completed += 1
                            progress = 40 + int((completed / len(unique_urls)) * 30)
                            progress_bar.progress(progress)
                
                # Step 3: Check keyword presence
                status_text.text("Checking keyword optimization...")
                progress_bar.progress(75)
                
                results = []
                urls_not_found = []
                
                for idx, row in filtered_df.iterrows():
                    url = row['url']
                    keyword = row['keyword']
                    
                    if url in crawl_results and crawl_results[url]['status'] == 'success':
                        crawl_data = crawl_results[url]
                        
                        in_title = check_keyword_presence(keyword, crawl_data['title'])
                        in_h1 = check_keyword_presence(keyword, crawl_data['h1'])
                        in_content = check_keyword_presence(keyword, crawl_data['content'])
                        
                        result = row.to_dict()
                        result.update({
                            'in_title': in_title,
                            'in_h1': in_h1,
                            'in_content': in_content,
                            'page_title': crawl_data['title'][:100],
                            'optimization_score': sum([in_title, in_h1, in_content])
                        })
                        results.append(result)
                    else:
                        urls_not_found.append({'url': url, 'keyword': keyword})
                
                # Step 4: Prepare final datasets
                status_text.text("Generating report...")
                progress_bar.progress(90)
                
                results_df = pd.DataFrame(results)
                
                # Separate fully optimized keywords
                if len(results_df) > 0:
                    all_checks_passed = results_df[
                        (results_df['in_title'] == True) & 
                        (results_df['in_h1'] == True) & 
                        (results_df['in_content'] == True)
                    ]
                    
                    striking_distance = results_df[
                        (results_df['in_title'] == False) | 
                        (results_df['in_h1'] == False) | 
                        (results_df['in_content'] == False)
                    ].sort_values('position')
                else:
                    all_checks_passed = pd.DataFrame()
                    striking_distance = pd.DataFrame()
                
                # Calculate opportunities
                if len(striking_distance) > 0:
                    opportunities_df = calculate_striking_distance_opportunities(striking_distance)
                    striking_distance = striking_distance.merge(
                        opportunities_df[['url', 'keyword', 'opportunity_score', 'recommendations']], 
                        on=['url', 'keyword'],
                        how='left'
                    )
                    striking_distance = striking_distance.sort_values('opportunity_score', ascending=False)
                
                # Store results in session state
                st.session_state.report_generated = True
                st.session_state.striking_distance = striking_distance
                st.session_state.all_checks_passed = all_checks_passed
                st.session_state.blocklist_removed = pd.DataFrame(blocklist_removed)
                st.session_state.urls_not_found = pd.DataFrame(urls_not_found)
                st.session_state.all_data = df
                
                progress_bar.progress(100)
                status_text.text("Report generated successfully!")
                time.sleep(1)
                status_text.empty()
                progress_bar.empty()
        
        # Display results if report is generated
        if st.session_state.report_generated:
            st.success("✅ Report generated successfully!")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Striking Distance Report", 
                "📈 Analytics", 
                "✅ Fully Optimized", 
                "ℹ️ Additional Info"
            ])
            
            with tab1:
                st.subheader("Keywords with Optimization Opportunities")
                
                if len(st.session_state.striking_distance) > 0:
                    # Display actionable keywords
                    st.dataframe(
                        st.session_state.striking_distance[[
                            'url', 'keyword', 'position', 'in_title', 'in_h1', 
                            'in_content', 'opportunity_score', 'recommendations'
                        ]],
                        use_container_width=True,
                        height=500
                    )
                    
                    # Download button
                    excel_file = generate_excel_report(
                        st.session_state.striking_distance,
                        st.session_state.all_checks_passed,
                        st.session_state.blocklist_removed,
                        st.session_state.urls_not_found,
                        st.session_state.all_data
                    )
                    
                    st.download_button(
                        label="📥 Download Full Excel Report",
                        data=excel_file,
                        file_name=f"striking_distance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No keywords found that need optimization in the selected range.")
            
            with tab2:
                st.subheader("Analytics Dashboard")
                
                if len(st.session_state.striking_distance) > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Position distribution
                        fig_pos = px.histogram(
                            st.session_state.striking_distance, 
                            x='position',
                            title="Position Distribution",
                            nbins=20,
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig_pos.update_layout(height=400)
                        st.plotly_chart(fig_pos, use_container_width=True)
                    
                    with col2:
                        # Optimization status
                        optimization_data = pd.DataFrame({
                            'Status': ['Missing in Title', 'Missing in H1', 'Missing in Content'],
                            'Count': [
                                len(st.session_state.striking_distance[~st.session_state.striking_distance['in_title']]),
                                len(st.session_state.striking_distance[~st.session_state.striking_distance['in_h1']]),
                                len(st.session_state.striking_distance[~st.session_state.striking_distance['in_content']])
                            ]
                        })
                        
                        fig_opt = px.bar(
                            optimization_data,
                            x='Status',
                            y='Count',
                            title="Optimization Gaps",
                            color_discrete_sequence=['#ff7f0e']
                        )
                        fig_opt.update_layout(height=400)
                        st.plotly_chart(fig_opt, use_container_width=True)
                    
                    # Top opportunities table
                    st.subheader("Top 10 Optimization Opportunities")
                    top_opportunities = st.session_state.striking_distance.nlargest(10, 'opportunity_score')
                    st.dataframe(
                        top_opportunities[['url', 'keyword', 'position', 'opportunity_score', 'recommendations']],
                        use_container_width=True
                    )
            
            with tab3:
                st.subheader("Keywords with All Optimizations Complete")
                st.markdown('<div class="info-box">These keywords are already well-optimized and may not need immediate attention.</div>', unsafe_allow_html=True)
                
                if len(st.session_state.all_checks_passed) > 0:
                    st.dataframe(
                        st.session_state.all_checks_passed[['url', 'keyword', 'position']],
                        use_container_width=True
                    )
                else:
                    st.info("No keywords found with all optimizations complete.")
            
            with tab4:
                st.subheader("Additional Information")
                
                # Blocked keywords
                if len(st.session_state.blocklist_removed) > 0:
                    st.markdown("**Keywords Removed by Blocklist:**")
                    st.dataframe(st.session_state.blocklist_removed[['keyword', 'position']], use_container_width=True)
                
                # URLs not found
                if len(st.session_state.urls_not_found) > 0:
                    st.markdown("**URLs Not Found in Crawl:**")
                    st.dataframe(st.session_state.urls_not_found, use_container_width=True)
    
    else:
        # Welcome message when no data is loaded
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        ### 👋 Welcome to the Striking Distance Keyword Report Tool!
        
        This tool helps you identify and optimize keywords that are close to ranking in top positions (3-20).
        
        **To get started:**
        1. Upload your keyword data from Google Search Console or SEO tools
        2. Configure your crawl settings and filters
        3. Generate your report to find optimization opportunities
        
        **What you'll get:**
        - Keywords that need optimization in title tags, H1s, or content
        - Opportunity scores to prioritize your efforts
        - Actionable recommendations for each keyword
        - Comprehensive Excel report with multiple worksheets
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Built with ❤️ using Streamlit | Inspired by Lee Foot's Striking Distance Report
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
