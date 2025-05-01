import requests
import csv
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from iso3166 import countries_by_alpha2
import matplotlib.patheffects

# Define the API URLs and the API Key
url_layer7_source = "https://api.cloudflare.com/client/v4/radar/attacks/layer7/top/locations/origin?name=main&dateRange=28d&limit=10"
url_layer7_target = "https://api.cloudflare.com/client/v4/radar/attacks/layer7/top/locations/target?name=main&dateRange=28d&limit=10"
url_layer3_source = "https://api.cloudflare.com/client/v4/radar/attacks/layer3/top/locations/origin?name=main&dateRange=28d&limit=10"
url_layer3_target = "https://api.cloudflare.com/client/v4/radar/attacks/layer3/top/locations/target?name=main&dateRange=28d&limit=10"
api_key = "f-FRjM33GHBwji9Ss-gGc_otUKFH0mi3CUzJ-T7n"

# Set headers with the API Key for authorization
headers = {
    "Authorization": f"Bearer {api_key}"
}

def fetch_data(url):
    """Fetch data from Cloudflare API."""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Returning the raw JSON data
    else:
        print(f"Failed to fetch data from {url}, Status Code: {response.status_code}")
        return None

def write_to_csv(data, filename, is_target=False):
    """Write the data to a CSV file."""
    if not data:
        print(f"No data to write to {filename}")
        return
    
    # Check if the "result" key exists in the response
    if "result" not in data:
        print(f"Invalid data structure in response. Missing 'result' key.")
        return
    
    # Access the 'main' data under 'result'
    sorted_data = sorted(data["result"]["main"], key=lambda x: x.get("rank", float('inf')))
    
    # Open the CSV file in write mode
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write header (adjusted to the structure of the data returned)
        if is_target:
            writer.writerow(["CountryCode", "CountryName_target", "Value_target", "Rank_target"])
        else:
            writer.writerow(["CountryCode", "CountryName", "Value", "Rank"])

        # Write rows (adjust based on the actual structure of the API response)
        for item in sorted_data:
            # Extract values for country code and country name based on whether it's a target or not
            if is_target:
                country_code = item.get("targetCountryAlpha2", "N/A")
                country_name = item.get("targetCountryName", "N/A")
            else:
                country_code = item.get("originCountryAlpha2", "N/A")
                country_name = item.get("originCountryName", "N/A")
            
            value = item.get("value", "N/A")
            rank = item.get("rank", "N/A")
            writer.writerow([country_code, country_name, value, rank])

def create_comparison_graph(layer3_source, layer3_target, layer7_source, layer7_target):
    """Create a double bar graph comparing Layer 3 and Layer 7 data, aligning by country name."""
    
    def align_data_by_country(source_data, target_data):
        """Align source and target data by country name, filtering out invalid entries."""
        # Filter out entries with missing 'originCountryName' or 'value'
        source_dict = {
            item["originCountryName"]: float(item["value"])
            for item in source_data
            if item.get("originCountryName") and item.get("value") is not None
        }
        target_dict = {
            item["targetCountryName"]: float(item["value"])
            for item in target_data
            if item.get("targetCountryName") and item.get("value") is not None
        }
        
        # Get all unique countries in the order they appear in the source data (rank order)
        all_countries = list(source_dict.keys())  # Use source order
        # Add missing countries from the target data
        all_countries += [country for country in target_dict.keys() if country not in all_countries]
        
        # Prepare aligned lists of values
        source_values = [source_dict.get(country, 0) for country in all_countries]
        target_values = [target_dict.get(country, 0) for country in all_countries]
        
        return all_countries, source_values, target_values


    # Align Layer 3 data
    countries_layer3, values_layer3_source, values_layer3_target = align_data_by_country(layer3_source, layer3_target)
    
    # Align Layer 7 data
    countries_layer7, values_layer7_source, values_layer7_target = align_data_by_country(layer7_source, layer7_target)

    # Set up the bar chart positions
    x_layer3 = np.arange(len(countries_layer3))  # The label locations for Layer 3
    x_layer7 = np.arange(len(countries_layer7))  # The label locations for Layer 7
    
    # Bar width
    bar_width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))  # Create two subplots (Layer 3 and Layer 7)

    # Layer 3 bar chart
    ax1.bar(x_layer3 - bar_width / 2, values_layer3_source, bar_width, label='Source', color='blue')
    ax1.bar(x_layer3 + bar_width / 2, values_layer3_target, bar_width, label='Target', color='orange')

    ax1.set_xlabel('Countries')
    ax1.set_ylabel('Attack Value')
    ax1.set_title('Layer 3 Attacks (Source vs Target)')
    ax1.set_xticks(x_layer3)
    ax1.set_xticklabels(countries_layer3, rotation=90)
    ax1.legend()

    # Layer 7 bar chart
    ax2.bar(x_layer7 - bar_width / 2, values_layer7_source, bar_width, label='Source', color='blue')
    ax2.bar(x_layer7 + bar_width / 2, values_layer7_target, bar_width, label='Target', color='orange')

    ax2.set_xlabel('Countries')
    ax2.set_ylabel('Attack Value')
    ax2.set_title('Layer 7 Attacks (Source vs Target)')
    ax2.set_xticks(x_layer7)
    ax2.set_xticklabels(countries_layer7, rotation=90)
    ax2.legend()

    # Adjust layout
    plt.tight_layout()
    plt.show()

def plot_flagged_countries_on_map(flagged_country_codes):
    """Plot a professional world map with flagged countries filled and all country names and borders in black."""
    import matplotlib.patches as mpatches

    # Load world map from local shapefile
    world = gpd.read_file('C:\\CloudFlare Data\\naturalearth\\ne_110m_admin_0_countries.shp')
    alpha2_to_alpha3 = {c.alpha2: c.alpha3 for c in countries_by_alpha2.values()}
    flagged_alpha3 = set()
    for code in flagged_country_codes:
        if code in ('GB', 'IE'):
            continue  # Skip UK and Ireland
        if code in alpha2_to_alpha3:
            flagged_alpha3.add(alpha2_to_alpha3[code])

    world['flagged'] = world['ADM0_A3'].apply(lambda x: x in flagged_alpha3)

    # Prepare the figure
    fig, ax = plt.subplots(figsize=(20, 10), facecolor='white')
    fig.subplots_adjust(left=0.18, right=0.98, top=0.92, bottom=0.08)

    # Plot the map: flagged in muted red, others in light blue/gray, black borders
    world.plot(ax=ax,
               color=world['flagged'].map({True: '#c94c4c', False: '#c9d3db'}),
               edgecolor='black', linewidth=0.7, zorder=1)

    # Only label a small set of major countries/regions (like mapchart.net), abbreviate long names and adjust positions for clarity
    major_labels = [
        ("CANADA", -110, 60, 14),
        ("UNITED STATES", -100, 40, 14),
        ("MEXICO", -102, 23, 11),
        ("BRAZIL", -51, -10, 14),
        ("ARGENTINA", -64, -35, 11),
        ("GREENLAND", -42, 72, 11),
        ("RUSSIA", 100, 60, 14),
        ("CHINA", 105, 35, 14),
        ("INDIA", 80, 22, 11),
        ("AUSTRALIA", 135, -25, 14),
        ("SOUTH AFRICA", 24, -29, 11),
        ("SAUDI ARABIA", 50, 22, 9),  # moved east, smaller
        ("EGYPT", 36, 28, 9),         # moved east, smaller
        ("ALGERIA", 0, 32, 9),        # moved west, smaller
        ("UK", -2, 56, 8),            # moved north, smaller
        ("FRANCE", 2, 48, 9),         # moved north, smaller
        ("GERMANY", 15, 53, 8),       # moved east/north, smaller
        ("SPAIN", -4, 42, 9),         # moved north, smaller
        ("TURKEY", 37, 41, 9),        # moved east/north, smaller
        ("IRAN", 56, 34, 9),          # moved east/north, smaller
        ("JAPAN", 138, 39, 11),       # moved north
        ("INDONESIA", 120, -2, 9),    # moved north, smaller
        ("NEW ZEALAND", 174, -39, 11),
        ("NIGERIA", 8, 13, 9),        # moved north, smaller
        ("ETHIOPIA", 39, 13, 9),      # moved north, smaller
        ("DR CONGO", 27, -2, 8),      # moved north, smaller
        ("CAR", 25, 11, 7),           # moved north, smaller
    ]

    # Mapping from shapefile names to label names (add more as needed)
    name_map = {
        "UNITED STATES OF AMERICA": "UNITED STATES",
        "KOREA, REPUBLIC OF": "SOUTH KOREA",
        "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "NORTH KOREA",
        "CONGO, DEMOCRATIC REPUBLIC OF THE": "DR CONGO",
        "CENTRAL AFRICAN REPUBLIC": "CAR",
        "UNITED KINGDOM": "UK",
        "RUSSIAN FEDERATION": "RUSSIA",
        "CZECH REPUBLIC": "CZECHIA",
        "SYRIAN ARAB REPUBLIC": "SYRIA",
        "IRAN (ISLAMIC REPUBLIC OF)": "IRAN",
        "VIET NAM": "VIETNAM",
        "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "LAOS",
        "BOLIVARIAN REPUBLIC OF VENEZUELA": "VENEZUELA",
        "BOSNIA AND HERZEGOVINA": "BOSNIA",
        "MYANMAR": "MYANMAR",
        "CÔTE D'IVOIRE": "IVORY COAST",
        "SWAZILAND": "ESWATINI",
        "TANZANIA, UNITED REPUBLIC OF": "TANZANIA",
        "BOLIVIA (PLURINATIONAL STATE OF)": "BOLIVIA",
        "MOLDOVA, REPUBLIC OF": "MOLDOVA",
        "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF": "NORTH MACEDONIA",
        "PALESTINE, STATE OF": "PALESTINE",
        "BRUNEI DARUSSALAM": "BRUNEI",
        "SAINT KITTS AND NEVIS": "ST KITTS & NEVIS",
        "SAINT LUCIA": "ST LUCIA",
        "SAINT VINCENT AND THE GRENADINES": "ST VINCENT & GRENADINES",
        "TRINIDAD AND TOBAGO": "TRINIDAD & TOBAGO",
        "ANTIGUA AND BARBUDA": "ANTIGUA & BARBUDA",
        "BAHAMAS": "BAHAMAS",
        "GAMBIA": "GAMBIA",
        "EAST TIMOR": "TIMOR-LESTE",
        "SÃO TOMÉ AND PRÍNCIPE": "SAO TOME & PRINCIPE",
        "MICRONESIA, FEDERATED STATES OF": "MICRONESIA",
        "MARSHALL ISLANDS": "MARSHALL ISLANDS",
        "SOLOMON ISLANDS": "SOLOMON ISLANDS",
        "VATICAN CITY": "VATICAN CITY",
        "HOLY SEE": "VATICAN CITY",
        "SAINT PIERRE AND MIQUELON": "ST PIERRE & MIQUELON",
        "SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA": "ST HELENA",
        "SAINT BARTHELEMY": "ST BARTHELEMY",
        "SAINT MARTIN (FRENCH PART)": "ST MARTIN",
        "SINT MAARTEN (DUTCH PART)": "SINT MAARTEN",
        "NETHERLANDS": "NETHERLANDS",
        "SWITZERLAND": "SWITZERLAND",
        "CYPRUS": "CYPRUS",
        "MALAYSIA": "MALAYSIA",
        "JAPAN": "JAPAN",
        "FRANCE": "FRANCE",
        "GERMANY": "GERMANY",
        "SPAIN": "SPAIN",
        "TURKEY": "TURKEY",
        "INDIA": "INDIA",
        "CHINA": "CHINA",
        "ARGENTINA": "ARGENTINA",
        "BRAZIL": "BRAZIL",
        "CANADA": "CANADA",
        "AUSTRALIA": "AUSTRALIA",
        "NEW ZEALAND": "NEW ZEALAND",
        "MEXICO": "MEXICO",
        "NIGERIA": "NIGERIA",
        "ETHIOPIA": "ETHIOPIA",
        "SAUDI ARABIA": "SAUDI ARABIA",
        "EGYPT": "EGYPT",
        "ALGERIA": "ALGERIA",
        "SOUTH AFRICA": "SOUTH AFRICA",
    }

    # --- Expanded hand-tuned overrides for crowded/overlapping countries ---
    crowded_overrides = {
        # Europe
        "NETHERLANDS": {"x": 2, "y": 54, "fontsize": 5, "label": "NETH."},
        "SWITZERLAND": {"x": 11, "y": 47, "fontsize": 5, "label": "SWITZ."},
        "UK": {"x": -5, "y": 57, "fontsize": 5, "label": "UK"},
        "GERMANY": {"x": 16, "y": 52.5, "fontsize": 5, "label": "GER."},
        "FRANCE": {"x": -3, "y": 47, "fontsize": 5, "label": "FR."},
        "SPAIN": {"x": -8, "y": 41, "fontsize": 5, "label": "SPAIN"},
        "ITALY": {"x": 15, "y": 44.5, "fontsize": 5, "label": "ITALY"},
        "POLAND": {"x": 22, "y": 52, "fontsize": 5, "label": "POL."},
        "BELGIUM": {"x": 4.5, "y": 51, "fontsize": 5, "label": "BELG."},
        "LUXEMBOURG": {"x": 6, "y": 49.7, "fontsize": 5, "label": "LUX."},
        "DENMARK": {"x": 10, "y": 56, "fontsize": 5, "label": "DEN."},
        "CZECHIA": {"x": 15, "y": 49.8, "fontsize": 5, "label": "CZECH."},
        "SLOVAKIA": {"x": 19, "y": 48.7, "fontsize": 5, "label": "SVK."},
        "HUNGARY": {"x": 19, "y": 47, "fontsize": 5, "label": "HUN."},
        "AUSTRIA": {"x": 14, "y": 47.5, "fontsize": 5, "label": "AUS."},
        "SLOVENIA": {"x": 15, "y": 46.2, "fontsize": 5, "label": "SLOV."},
        "CROATIA": {"x": 16, "y": 45.5, "fontsize": 5, "label": "CRO."},
        "BOSNIA": {"x": 18, "y": 44.5, "fontsize": 5, "label": "BIH."},
        "SERBIA": {"x": 21, "y": 44, "fontsize": 5, "label": "SRB."},
        "MONTENEGRO": {"x": 19, "y": 42.7, "fontsize": 5, "label": "MNE."},
        "ALBANIA": {"x": 20, "y": 41, "fontsize": 5, "label": "ALB."},
        "MACEDONIA": {"x": 21.5, "y": 41.6, "fontsize": 5, "label": "MKD."},
        "GREECE": {"x": 22, "y": 39, "fontsize": 5, "label": "GRC."},
        "PORTUGAL": {"x": -8, "y": 39.5, "fontsize": 5, "label": "PORT."},
        "IRELAND": {"x": -8, "y": 53, "fontsize": 5, "label": "IRE."},
        # SE Asia
        "SOUTH KOREA": {"x": 130, "y": 36, "fontsize": 5, "label": "S. KOREA"},
        "NORTH KOREA": {"x": 127, "y": 40, "fontsize": 5, "label": "N. KOREA"},
        "JAPAN": {"x": 140, "y": 38, "fontsize": 6, "label": "JAPAN"},
        "MALAYSIA": {"x": 104, "y": 2, "fontsize": 5, "label": "MALAY."},
        "VIETNAM": {"x": 108, "y": 15, "fontsize": 5, "label": "VIET."},
        "SINGAPORE": {"x": 104, "y": 1.3, "fontsize": 5, "label": "SGP."},
        "PHILIPPINES": {"x": 122, "y": 12, "fontsize": 5, "label": "PHIL."},
        "THAILAND": {"x": 101, "y": 15, "fontsize": 5, "label": "THAI."},
        "INDONESIA": {"x": 120, "y": -2, "fontsize": 5, "label": "INDO."},
        # Middle East
        "CYPRUS": {"x": 33, "y": 34, "fontsize": 5, "label": "CYPRUS"},
        "ISRAEL": {"x": 35, "y": 31, "fontsize": 5, "label": "ISR."},
        "LEBANON": {"x": 36, "y": 34, "fontsize": 5, "label": "LEB."},
        "JORDAN": {"x": 36, "y": 31, "fontsize": 5, "label": "JOR."},
        # Africa (examples)
        "DJIBOUTI": {"x": 43, "y": 12, "fontsize": 5, "label": "DJI."},
        "RWANDA": {"x": 30, "y": -2, "fontsize": 5, "label": "RWA."},
        "BURUNDI": {"x": 30, "y": -3, "fontsize": 5, "label": "BDI."},
        # Caribbean/Central America (examples)
        "CUBA": {"x": -79, "y": 21.5, "fontsize": 5, "label": "CUBA"},
        "JAMAICA": {"x": -77, "y": 18, "fontsize": 5, "label": "JAM."},
        "HAITI": {"x": -72.5, "y": 19, "fontsize": 5, "label": "HAITI"},
        "DOMINICAN REPUBLIC": {"x": -70, "y": 19, "fontsize": 5, "label": "DOM."},
        "TRINIDAD & TOBAGO": {"x": -61, "y": 10.5, "fontsize": 5, "label": "T&T"},
        # Oceania (examples)
        "FIJI": {"x": 178, "y": -17, "fontsize": 5, "label": "FIJI"},
        "SAMOA": {"x": -172, "y": -13.5, "fontsize": 5, "label": "SAMOA"},
        "TONGA": {"x": -175, "y": -21, "fontsize": 5, "label": "TONGA"},
        "VANUATU": {"x": 167, "y": -16, "fontsize": 5, "label": "VAN."},
    }

    # Abbreviations for small/crowded countries
    abbr_dict = {
        "NETHERLANDS": "NETH.", "SWITZERLAND": "SWITZ.", "UNITED KINGDOM": "UK", "SOUTH KOREA": "S. KOREA",
        "NORTH KOREA": "N. KOREA", "CZECH REPUBLIC": "CZECHIA", "CZECHIA": "CZECH.", "NEW ZEALAND": "N.ZEALAND",
        "AUSTRALIA": "AUS.", "ARGENTINA": "ARG.", "INDONESIA": "INDO.", "MALAYSIA": "MALAY.", "VIET NAM": "VIET.",
        "VIETNAM": "VIET.", "DEMOCRATIC REPUBLIC OF THE CONGO": "D.R.C.", "CENTRAL AFRICAN REPUBLIC": "C.A.R.",
        "SOUTH AFRICA": "S. AFRICA", "SAUDI ARABIA": "S. ARABIA", "ETHIOPIA": "ETH.", "NIGERIA": "NIG.",
        "FRANCE": "FR.", "GERMANY": "GER.", "SPAIN": "SPAIN", "CYPRUS": "CYPRUS", "JAPAN": "JAPAN",
        "TURKEY": "TURKEY", "EGYPT": "EGYPT", "RUSSIA": "RUSSIA", "CANADA": "CANADA", "CHINA": "CHINA",
        "INDIA": "INDIA", "BRAZIL": "BRAZIL", "MEXICO": "MEXICO"
    }

    def get_default_label(row):
        shapefile_name = row['NAME'].upper()
        mapped_name = name_map.get(shapefile_name, shapefile_name)
        point = row['geometry'].representative_point()
        x, y = point.x, point.y
        # Font size: large for big, small for small
        area = row['geometry'].area
        if area > 2e12:
            fontsize = 13
        elif area > 5e11:
            fontsize = 10
        elif area > 1e11:
            fontsize = 8
        elif area > 5e10:
            fontsize = 7
        else:
            fontsize = 5
        label = abbr_dict.get(mapped_name, mapped_name)
        return {"x": x, "y": y, "fontsize": fontsize, "label": label}

    # Merge hand-tuned and default overrides
    def get_label_override(mapped_name, row):
        if mapped_name in crowded_overrides:
            return crowded_overrides[mapped_name]
        else:
            return get_default_label(row)

    already_labeled = set()
    for label, x, y, font_size in major_labels:
        label_text = crowded_overrides.get(label, {}).get("label", label)
        ax.text(
            x, y, label_text,
            fontsize=font_size,
            color='black',
            ha='center', va='center',
            zorder=2,
            family='DejaVu Sans',
            fontweight='bold',
            path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="white")]
        )
        already_labeled.add(label)

    for idx, row in world.iterrows():
        shapefile_name = row['NAME'].upper()
        mapped_name = name_map.get(shapefile_name, shapefile_name)
        # Only label flagged (blacklisted) countries not already labeled
        if row['flagged'] and mapped_name not in already_labeled:
            override = get_label_override(mapped_name, row)
            x = override["x"]
            y = override["y"]
            fontsize = override["fontsize"]
            label_text = override["label"]
            ax.text(
                x, y, label_text,
                fontsize=fontsize,
                color='black',
                ha='center', va='center',
                zorder=2,
                family='DejaVu Sans',
                fontweight='bold',
                path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground="white")]
            )
            already_labeled.add(mapped_name)

    # Remove axes
    ax.set_axis_off()

    # Title (unchanged, but ensure not too close to top)
    plt.suptitle('Blacklisted Sign-in Countries', fontsize=26, fontweight='bold', ha='left', x=0.13, y=0.97, family='DejaVu Sans', color='black')

    # Legend (unchanged, but ensure clean)
    red_patch = mpatches.Patch(color='#b22222', label='Blacklisted Sign-in Countries')
    ax.legend(handles=[red_patch], loc='upper left', bbox_to_anchor=(-0.16, 1.05), fontsize=14, frameon=False, labelcolor='black')

    # List of high risk countries (unchanged)
    high_risk_names = sorted(world.loc[world['flagged'], 'NAME'].tolist())
    country_list_text = 'Blacklisted Countries:\n' + '\n'.join(f'• {name}' for name in high_risk_names)
    fig.text(0.01, 0.7, country_list_text, fontsize=13, color='black', ha='left', va='top', fontweight='bold', linespacing=1.5, family='DejaVu Sans')

    # Save as high-res PNG with tight bounding box and minimal padding
    plt.savefig('C:\\CloudFlare Data\\flagged_countries_map.png', bbox_inches='tight', facecolor='white', dpi=300, pad_inches=0.1)
    plt.show()

# Fetch data and write it to CSV files
data_layer7_source = fetch_data(url_layer7_source)
data_layer7_target = fetch_data(url_layer7_target)
data_layer3_source = fetch_data(url_layer3_source)
data_layer3_target = fetch_data(url_layer3_target)

# Write the Layer 7 and Layer 3 data to CSV files
if data_layer7_source:
    write_to_csv(data_layer7_source, 'C:\\CloudFlare Data\\layer7_source_attack_data.csv')

if data_layer7_target:
    write_to_csv(data_layer7_target, 'C:\\CloudFlare Data\\layer7_target_attack_data.csv', is_target=True)

if data_layer3_source:
    write_to_csv(data_layer3_source, 'C:\\CloudFlare Data\\layer3_source_attack_data.csv')

if data_layer3_target:
    write_to_csv(data_layer3_target, 'C:\\CloudFlare Data\\layer3_target_attack_data.csv', is_target=True)

# Create the comparison graphs for Layer 3 and Layer 7
if data_layer3_source and data_layer3_target and data_layer7_source and data_layer7_target:
    create_comparison_graph(
        data_layer3_source["result"]["main"],
        data_layer3_target["result"]["main"],
        data_layer7_source["result"]["main"],
        data_layer7_target["result"]["main"]
    )

# After all data is fetched and written to CSV, plot the map
if data_layer3_source and data_layer3_target and data_layer7_source and data_layer7_target:
    # Collect all unique country codes from all four datasets
    flagged_country_codes = set()
    for dataset, is_target in [
        (data_layer3_source["result"]["main"], False),
        (data_layer3_target["result"]["main"], True),
        (data_layer7_source["result"]["main"], False),
        (data_layer7_target["result"]["main"], True),
    ]:
        for item in dataset:
            if is_target:
                code = item.get("targetCountryAlpha2")
            else:
                code = item.get("originCountryAlpha2")
            if code:
                flagged_country_codes.add(code)
    plot_flagged_countries_on_map(flagged_country_codes)

print("Data exported to CSV files and comparison graphs created successfully.")
