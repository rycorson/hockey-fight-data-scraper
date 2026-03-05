import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import gspread
from playwright.sync_api import sync_playwright

load_dotenv()

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

# First time Run
#target_start_date = datetime.strptime("2025-10-7", "%Y-%m-%d")

# Run this every Monday morning/ Sunday night, setup Task Scheduler to automate
target_start_date = datetime.now() - timedelta(days=7)

def scrape_and_calculate_points(stop_date):
    fantasy_fight_tracker = {}
    page_num = 1
    keep_scraping = True
    
    master_fight_memory = set()

    print(f"Scraping backwards until we hit {stop_date.date()}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page_num = 1

        while keep_scraping:
            url = f"https://www.hockeyfights.com/fightlog/1/reg2026/{page_num}"
            print(f"Checking page {page_num}...")

            try:
                page.goto(url, timeout=90000, wait_until="domcontentloaded")
                
                page.locator("text=voted winner").first.wait_for(timeout=60000)
                
                page.keyboard.press("End")
                
                page.wait_for_timeout(3000)

                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')

                all_tags = soup.find_all(['div', 'li', 'article', 'tr'])
                fights_found_this_page = 0

                for tag in all_tags:
                    text = tag.get_text(" ", strip=True)
                    
                    if "Post Season" in text or "Fight Logs" in text or "Login" in text:
                        continue
                    
                    if len(text) > 15000: 
                        continue

                    if "voted winner" not in text.lower() or "vs" not in text.lower():
                        continue
                        
                    date_match = re.search(r"(\d{2}/\d{2}/\d{2})", text)
                    if not date_match:
                        continue
                        
                    raw_date = date_match.group(1)
                    fight_date_obj = datetime.strptime(raw_date, "%m/%d/%y")
                    
                    if fight_date_obj < stop_date:
                        continue
                        
                    fight_date = fight_date_obj.strftime("%Y-%m-%d")
                    
                    match_split = re.split(r"voted winner", text, flags=re.IGNORECASE)
                    if len(match_split) < 2:
                        continue
                        
                    match_text = match_split[0]
                    match_text = re.sub(r"\d{2}/\d{2}/\d{2}", "", match_text).strip()
                    
                    fighters = re.split(r"\s+vs\.?\s+", match_text, flags=re.IGNORECASE)
                    if len(fighters) != 2:
                        continue
                        
                    fighter1 = re.sub(r"^[^\w]*", "", fighters[0]).strip()
                    fighter2 = re.sub(r"^[^\w]*", "", fighters[1]).strip()
                    
                    if ")" in fighter1:
                        fighter1 = fighter1[:fighter1.find(")")+1]
                    if ")" in fighter2:
                        fighter2 = fighter2[:fighter2.find(")")+1]
                    
                    winner_match = re.search(r":\s*(.*?)\s*\((\d+)%\)", match_split[1])
                    if not winner_match:
                        continue
                        
                    voted_winner_text = winner_match.group(1).strip()
                    vote_percent = int(winner_match.group(2))
                    
                    sorted_fighters = sorted([fighter1, fighter2])
                    fight_id = f"{fight_date}_{sorted_fighters[0]}_{sorted_fighters[1]}"
                    
                    if fight_id in master_fight_memory:
                        continue
                        
                    master_fight_memory.add(fight_id)
                    fights_found_this_page += 1
                    
                    if fight_date not in fantasy_fight_tracker:
                        fantasy_fight_tracker[fight_date] = {}
                        
                    for player_name in [fighter1, fighter2]:
                        current_score = fantasy_fight_tracker[fight_date].get(player_name, 0)
                        points_to_add = 1
                        
                        end_index = player_name.rfind(" (")
                        if end_index > 0:
                            name_part = player_name[:end_index].strip()
                            last_name_only = name_part.split()[-1]
                            
                            if vote_percent > 50 and (voted_winner_text in last_name_only or last_name_only in voted_winner_text):
                                points_to_add += 1
                                
                        fantasy_fight_tracker[fight_date][player_name] = current_score + points_to_add

                if fights_found_this_page == 0:
                    print(f"No new valid fights found. Target date {stop_date.date()} reached. Ending scrape.")
                    break

                page_num += 1

            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                break

        browser.close()

    return fantasy_fight_tracker
    
def export_to_google_sheets(data):
    if not data:
        print("\nNo valid data was found to export.")
        return
    
    try:
        print("\nConnecting to Google Sheets...")
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open(GOOGLE_SHEET_NAME)
        worksheet = sh.sheet1

        existing_data = worksheet.get_all_values()

        saved_records = {}
        row_index = 2

        for row in existing_data[1:]:
            if len(row) >= 3:
                key = f"{row[0]}-{row[1]}"
                try:
                    saved_records[key] = {
                        "row_number": row_index,
                        "score": int(row[2])
                    }
                except ValueError:
                    pass
            row_index += 1
            
        rows_to_append = []
        cells_to_update = []

        for date, players in data.items():
            for player, scraped_score in players.items():
                key = f"{date}-{player}"

                if key in saved_records:
                    existing_score = saved_records[key]["score"]

                    if scraped_score > existing_score:
                        row_number = saved_records[key]["row_number"]
                        cells_to_update.append(
                            gspread.Cell(row=row_number, col=3, value=scraped_score)
                        )
                else:
                    rows_to_append.append([date, player, scraped_score])

        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            print(f"Updated {len(cells_to_update)} existing records with higher scores.")
        else:
            print("No existing records required score updates.")

        if rows_to_append:
            worksheet.append_rows(rows_to_append)
            print(f"Added {len(rows_to_append)} brand new records.")
        else:
            print("Checked the site, but there are no new fights to append")

    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")

if __name__ == "__main__":
    print("FIGHT SCRAPER INITIATED")
    fight_data = scrape_and_calculate_points(target_start_date)
    export_to_google_sheets(fight_data)
    print("PROCESS COMPLETE")