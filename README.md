# OpenEdu Courses Scraper

<img 
    src="https://github.com/user-attachments/assets/9e227c79-5792-43f6-bb5e-d31e64fb5f16" 
    width="40%" 
    height="40%" 
    alt="openedu-black" 
    style="display: block; margin: auto;" 
/>

A web-scraping pipeline that collects structured course information from the Russian educational platform OpenEdu.ru using a combination of Selenium with geckodriver (for dynamic pagination), Requests + BeautifulSoup (for detailed page parsing), and lightweight parallelization. The dataset with the parsing results is saved on Kaggle.

## Data Collected

- `openedu_courses_base_info.csv` - main fields from the course card: `index`, `title`, `url`, `university`, etc.  
- `openedu_courses_full_info.csv` - detailed information from the course page: `language`, `certificate`, `intro`, `directions`, `custom_info`, etc.  
- `openedu_groups_map.csv` - dictionary of educational fields: `index`,  `code`, `title`.  
- All text fields are normalized (new lines replaced with `||`) for CSV export.

## Tools Used

- Selenium (geckodriver + Firefox) — for scrolling and obtaining the complete list of courses with dynamic loading.  
- Requests + BeautifulSoup (lxml parser) — for detailed extraction of fields from individual course pages.  
- fake_useragent — for randomizing the User-Agent during requests.  
- ThreadPool / tqdm — for parallel page loading and progress indication. 

## Repository Structure

- `scrap_courses_list.py` — Selenium script to collect the basic list of courses (index, title, url, university, start/end).  
- `get_courses_info.py` — parser for course cards (Requests + BeautifulSoup), collects detailed fields and forms two CSVs.
