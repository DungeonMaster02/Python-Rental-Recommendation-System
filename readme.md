# 🏠 USC Housing Recommendation System

A data-driven housing recommendation system for USC students, integrating rental listings, crime data, amenities, and distance to campus.

## 📌 Overview

This project aims to help USC students make smarter housing decisions by combining multiple real-world data sources. Instead of manually browsing listings, users can receive personalized recommendations based on their preferences.

The system evaluates rental listings using four key factors:

* Safety
* Convenience (nearby amenities)
* Distance to USC
* Affordability

Users can assign weights to these factors, and the system will rank housing options accordingly.

---

## 📊 Data Sources

1. **Rental Listings**

   * Source: Craigslist Los Angeles
   * Data: rent, title, posting date, location text
   * URL: https://losangeles.craigslist.org/search/apa

2. **Amenities Data**

   * Source: Google Places API
   * Data: nearby grocery stores, restaurants, transit, etc.
   * URL: https://developers.google.com/maps/documentation/places/web-service/nearby-search

3. **Crime Data (Safety)**

   * Source: LA Open Data Portal
   * Data: crime incidents (2020–2024)
   * URL: https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-2024/2nrs-mtv8

---

## ⚙️ Methodology

### Step 1: Data Collection

* Scrape rental listings from Craigslist
* Load crime dataset (CSV)
* Query nearby amenities using Google Places API

### Step 2: Data Processing

* Convert listing locations into geographic coordinates
* Link each listing with:

  * Nearby crime incidents
  * Nearby amenities
  * Distance to USC

### Step 3: Feature Engineering

For each listing, compute:

* **Safety score** (based on nearby crime density)
* **Convenience score** (number/type of nearby amenities)
* **Distance score** (distance to USC)
* **Affordability score** (relative rent level)

### Step 4: Weighted Scoring

Users assign weights to:

* Safety
* Convenience
* Distance
* Affordability

Final score:

```
Final Score = w1 * Safety + w2 * Convenience + w3 * Distance + w4 * Affordability
```

### Step 5: Ranking & Recommendation

* Rank listings by final score
* Return top recommended housing options

---

## 🎯 Project Goals

* Provide **data-driven housing recommendations**
* Support **personalized decision-making**
* Combine multiple real-world factors into one system
* Improve over manual browsing of listings

---

## ❓ Key Questions

This project aims to explore:

* Which listings best match different student preferences?
* How do recommendations change with different weights?
* Are cheaper rentals associated with:

  * Lower safety?
  * Longer distance from USC?

---

## 📦 Expected Output

* Ranked list of rental listings (titles or URLs)
* Top recommendations based on user preferences
* (Optional) Visualizations:

  * Safety vs price
  * Distance vs affordability
  * Amenities comparison

---

## 🚧 Limitations

* Does not analyze **interior conditions** of housing
* Does not include:

  * Image recognition
  * Deep semantic analysis of listings
* Focus is on **external and location-based factors**

---

## 🧠 Future Improvements

* Image-based apartment quality analysis
* NLP-based listing description analysis
* More advanced personalization models

---

## 👤 Author

Pengshao Ye
