from fastapi import HTTPException, APIRouter, Query
import app.models.weather as model
from bs4 import BeautifulSoup
from typing_extensions import Annotated
from datetime import datetime as dt
import bs4
import requests
import re

router = APIRouter()
BASE_URL = "https://www.pagasa.dost.gov.ph"

def getTimeNow() -> str:
    timeNow = dt.now()
    month:str = "0" + str(timeNow.month) if len(str(timeNow.month)) == 1 else str(timeNow.month)
    day:str = "0" + str(timeNow.day) if len(str(timeNow.day)) == 1 else str(timeNow.day)
    time:str = f"{month}-{day}-{timeNow.year}"

    return time

def extractDigits(digitString:str) -> float|None:
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
        table:list = scraper.find_all("table", {"class":"table"})

        # Heading
        header:str = scraper.find("div",{"id":"daily-weather-forecast"}).text.strip()
        
        # Table for low temperature
        lowestTemp:list = table[0] 

        # Table for high temperature
        highestTemp:list = table[1]

        def getRecords(table:bs4.element.Tag) -> list[dict]:
            content = []
            tbody = table.find("tbody")
            records = tbody.find_all("tr")
            
            for row in records:
                cells = row.find_all("td")
                obj:dict = {}
                station = cells[0].text.strip()
                if len(cells) > 1:
                    # the "\u00b0" remove the degree icon and "[:-1]" to remove the C on end of each string
                    # temperature = float(cells[1].text.strip().replace("\u00b0", "")[:-1])
                    temperature = extractDigits(cells[1].text.strip())
                    obj = {
                        "station": station,
                        "temperature": temperature
                    }
                else:
                    obj =  station
                content.append(obj)
            return content

        lowTemperatureData = getRecords(lowestTemp)
        highTemperatureData = getRecords(highestTemp)
        time = getTimeNow()

        response = model.ResponseData(
            header=header,
            time_issued=f"{time}",
            valid_until = f"{time}",
            datas=model.TemperatureData(
                low_table=lowTemperatureData,
                high_table=highTemperatureData
            )
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
                weather=description,
                temperature=model.AsianTemperatureData(
                    high=highTemperature,
                    low=lowTemperature
                )
            )

            datas.append(data)
        
        response = model.ResponseData(
            header="Asian Cities Weather Forecast",
            time_issued=timeIssued,
            valid_until=validUntil,
            datas= datas
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
            dates = columns[1:]
            temperature = []

            for index, date in enumerate(dates, 0):
                description = date.find("img")['title']
                high = extractDigits(date.find("h5", {"class":"high-temp"}).text.strip())
                low = extractDigits(date.find("h5", {"class":"low-temp"}).text.strip())
              
                tempe = model.TouristAreasDates(
                    day=dayDateContainer[index]['day'],
                    date=dayDateContainer[index]['date'],
                    temperature=model.TouristAreasTemperature(
                        description=description,
                        high=high,
                        low=low
                    )
                )
                temperature.append(tempe)

            data = model.TouristAreasData(
                destination=destination,
                dates=temperature
            )
            datas.append(data)

        response = model.ResponseData(
            header=header,
            time_issued=timeIssued,
            valid_until=validUntil,
            datas=datas
        )
        mainResponse = model.MainResponse(response = response)

        return mainResponse
    
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")