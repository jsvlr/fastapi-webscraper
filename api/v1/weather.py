from fastapi import HTTPException, APIRouter, Query
from bs4 import BeautifulSoup
from typing_extensions import Annotated
from datetime import datetime as dt
import bs4
import requests



router = APIRouter()
BASE_URL = "https://www.pagasa.dost.gov.ph"


def getTimeNow() -> str:
    timeNow = dt.now()
    month:str = "0" + str(timeNow.month) if len(str(timeNow.month)) == 1 else str(timeNow.month)
    day:str = "0" + str(timeNow.day) if len(str(timeNow.day)) == 1 else str(timeNow.day)
    time:str = f"{month}-{day}-{timeNow.year}"

    return time

@router.get("/daily/", tags=['daily'])
async def dailyTemperature() -> dict:

    URL:str = f"{BASE_URL}/weather/low-high-temperature"
    content = requests.get(URL)
    scraper = BeautifulSoup(content.text, "html.parser")
    table:list = scraper.find_all("table", {"class":"table"})

    # Heading
    heading:str = scraper.find("div",{"id":"daily-weather-forecast"}).text.strip()
    
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
                obj = {
                    "station": station,
                    "temperature": cells[1].text.strip()
                }
            else:
                obj =  station
            content.append(obj)
        return content

    lowTemperatureData = getRecords(lowestTemp)
    highTemperatureData = getRecords(highestTemp)
    time = getTimeNow()

    # api model
    response = {
        "response":{
            "header":heading,
            "time": f"Temperature as of {time}",
            "datas":{          
                "low":lowTemperatureData,
                "high": highTemperatureData
              },
        }
    }

    return response

@router.get("/asian-cities/", tags=['asian-cities'])
async def asiaWeather(country: Annotated[str | None, Query(min_length=3, max_length=50)] = None):
    URL:str = f"{BASE_URL}/weather/weather-asian-cities-weather-forecast"
    content = requests.get(URL)
    scraper = BeautifulSoup(content.text, "html.parser")
    
    infos:list[str] = [info.text.strip() for info in scraper.find_all("h5")]

    timeIssued:str = infos[0]
    validUntil:str = infos[1]
    table = scraper.find("table", {"class":"table"})
    tbody = table.find("tbody")
    rows = tbody.find_all("tr")

    response = {
        'response':{
            'header':"Asian Cities Weather Forecast",
            'time_issued':timeIssued,
            'valid_until':validUntil,
            'datas':[]
        }
    }

    # if there is no query
    if not country:
        for row in rows:
            columns = row.find_all("td")
            station:list[str] = columns[0].text.strip().split(',')
            city:str = station[0].strip()
            country:str = station[-1].strip()
            description = columns[1].text.strip()
            highTemperature = columns[2].text.strip()
            lowTemperature = columns[3].text.strip()
            data:dict = {
                        'country': country,
                        'city':city,
                        'weather':description,
                        'temperature':{
                            'high':highTemperature,
                            'low':lowTemperature
                        }
                    }

            response['response']['datas'].append(data)


    return response