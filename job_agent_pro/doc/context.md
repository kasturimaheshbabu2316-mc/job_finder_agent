# Job Agent Project Context

## Project Overview
Building an automated job agent that scrapes job listings from multiple platforms based on user-provided exact job role and location preferences, and stores them in a structured CSV format for further processing and analysis.

## Problem Statement
Job seekers need to monitor multiple job platforms to find relevant opportunities. Manually checking naukri and remoteOK for specific job roles and locations is time-consuming and inefficient. An automated agent can consolidate job listings from these sources into a single, searchable format based on user preferences.

## Solution Architecture
- **Job Scraping**: Automated web scraping from two major job platforms
  - **Naukri**: HTML scraping (India-focused job board)
  - **RemoteOK**: Public API integration (Remote job opportunities)

- **User Input Integration**:
  - Exact job role input from user (structured data field)
  - Exact location input from user (structured data field)
  - Dynamic triggering of scrapers based on user input
  - *Note: No natural language processing - direct field input*

- **Data Processing**: Normalize job data from different sources into a consistent format
- **Data Storage**: Store aggregated job listings in CSV format for easy access and analysis

## Key Features
1. **Multi-platform Scraping**: Extract job data from naukri and remoteOK based on user input
2. **User-Driven Search**: Accept exact job role and location as user input parameters
3. **Dynamic Scraper Triggering**: Automatically trigger both platform scrapers with user-provided criteria
4. **Job Filtering**: Filter jobs by relevant job titles/keywords and location
5. **Data Normalization**: Standardize job fields across different platforms
6. **CSV Export**: Store results in structured CSV format
7. **Deduplication**: Remove duplicate job listings across platforms

## Technical Considerations
- **Rate Limiting**: Respect each platform's API limits or scraping policies
- **Error Handling**: Robust error handling for network issues and changes in platform structure
- **Data Validation**: Ensure data quality and completeness
- **User Input Handling**: Process and validate exact user-provided job role and location fields
- **Scheduling**: Potential for scheduled runs to capture new job postings

## Platform-Specific Implementation
- **Naukri**: HTML scraping using requests and BeautifulSoup for parsing job listings with user-provided exact search parameters
- **RemoteOK**: Public API integration using their official REST API for structured job data with user-provided exact filters

## User Input Flow (Phase 5)
1. **User Input Collection**:
   - **Exact job role**: User provides specific job title/role (e.g., "software engineer", "data scientist", "frontend developer")
   - **Exact location**: User provides specific location (e.g., "remote", "bengaluru", "mumbai", "pune")
   - *Note: Input is structured data fields, not natural language processing*

2. **Scraper Triggering**:
   - Automatically trigger Naukri scraper with exact user-provided job role and location
   - Automatically trigger RemoteOK scraper with exact user-provided job role and location
   - Both scrapers run in parallel for efficiency

3. **Data Aggregation**:
   - Collect results from both platforms
   - Normalize and deduplicate job listings
   - Export to CSV with user-specified filename or default

## Data Fields to Capture
- Job Title
- Company Name
- Job Description
- Location
- Salary Range
- Job Type (Full-time, Part-time, Contract, etc.)
- Posted Date
- Job URL
- Platform Source

## Current Status
- Project initialization phase completed
- Core infrastructure implemented (Phases 1-6)
- User input integration in Phase 5
- Ready for deployment and testing with real user scenarios