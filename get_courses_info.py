from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
import csv
import re
from tqdm import tqdm
import time
from lxml import etree
from multiprocessing.pool import ThreadPool


START_CSV = "openedu_courses_base_info.csv"
OUT_CSV = "openedu_courses_full_info.csv"
GROUPS_CSV = 'openedu_groups_map.csv'
HEADERS_LANG = "en-US,en;q=0.8"


def make_session():
    ua = UserAgent()
    s = requests.Session()
    s.headers.update({
        "User-Agent": ua.random,
        "Accept-Language": HEADERS_LANG,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    return s


def read_input_urls(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def parse_weeks(text):
    text = text.split()
    if 'from' in text:
        return (int(text[1]), int(text[3]))
    return (int(text[0]), int(text[0]))


def parse_hours(text):
    text = text.split()
    if 'from' in text:
        return (int(text[1]), int(text[3]))
    return (int(text[1]), int(text[1]))


def parse_credits(text):
    return int(text.split()[0])


def parse_language(text):
    t = text.strip()
    languages = {
        "Russian language": "ru",
        "English language": "en"
    }
    return languages.get(t, "")


def parse_left_panel(soup):
    container = soup.find('div', class_='productDetails')
    fields = {}
    custom_fields = {}
    groups_dict = {}

    children = container.find_all(recursive=False)

    for child in children:
        field = child.find_all(recursive=False)

        if len(field) == 1:
            fields['intro'] = field[0].get_text()
            continue

        field_name = field[0].get('id')
        content = field[1]

        if field_name == 'directions':
            links = []

            for a in content.find_all('a'):
                group_id = int(a.get('href').split('=')[-1])
                links.append(group_id)
                descr = a.get_text()
                sep_idx = descr.index(' ')
                groups_dict.update({group_id: (descr[:sep_idx], descr[sep_idx+1:])})

            fields['directions'] = links
        elif re.match(r"custom_field\d+_body", field_name):
            custom_fields[field_name] = content.get_text()
        elif field_name == 'instructors':
            continue
        else:
            fields[field_name] = content.get_text()

    if custom_fields:
        fields['custom_info'] = custom_fields

    return fields, groups_dict


def parse_top_ul_info(soup):
    header = soup.find('h1', class_='product-page-module__qYqKqa__title')
    ul = header.find_next_sibling()
    lis = ul.find_all('li', recursive=False)
    info = {}

    for li in lis:
        text = li.get_text().strip()
        if 'week' in text and 'hour' not in text:
            wmin, wmax = parse_weeks(text)
            info["weeks_min"] = wmin
            info["weeks_max"] = wmax
        elif 'hour' in text:
            hmin, hmax = parse_hours(text)
            info["hours_min"] = hmin
            info["hours_max"] = hmax
        elif 'credit' in text:
            info["credit_units"] = parse_credits(text)
        elif 'language' in text:
            info["language"] = parse_language(text)
        elif 'certificate' in text:
            info["certificate"] = 1

    return info


def parse_course_page(session, url):
    r = session.get(url)
    html = r.text
    soup = BeautifulSoup(html, "lxml")

    try:
        left, groups = parse_left_panel(soup)
        top = parse_top_ul_info(soup)
    except:
        return parse_course_page(session, url)

    return {**top, **left}, groups


def collect_all_details_sequential(rows):
    s = make_session()
    results = []
    groups_results = {}
    for row in tqdm(rows):
        url = row.get("url")
        detail, groups = parse_course_page(s, url)
        all_info = {**row, **detail}
        results.append(all_info)
        groups_results.update(groups)
    return results, groups_results



def collect_all_details_parallel(rows):
    s = make_session()
    results = []
    groups_results = {}

    def fetch_detail(row):
        url = row["url"]
        detail, groups = parse_course_page(s, url)
        return ({**row, **detail}, groups)

    with ThreadPool(processes=10) as pool:
        for result, groups in tqdm(pool.imap(fetch_detail, rows), total=len(rows)):
            results.append(result)
            groups_results.update(groups)

    return results, groups_results


def print_fieldnames(rows, path):
    keys = set()
    for r in rows:
        keys.update(r.keys())
    keys = sorted(list(keys))
    print(keys)


def write_output(rows, path):
    keys = [
        'index', 'title', 'university', 'language', 'url', 'weeks_max', 'weeks_min', 
        'hours_min', 'hours_max', 'start_date', 'end_date', 'credit_units', 
        'certificate', 'competence', 'course_format', 'directions', 
        'intro', 'links', 'result_abilities', 'about', 'syllabus',
        'result_knowledge', 'result_skills', 'results', 'specifications', 'custom_info'
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            r = {k: v.replace('\n', '||') if isinstance(v, str) else v for k, v in r.items()}
            writer.writerow(r)


def write_groups(rows, path):
    keys = [
        'index', 'code', 'title'
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        rows = {key: rows[key] for key in sorted(rows)}
        for k, v in rows.items():
            res = {}
            res['index'] = k
            res['code'] = v[0]
            res['title'] = v[1]
            writer.writerow(res)


def main():
    rows = read_input_urls(START_CSV)
    details, groups_details = collect_all_details_parallel(rows)
    write_output(details, OUT_CSV)
    write_groups(groups_details, GROUPS_CSV)


if __name__ == "__main__":
    main()
