from pydantic import BaseModel
from typing import List,Union


class MainResponse(BaseModel):
    response: "ResponseData"
class ResponseData(BaseModel):
    header: str
    time_issued: str
    valid_until: str
    locations: Union[List["StationTemperature"], List["AsianCitiesData"], List["TouristAreasData"]]

# For daily temperature
class StationTemperature(BaseModel):
    place:str
    temperature:Union[float, None]

###################################

# asianCities Mpdel
class AsianTemperatureData(BaseModel):
    low: Union[float, None]
    high: Union[float, None]

class AsianCitiesData(BaseModel):
    country:str
    city:str
    temperature_description:str
    temperature_high:Union[float, None]
    temperature_low:Union[float, None]

################################

# touristAreasWeather Model
class TouristAreasData(BaseModel):
    place:str
    areas:str
    dates:List["TouristAreasDates"]

class TouristAreasDates(BaseModel):
    day:str
    date:str
    temperature_description:str
    temperature_high:Union[float, None]
    temperature_low:Union[float, None]

####################################
