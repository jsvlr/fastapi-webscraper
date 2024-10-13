from fastapi import HTTPException, APIRouter
from bs4 import BeautifulSoup
from datetime import datetime as dt
from dotenv import load_dotenv
from app.models import weather as model
import requests, re, os

# load variables from .env files
load_dotenv()

router = APIRouter()
BASE_URL = os.getenv("WEATHER_BASE_URL")

@router.on_event("startup")
async def start():
    print("Weather API started")

@router.on_event("shutdown")
async def end():
    print("Weather API shutdown")

def getTimeNow() -> str:
    timeNow = dt.now()
    minute:str =f"0{timeNow.minute}" if timeNow.minute < 10 else timeNow.minute
    hour:str = f"{timeNow.hour - 12}:{minute} PM" if int(timeNow.hour) > 12 else f"{timeNow.hour} : {minute} AM"
    fulltime:str = f"Issued at {hour} today, {timeNow.strftime("%d %B %Y")} "

    return fulltime

def extractDigits(digitString:str) -> float|None:
   
    # get the numbers or integers in a string (with decimal point ".")
    pattern =  r'-?\d+\.\d+|-?\d+'
    digit = re.search(pattern=pattern, string=digitString)
    if digit:
        return float(digit.group())
    return None


@router.get("/daily/", tags=['daily'], response_model=model.MainResponse)
async def dailyTemperature() -> model.MainResponse:

    try:
        URL:str = f"{BASE_URL}/weather/low-high-temperature"
        content = requests.get(URL)
        scraper = BeautifulSoup(content.text, "html.parser")

        # get all tables
        tables:list = scraper.find_all("table", {"class":"table"})

        # Heading
        header:str = scraper.find("div",{"id":"daily-weather-forecast"}).text.strip()

        datas = []
        for table in tables:
            tbody = table.find("tbody")
            records = tbody.find_all("tr")
        
            for row in records:
                cells = row.find_all("td")
                place = cells[0].text.strip()
                # ensure the row has two columns
                if len(cells) > 1:
                    temperature = extractDigits(cells[1].text.strip())
                    data = model.StationTemperature(
                        place=place,
                        temperature=temperature
                    )
                    datas.append(data)

        time = getTimeNow()

        response = model.ResponseData(
            header=header,
            time_issued=f"{time}",
            valid_until = "n/a",
            locations=datas
        )

        return model.MainResponse(response=response)
    
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
     
@router.get("/asian-cities/", tags=['asian-cities'], response_model=model.MainResponse)
async def asiaWeather() -> model.MainResponse:
    try:
        URL:str = f"{BASE_URL}/weather/weather-asian-cities-weather-forecast"
        content = requests.get(URL)
        scraper = BeautifulSoup(content.text, "html.parser")
        
        infos:list[str] = [info.text.strip() for info in scraper.find_all("h5")]

        timeIssued:str = infos[0]
        validUntil:str = infos[1]
        table = scraper.find("table", {"class":"table"})
        tbody = table.find("tbody")
        rows = tbody.find_all("tr")
        
        datas = []

        for row in rows:
            columns = row.find_all("td")
            station:list[str] = columns[0].text.strip().split(',')
            city:str = station[0].strip()
            country:str = station[-1].strip()
            description = columns[1].text.strip()
            highTemperature = extractDigits(columns[2].text.strip())
            lowTemperature = extractDigits(columns[3].text.strip())
            
            data = model.AsianCitiesData(
                country=country,
                city=city,
                temperature_description=description,
                temperature_high=highTemperature,
                temperature_low=lowTemperature
            )

            datas.append(data)
        
        response = model.ResponseData(
            header="Asian Cities Weather Forecast",
            time_issued=timeIssued,
            valid_until=validUntil,
            locations= datas
        )

        return model.MainResponse(response=response)
    
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
 
@router.get("/tourist-areas/", tags=["tourist-areas"], response_model=model.MainResponse)
async def touristAreasWeather() -> model.MainResponse:
    try:
        URL:str = f"{BASE_URL}/weather/weather-outlook-selected-tourist-areas"
        content = requests.get(URL)
        scraper = BeautifulSoup(content.text, "html.parser")
        table = scraper.find("table",{"class":"table"})
        theads = table.find("thead").find("tr").find_all("th")

        theadsContainer = [head.text.strip() for head in theads]

        # Skips first column does it not contain date
        datesColumns:list[str] = [date.strip().split(" ") for date in theadsContainer[1:]]

        dayDateContainer = []
        for ds in datesColumns:
            date = ' '.join(ds[2:])
            day = ds[0]
            dateData = {
                'day':day,
                'date':date
            }
            dayDateContainer.append(dateData)

        header = scraper.find("div", {'id':'weather-outlook-selected-tourist-areas'}).text.strip()
        infos:list[str] = [info.text.strip() for info in scraper.find_all("h5")]
        timeIssued:str = infos[0]
        validUntil:str = infos[1]

        tbody = table.find("tbody")
        rows = tbody.find_all("tr")

        datas = []

        for row in rows:
            columns = row.find_all("td")
            destination = columns[0].text.strip()
            place = destination[destination.index(")") + 1:]
            areas = destination[1:destination.index(")")]
            dates = columns[1:]
            temperature = []

            for index, date in enumerate(dates, 0):
                description = date.find("img")['title']
                high = extractDigits(date.find("h5", {"class":"high-temp"}).text.strip())
                low = extractDigits(date.find("h5", {"class":"low-temp"}).text.strip())
              
                tempe = model.TouristAreasDates(
                    day=dayDateContainer[index]['day'],
                    date=dayDateContainer[index]['date'],
                    temperature_description=description,
                    temperature_high=high,
                    temperature_low=low
                )
                temperature.append(tempe)

            data = model.TouristAreasData(
                place=place,
                areas=areas,
                dates=temperature
            )
            datas.append(data)

        response = model.ResponseData(
            header=header,
            time_issued=timeIssued,
            valid_until=validUntil,
            locations=datas
        )
        mainResponse = model.MainResponse(response = response)

        return mainResponse
    
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/selected-cites/")
async def selectedCities():
    try:
        URL = f"{BASE_URL}/weather/weather-outlook-selected-philippine-cities"
        content = requests.get(URL)
        scraper = BeautifulSoup(content.text, "html.parser")

        header = scraper.find("div", {'id':"weather-outlook-selected-philippine-cities"}).text.strip()
        time = scraper.find("h5").text.strip()
        panels = scraper.find_all("div", {'class':"panel-pagasa"})
        cities = []
        # for panel in panels:
        #     city = panel.find("h4", {'class':"panel-title"})
        #     cities.add(city)
        
        response = model.ResponseData(
            header=header,
            time_issued=time,
            valid_until=time,
            locations=None
        )
        return model.MainResponse(response=response)
    except Exception as e:
        print(f"ERROR: {e}")
        