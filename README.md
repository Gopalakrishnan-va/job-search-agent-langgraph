# 🎯 AI Job Search Agent

This Apify actor analyzes a resume and finds matching job opportunities from LinkedIn and Indeed, providing detailed scoring and relevancy analysis for each position.

## 🌟 Features

- 🤖 **Autonomous AI Agent**: Intelligently analyzes resumes and job postings
- 🎯 **Smart Matching**: Uses AI to calculate relevance scores based on multiple factors
- 🔍 **Multi-Platform Search**: Searches both LinkedIn and Indeed for comprehensive results
- 📊 **Advanced Scoring**: Evaluates jobs based on:
  - Skills Match (30%)
  - Experience Level (25%)
  - Location Match (25%)
  - Company/Role Fit (20%)
- 💡 **Intelligent Filtering**: Removes duplicate listings and irrelevant matches
- 📈 **Detailed Analytics**: Provides match scores and explanations for each job

## 🚀 Input Parameters

```json
{
    "resumeText": "Your resume text here",
    "apifyApiToken": "your-apify-token",
    "openAiApiKey": "your-openai-api-key",
    "locationPreference": "City, State",
    "workModePreference": "Any|Remote|Hybrid|On-site",
    "searchRadius": 25,
    "minSalary": 0
}
```

### Required Parameters
- `resumeText`: The full text of the resume to analyze
- `apifyApiToken`: Your Apify API token
- `openAiApiKey`: Your OpenAI API key

### Optional Parameters
- `locationPreference`: Preferred job location
- `workModePreference`: Preferred work mode (defaults to "Any")
- `searchRadius`: Search radius in miles (defaults to 25)
- `minSalary`: Minimum salary requirement (defaults to 0)

## 📊 Output Format

```json
{
    "query": {
        "resumeSummary": {
            "desired_role": "string",
            "skills": ["skill1", "skill2"],
            "years_of_experience": "number",
            "education": {
                "degree": "string",
                "institution": "string",
                "location": "string",
                "graduation_date": "string"
            },
            "location_preference": "string",
            "work_mode_preference": "string"
        },
        "searchParameters": {
            "location": "string",
            "workMode": "string"
        }
    },
    "results": [
        {
            "position": "string",
            "company": "string",
            "location": "string",
            "matchScore": "number",
            "matchDetails": {
                "skills_match": {
                    "score": "number",
                    "explanation": "string"
                },
                "experience_match": {
                    "score": "number",
                    "explanation": "string"
                },
                "location_match": {
                    "score": "number",
                    "explanation": "string"
                },
                "company_fit": {
                    "score": "number",
                    "explanation": "string"
                }
            },
            "applicationUrl": "string",
            "source": "LinkedIn|Indeed"
        }
    ],
    "statistics": {
        "totalJobsFound": "number",
        "averageMatchScore": "number",
        "topSkillsRequested": ["skill1", "skill2", "skill3", "skill4", "skill5"],
        "timestamp": "string"
    }
}
```

## 💰 Pricing

The actor uses a pay-per-event pricing model with the following charges:

- Resume Parsing: $0.10 per resume
- Job Scoring: $0.02 per job analyzed
- Results Summary: $0.10 per search completion

## 🛠️ Technical Details

- Built on Apify platform
- Uses OpenAI's GPT model for analysis
- Integrates with LinkedIn and Indeed job search APIs
- Implements asynchronous processing for better performance

## 🔄 How It Works

1. 📄 **Resume Analysis**
   - Extracts key information from resume
   - Identifies skills, experience, and preferences

2. 🔍 **Job Search**
   - Searches LinkedIn and Indeed simultaneously
   - Collects detailed job information
   - Removes duplicates and irrelevant listings

3. ⚖️ **Smart Matching**
   - Scores each job based on multiple criteria
   - Uses AI to evaluate job descriptions
   - Calculates weighted relevance scores

4. 📊 **Results Processing**
   - Ranks jobs by match score
   - Generates detailed match explanations
   - Provides comprehensive statistics

## 🚀 Getting Started

1. Get your API keys:
   - Apify API Token
   - OpenAI API Key

2. Set up environment variables:
```bash
APIFY_TOKEN=your_token
OPENAI_API_KEY=your_key
```

3. Run the actor with your resume and preferences

## 📝 License

MIT License - feel free to use and modify!

## Scrape single-page in Python template

A template for [web scraping](https://apify.com/web-scraping) data from a single web page in Python. The URL of the web page is passed in via input, which is defined by the [input schema](https://docs.apify.com/platform/actors/development/input-schema). The template uses the [HTTPX](https://www.python-httpx.org) to get the HTML of the page and the [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to parse the data from it. The data are then stored in a [dataset](https://docs.apify.com/sdk/python/docs/concepts/storages#working-with-datasets) where you can easily access them.

The scraped data in this template are page headings but you can easily edit the code to scrape whatever you want from the page.

## Included features

- **[Apify SDK](https://docs.apify.com/sdk/python/)** for Python - a toolkit for building Apify [Actors](https://apify.com/actors) and scrapers in Python
- **[Input schema](https://docs.apify.com/platform/actors/development/input-schema)** - define and easily validate a schema for your Actor's input
- **[Request queue](https://docs.apify.com/sdk/python/docs/concepts/storages#working-with-request-queues)** - queues into which you can put the URLs you want to scrape
- **[Dataset](https://docs.apify.com/sdk/python/docs/concepts/storages#working-with-datasets)** - store structured data where each object stored has the same attributes
- **[HTTPX](https://www.python-httpx.org)** - library for making asynchronous HTTP requests in Python
- **[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)** - library for pulling data out of HTML and XML files

## How it works

1. `Actor.get_input()` gets the input where the page URL is defined
2. `httpx.AsyncClient().get(url)` fetches the page
3. `BeautifulSoup(response.content, 'lxml')` loads the page data and enables parsing the headings
4. This parses the headings from the page and here you can edit the code to parse whatever you need from the page
    ```python
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
    ```
5. `Actor.push_data(headings)` stores the headings in the dataset

## Resources

- [BeautifulSoup Scraper](https://apify.com/apify/beautifulsoup-scraper)
- [Python tutorials in Academy](https://docs.apify.com/academy/python)
- [Web scraping with Beautiful Soup and Requests](https://blog.apify.com/web-scraping-with-beautiful-soup/)
- [Beautiful Soup vs. Scrapy for web scraping](https://blog.apify.com/beautiful-soup-vs-scrapy-web-scraping/)
- [Integration with Make, GitHub, Zapier, Google Drive, and other apps](https://apify.com/integrations)
- [Video guide on getting scraped data using Apify API](https://www.youtube.com/watch?v=ViYYDHSBAKM)
- A short guide on how to build web scrapers using code templates:

[web scraper template](https://www.youtube.com/watch?v=u-i-Korzf8w)


## Getting started

For complete information [see this article](https://docs.apify.com/platform/actors/development#build-actor-locally). To run the actor use the following command:

```bash
apify run
```

## Deploy to Apify

### Connect Git repository to Apify

If you've created a Git repository for the project, you can easily connect to Apify:

1. Go to [Actor creation page](https://console.apify.com/actors/new)
2. Click on **Link Git Repository** button

### Push project on your local machine to Apify

You can also deploy the project on your local machine to Apify without the need for the Git repository.

1. Log in to Apify. You will need to provide your [Apify API Token](https://console.apify.com/account/integrations) to complete this action.

    ```bash
    apify login
    ```

2. Deploy your Actor. This command will deploy and build the Actor on the Apify Platform. You can find your newly created Actor under [Actors -> My Actors](https://console.apify.com/actors?tab=my).

    ```bash
    apify push
    ```

## Documentation reference

To learn more about Apify and Actors, take a look at the following resources:

- [Apify SDK for JavaScript documentation](https://docs.apify.com/sdk/js)
- [Apify SDK for Python documentation](https://docs.apify.com/sdk/python)
- [Apify Platform documentation](https://docs.apify.com/platform)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)

## Scoring System

Each job is scored across four dimensions:

1. **Skills Match (30%)**: Evaluates how well the candidate's skills align with job requirements
2. **Experience Match (25%)**: Assesses the match between required and actual experience
3. **Location Match (25%)**: Considers geographical alignment with preferences
4. **Company/Role Fit (20%)**: Evaluates overall role and company culture fit

Final scores are weighted averages of these components, ranging from 0-100.

## Usage Limits

- Maximum of 10 jobs per source (LinkedIn and Indeed)
- Job descriptions are truncated to 1000 characters for scoring
- Results are limited to top 10 matches

## Error Handling

- Failed job scores default to 70 points
- Missing application URLs default to empty strings
- Invalid inputs trigger appropriate error messages

## Best Practices

1. Provide detailed resume text for better matching
2. Include location preferences for more accurate results
3. Specify work mode preference if important
4. Use appropriate API tokens with necessary permissions

## Support

For issues and feature requests, please contact Apify support or submit an issue in the repository.