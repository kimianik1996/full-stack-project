import pymongo
import streamlit as st
import pandas as pd
import plotly.express as px

# MongoDB Atlas connection string (Replace with your credentials)
client = pymongo.MongoClient("mongodb+srv://kimiaNik1375:Khatereh1351@businessdbcluster.nmoz7.mongodb.net/VancouverBusinesses?retryWrites=true&w=majority")

# Test the connection
try:
    db = client["VancouverBusinesses"]
    print("Connected to the database!")
    print("Collections:", db.list_collection_names())
except Exception as e:
    print("Error connecting to MongoDB:", e)

# Get the collection for business data
collection1 = db["business"]

# Query data from the business collection and convert the cursor to a list
business_data = list(collection1.find())  # Business data

# Provided city population data
city_population = {
    'Abbotsford': 170854,
    'Ammore': 2606,
    'BowenIsland': 4256,
    'Burnaby': 259495,
    'Coquitlam': 154528,
    'Delta': 88461,
    'DownTown': 737216,
    'Langley': 142738,
    'Lions Bay': 1473,
    'Maple Ridge': 96669,
    'New Westminster': 84086,
    'North Vancouver': 89715,
    'Pitt Meadows': 19498,
    'Port Coquitlam': 63297,
    'Port Moody': 33525,
    'Richmond': 217239,
    'Surrey': 600911,
    'Tsawwassen': 23904,
    'WestVancouver': 45142,
    'White Rock': 23225
}

# Count the number of businesses in each city
city_names = [doc['City'] for doc in business_data]  # Extract city names from the business data
business_counts = {city: city_names.count(city) for city in set(city_names)}  # Count occurrences of each city

# Create a DataFrame for the cities and their business count and population
df = pd.DataFrame(list(business_counts.items()), columns=["City", "BusinessCount"])

# Add population data for each city from the provided dictionary
df["Population"] = df["City"].apply(lambda x: city_population.get(x, 0))

# Sort the data by BusinessCount in descending order
df = df.sort_values(by="BusinessCount", ascending=False)

# Create a bar chart using Plotly
fig = px.bar(df, 
             x="City", 
             y="BusinessCount", 
             hover_data=["Population"], 
             title="Small Businesses in Metro Vancouver Cities", 
             labels={"BusinessCount": "Number of Small Businesses", "City": "City"})
fig.update_traces(marker_color='royalblue', opacity=0.7)

# Display the bar chart in Streamlit
st.plotly_chart(fig)

# Add a dropdown to select a city
selected_city = st.selectbox("Select a City to View Details", ["All Cities"] + list(df['City'].unique()))

# Filter the data for the selected city
if selected_city != "All Cities":
    selected_city_data = [doc for doc in business_data if doc['City'] == selected_city]
else:
    # For "All Cities", display the data for all cities
    selected_city_data = business_data

# Filter data based on business categories for the selected city or all cities
category_data = pd.DataFrame([doc['Category'] for doc in selected_city_data], columns=["Category"])
category_count = category_data['Category'].value_counts()

# Create the pie chart for the selected city or all cities
fig_pie = px.pie(values=category_count.values, 
                 names=category_count.index, 
                 title=f"Top Small Business Categories in {selected_city}" if selected_city != "All Cities" else "Top Small Business Categories in All Cities", 
                 labels={"Category": "Business Category"})
fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0.1, 0.1, 0.1])

# Display the pie chart in Streamlit
st.plotly_chart(fig_pie)

# Get all unique cities from the database
cities = collection1.distinct('City')

# Add a dropdown to select a city
selected_city = st.selectbox("Select a City to View Details", ["All Cities"] + cities)

# Prepare query based on city selection
if selected_city != "All Cities":
    query = {'City': selected_city}
else:
    query = {}

# Aggregate total ratings per category based on the selected city
pipeline = [
    {"$match": query},  # Filter by city if selected
    {"$group": {
        "_id": "$Category",  # Group by business category
        "total_ratings": {"$sum": "$Total Ratings"}  # Sum up the total ratings for each category
    }},
    {"$sort": {"total_ratings": -1}}  # Sort by total ratings in descending order
]

# Execute the aggregation pipeline
category_data = list(collection1.aggregate(pipeline))

# If no data found, display a message
if not category_data:
    st.write("No data available for the selected city.")
else:
    # Prepare the data for visualization
    category_df = pd.DataFrame(category_data)
    category_df = category_df.rename(columns={"_id": "Category", "total_ratings": "Total Google Ratings"})

    # Create a bar chart for total Google ratings by category
    fig_category_total_ratings = px.bar(category_df, 
                                        x="Category", 
                                        y="Total Google Ratings", 
                                        title="Total Google Ratings by Category",
                                        labels={'Total Google Ratings': 'Total Google Ratings', 'Category': 'Business Category'},
                                        color="Total Google Ratings",
                                        color_continuous_scale="Purples")

    # Display the bar chart
    st.plotly_chart(fig_category_total_ratings)

