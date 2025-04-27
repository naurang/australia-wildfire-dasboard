import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import requests
import folium

# Create app
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
])

# this code is for the render server
server = app.server


app.config.suppress_callback_exceptions = True

# Read the wildfire data
df = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/Historical_Wildfires.csv')
df['Month'] = pd.to_datetime(df['Date']).dt.month_name()
df['Year'] = pd.to_datetime(df['Date']).dt.year

# Custom color theme
custom_theme = {
    "primary": "#3A59D1",
    "secondary": "#3D90D7",
    "accent": "#7AC6D2",
    "light": "#B5FCCD",
    "white": "#FFFFFF"
}

# App Layout
app.layout = html.Div([
    # Navbar
    dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Img(src="/assets/284471.png", height="40px")),
                dbc.Col(dbc.NavbarBrand("Australia Wildfire Dashboard", className="ms-2", style={"color": "white", "fontWeight": "bold"}))
            ], align="center", className="g-0")
        ], fluid=True),
        color=custom_theme["primary"],
        dark=True,
        className="mb-2"
    ),

    # Sidebar and Main Content
    dbc.Container(fluid=True, children=[
        dbc.Row([
            # Sidebar
            dbc.Col([
                html.H4("Filters", style={"color": "white", "fontWeight": "bold", "marginBottom": "20px"}),
                html.Hr(style={"borderColor": custom_theme["accent"], "borderWidth": "2px"}),
                
                html.Label("Select Region:", style={"color": "white", "fontSize": "16px"}),
                dcc.RadioItems(
                    options=[
                        {"label": "New South Wales", "value": "NSW"},
                        {"label": "Northern Territory", "value": "NT"},
                        {"label": "Queensland", "value": "QL"},
                        {"label": "South Australia", "value": "SA"},
                        {"label": "Tasmania", "value": "TA"},
                        {"label": "Victoria", "value": "VI"},
                        {"label": "Western Australia", "value": "WA"}
                    ],
                    value="NSW",
                    id="region",
                    style={"color": "white", "marginBottom": "20px"}
                ),

                html.Label("Select Year:", style={"color": "white", "fontSize": "16px"}),
                dcc.Dropdown(
                    options=[{"label": year, "value": year} for year in sorted(df.Year.unique())],
                    value=2005,
                    id="year",
                    style={
                        "backgroundColor": custom_theme["white"],
                        "color": custom_theme["primary"],
                        "borderRadius": "5px",
                        "marginTop": "10px"
                    }
                )
            ], width=2, style={
                "backgroundColor": custom_theme["secondary"],
                "height": "100vh",
                "borderRadius": "10px",
                "padding": "20px",
                "position": "fixed",
                "left": 0,
                "top": 60,  # navbar height
                "overflowY": "auto"
            }),

            # Main Content
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Monthly Average Estimated Fire Area", className="card-title", style={"color": custom_theme["primary"], "marginBottom": "20px"}),
                                html.Div(id="plot1")
                            ])
                        ], style={"height": "550px", "marginBottom": "40px"}),  # Increased margin below the card

                        html.Iframe(
                            id="region-map",
                            style={"width": "100%", "height": "400px", "border": "0"}
                        )
                    ], width=6),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Live Weather", className="card-title", style={"color": custom_theme["primary"], "marginBottom": "20px"}),
                                html.Div(id="live-weather")
                            ])
                        ], style={"height": "400px", "marginBottom": "10px"}),  # Added margin below the Live Weather card

                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Average Count of Pixels for Presumed Vegetation Fires", className="card-title", style={"color": custom_theme["primary"], "marginBottom": "20px"}),
                                html.Div(id="plot2")
                            ])
                        ], style={"height": "600px"})
                    ], width=6)
                ])
            ], width={"size": 10, "offset": 2}, style={"marginTop": "20px"})
        ])
    ])
])

# Plot Callback
@app.callback(
    [Output('plot1', 'children'),
     Output('plot2', 'children')],
    [Input('region', 'value'),
     Input('year', 'value')]
)
def reg_year_display(input_region, input_year):  
    region_data = df[df['Region'] == input_region]
    y_r_data = region_data[region_data['Year'] == input_year]
    
    est_data = y_r_data.groupby('Month')['Estimated_fire_area'].mean().reset_index()
    fig1 = px.pie(est_data, values='Estimated_fire_area', names='Month',
                  title=f"{input_region} : Monthly Average Estimated Fire Area in {input_year}")
    fig1.update_layout(title_font_color='gray')

    veg_data = y_r_data.groupby('Month')['Count'].mean().reset_index()
    fig2 = px.bar(veg_data, x='Month', y='Count',
                  title=f"{input_region} : Avg. Count of Pixels for Presumed Vegetation Fires in {input_year}")
    fig2.update_layout(title_font_color='gray')

    return dcc.Graph(figure=fig1), dcc.Graph(figure=fig2)

# Function to fetch the user's location based on their IP address
def fetch_user_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "Unknown")
            return city
        else:
            return "Unknown"
    except Exception as e:
        return "Unknown"

# Function to fetch live weather data using wttr.in (no API key required)
def fetch_weather_data(city="Chicago"):
    base_url = f"https://wttr.in/{city}?format=%t|%C|%l"
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.text.split('|')
            return {
                "temperature": data[0],
                "condition": data[1],
                "location": data[2]
            }
        else:
            return {
                "temperature": "N/A",
                "condition": "N/A",
                "location": city
            }
    except Exception as e:
        return {
            "temperature": "N/A",
            "condition": "N/A",
            "location": city
        }

# Update the live weather callback to use the user's location
@app.callback(
    Output("live-weather", "children"),
    [Input("region", "value")]
)
def update_weather(region):
    # Fetch the user's location
    user_city = fetch_user_location()

    # Map region to a city (fallback if user location is unavailable)
    region_to_city = {
        "NSW": "Sydney",
        "NT": "Darwin",
        "QL": "Brisbane",
        "SA": "Adelaide",
        "TA": "Hobart",
        "VI": "Melbourne",
        "WA": "Perth"
    }
    city = user_city if user_city != "Unknown" else region_to_city.get(region, "Sydney")

    # Fetch weather data for the determined city
    weather_data = fetch_weather_data(city)

    return html.Div([
    html.H2(weather_data['temperature'], style={
        "color": "#222831",
        "fontWeight": "bold",
        "fontSize": "40px"
    }),
    html.H4(weather_data['location'], style={
        "color": "#393E46",
        "marginTop": "10px"
    }),
], style={
    "padding": "20px",
    "backgroundColor": "white",
    "backgroundImage": "url('/assets/people11.svg')",
    "backgroundSize": "cover",          # fill entire box
    "backgroundRepeat": "no-repeat",
    "backgroundPosition": "center",     # FIXED this!
    "borderRadius": "10px",
    "height": "300px",                  # give a fixed height
    "width": "100%",
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "center",
    "justifyContent": "center",
    "overflow": "hidden",               # clip extra if any
})


# Function to generate a Folium map based on the selected region
def generate_folium_map(region):
    # Map region to coordinates (example mapping, adjust as needed)
    region_to_coords = {
        "NSW": [-35.4865, 150.0843],  # Example: Morton National Park
        "NT": [-13.0923, 131.3076],  # Example: Litchfield National Park
        "QL": [-25.2406, 152.6145],  # Example: Fraser Island
        "SA": [-35.3533, 138.7071],  # Example: Belair National Park
        "TA": [-42.6833, 146.6667],  # Example: Southwest National Park
        "VI": [-37.4333, 145.8667],  # Example: Yarra Ranges National Park
        "WA": [-34.3333, 115.1667]   # Example: Leeuwin-Naturaliste National Park
    }
    coords = region_to_coords.get(region, [-33.8688, 151.2093])  # Default to Sydney

    # Create a Folium map
    folium_map = folium.Map(location=coords, zoom_start=10)
    folium.Marker(location=coords, popup=f"Region: {region}").add_to(folium_map)

    # Save the map to an HTML file
    map_path = "assets/folium_map.html"
    folium_map.save(map_path)
    return map_path

# Callback to update the Folium map based on the selected region
@app.callback(
    Output("region-map", "srcDoc"),
    [Input("region", "value")]
)
def update_folium_map(region):
    map_path = generate_folium_map(region)
    with open(map_path, "r") as f:
        return f.read()

if __name__ == '__main__':
    app.run()  # Disabled debug mode to prevent automatic refresh
# Note: Make sure to replace 'your_openweathermap_api_key' with your actual OpenWeatherMap API key.
# Also, ensure that the CSV file URL is accessible and the data format matches the expected structure.
# The above code is a complete Dash application that visualizes wildfire data in Australia and provides live weather information.
# The application includes a sidebar for filtering by region and year, and it displays two graphs:
