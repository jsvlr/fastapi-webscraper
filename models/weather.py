from pydantic import BaseModel
from typing import List,Union



class ResponseData(BaseModel):
    header: str
    time_issued: str
    valid_until: str
    datas: Union["TemperatureData", List["AsianCitiesData"], List["TouristAreasData"]]

class MainResponse(BaseModel):
    response: ResponseData

# For daily temperature
class StationTemperature(BaseModel):
    station:str
    temperature:Union[float, None]

class TemperatureData(BaseModel):
    low_table: Union[List[StationTemperature], List]
    high_table: Union[List[StationTemperature], List]

###################################

# asianCities Mpdel
class AsianTemperatureData(BaseModel):
    low: Union[float, None]
    high: Union[float, None]

class AsianCitiesData(BaseModel):
    country:str
    city:str
    weather:str
    temperature: AsianTemperatureData

################################

# touristAreasWeather Model
class TouristAreasData(BaseModel):
    destination:str
    dates:List["TouristAreasDates"]

class TouristAreasDates(BaseModel):
    day:str
    date:str
    temperature:"TouristAreasTemperature"

class TouristAreasTemperature(BaseModel):
    description:str
    high:Union[float, None]
    low:Union[float, None]

####################################
