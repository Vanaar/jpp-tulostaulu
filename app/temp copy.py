import requests
from bs4 import BeautifulSoup

def is_valid_match_number(match):
    # Match number must be an int (5 digits long)
    return match and match.isdigit() and len(match) == 5

def extract_period_data(soup, period_arrays):
    period_divs = soup.select(".online-match-live-container .period")
    current_period = 0

    for period_div in period_divs:
        period_class = period_div["class"]
        period_num = int(period_class[1].split("-")[1])

        if period_num == 0 or f"period-0-home" in period_arrays:
            if period_num > current_period:
                current_period = period_num

            home_div = period_div.select_one(".innings.home.d-flex")
            away_div = period_div.select_one(".innings.away.d-flex")

            home_elements = home_div.select("a, div")
            away_elements = away_div.select("a, div")

            for element in home_elements:
                value = int(element.get_text(strip=True)) if element.get_text(strip=True).isdigit() else 0
                period_arrays[f"period-{period_num}-home"].append(value)

            for element in away_elements:
                value = int(element.get_text(strip=True)) if element.get_text(strip=True).isdigit() else 0
                period_arrays[f"period-{period_num}-away"].append(value)

    if "period-0-home" in period_arrays and period_arrays["period-0-home"]:
        period_arrays["period-0-home-score"].append(period_arrays["period-0-home"][-1])
        period_arrays["period-0-away-score"].append(period_arrays["period-0-away"][-1])

    return period_arrays

def get_current_inning(soup):
    current_inning_div = soup.select_one(".text-muted font-weight-bold text-center")
    return current_inning_div.get_text(strip=True) if current_inning_div else None

def get_current_batting_team(soup):
    batting_team = None
    team_types = ["home", "away"]

    for team_type in team_types:
        batter = soup.select_one(f".innings.{team_type}.d-flex .bg-orange")
        if batter:
            batting_team = team_type
            break

    return batting_team

def get_current_period(soup):
    period_divs = soup.select(".online-match-live-container .period")

    for period_div in period_divs:
        batter = period_div.select_one(".bg-orange")
        if batter:
            period_num = int(period_div["class"][1].split("-")[1]) + 1
            return period_num

    return None

def extract_periods_won(soup):
    home_periods_won = None
    away_periods_won = None

    period_total_div = soup.select_one(".period.period-total")
    if period_total_div:
        home_periods_won_div = period_total_div.select_one(".innings.home.p-1")
        away_periods_won_div = period_total_div.select_one(".innings.away.p-1")

        if home_periods_won_div and away_periods_won_div:
            home_periods_won = int(home_periods_won_div.get_text(strip=True))
            away_periods_won = int(away_periods_won_div.get_text(strip=True))

    return {
        "home_periods_won": home_periods_won,
        "away_periods_won": away_periods_won
    }

def extract_outs(soup):
    outs_div = soup.select_one(".out.text-danger")
    return outs_div.get_text(strip=True) if outs_div else ""

def extract_team_names(soup):
    home_team_name = soup.select_one(".match-detail-team:nth-of-type(1) a:nth-of-type(2)")
    away_team_name = soup.select_one(".match-detail-team:nth-of-type(2) a:nth-of-type(1)")

    home_team_name = home_team_name.get_text(strip=True) if home_team_name else "Unknown"
    away_team_name = away_team_name.get_text(strip=True) if away_team_name else "Unknown"

    return {"home_team": home_team_name, "away_team": away_team_name}


def process_match(match, display, refresh):
    url = f"https://www.pesistulokset.fi/ottelut/{match}#live"
    print(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        period_arrays = extract_period_data(soup, {
            "period-0-home": [],
            "period-0-home-score": [],
            "period-0-away": [],
            "period-0-away-score": [],
            "period-1-home": [],
            "period-1-home-score": [],
            "period-1-away": [],
            "period-1-away-score": [],
            "period-2-home": [],
            "period-2-away": [],
            "period-3-home": [],
            "period-3-away": [],
        })
        periods_won = extract_periods_won(soup)
        outs = extract_outs(soup)
        current_batting_team = get_current_batting_team(soup)
        current_period = get_current_period(soup)
        current_inning = get_current_inning(soup)
        team_names = extract_team_names(soup)

        print(team_names)
        print (period_arrays)

        if display == 1 or display == 'junnu':
            display_data_as_table_junnu(period_arrays, periods_won, current_period, current_inning, team_names, current_batting_team, outs, refresh)
        elif display == 2 or display == 'text':
            display_data_as_text(period_arrays, periods_won, outs, current_batting_team, current_period, current_inning, team_names)
        else:
            # Print the full table
            display_data_as_table_full(period_arrays, periods_won, current_period, current_inning, team_names, current_batting_team, outs, refresh)
    except requests.RequestException as e:
        print("Error:", e)

def display_data_as_text(period_arrays, periods_won, outs, current_batting_team, current_period, current_inning, team_names):
    print("Koti:", team_names['home_team'])
    print("Vieras:", team_names['away_team'])
    print()
    for period_name, period_data in period_arrays.items():
        print(f"{period_name}: {' - '.join(map(str, period_data))}")

    if periods_won["home_periods_won"] is not None:
        print("Home score:", periods_won["home_periods_won"])

    if periods_won["away_periods_won"] is not None:
        print("Away score:", periods_won["away_periods_won"])

    if current_batting_team is not None:
        print("Batting team:", current_batting_team)
    else:
        print("Batting team: NA")

    print("Current period:", current_period)
    print("Current inning:", current_inning)
    print("Current Outs:", outs if outs else "0")

def display_data_as_table_full(period_arrays, periods_won, current_period, current_inning, team_names, current_batting_team, outs, refresh):
    # Format the table and print here
    pass

def display_data_as_table_junnu(period_arrays, periods_won, current_period, current_inning, team_names, current_batting_team, outs, refresh):
    # Format the table and print here
    pass

match = input("Enter match number: ")
display = input("Enter display option (1 for junior, 2 for text, any other key for full table): ")
refresh = input("Enter refresh rate (default is 10 seconds): ")

if is_valid_match_number(match):
    process_match(match, display, refresh)
else:
    print("Invalid match number. Input a suitable number.")
