from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests, os, re

# Load env variables
load_dotenv()

BASE_URL = os.getenv("MANGA_BASE_URL")
router = APIRouter()

def extractDigits(string:str) -> int:
    string = string.replace(",", "") # remove all coma's
    pattern =  r'\d+'
    digit = re.search(pattern=pattern, string=string)
    if digit:
        return int(digit.group())
    return 0


@router.get("/")
async def main():
    try:
        URL:str = f"{BASE_URL}"
        content = requests.get(URL)
        scraper = BeautifulSoup(content.text, "html.parser")
        tableRanking = scraper.find("table",{'class':"top-ranking-table"})

        tableHeader = tableRanking.find("tr", {'class':"table-header"})

        # table header
        tableHeaderRows = [ h.text.strip() for h in tableHeader.find_all("td")]
        tableHeaderRows.pop(-2) # remove unnecessary column 
        tableRecordsRow = tableRanking.find_all("tr", {'class':"ranking-list"})
        datas = []
        for row in tableRecordsRow:
            columns = row.find_all("td")
            rank:int = int(columns[0].text.strip())
            title:str = columns[1].find("h3").text.strip()
            imageURL:str = columns[1].find("a").find("img")["data-src"]
            informations:list = columns[1].find("div", {'class':"information"}).text.strip().split('\n')
            volume = informations[0].strip()
            published = informations[1].strip()
            members = extractDigits(informations[2].strip())
            score:float = float(columns[2].find("span", {'class':"score-label"}).text.strip())
            obj = {
                    'rank':rank, 
                    'title': title,
                    'volume': volume,
                    'published': published,
                    'members': members,
                    'image_url': imageURL,
                    'score': score
                }

            datas.append(obj)
        return {'response': datas}
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def extractDataFromURL(url:str) -> any:
    response = {
        'title': '',
        
    }
    content = requests.get(url)
    scraper = BeautifulSoup(content.text, "html.parser")
    title = scraper.find("span", {'itemprop': "name"}).text.strip()
    response['title'] = title

    return response


@router.get("/top-mangas/")
async def topMangas():
    URL:str = f"{BASE_URL}"
    content = requests.get(URL)
    scraper = BeautifulSoup(content.text, "html.parser")
    tableRanking = scraper.find("table",{'class':"top-ranking-table"})
    tableRecordsRow = tableRanking.find_all("tr", {'class':"ranking-list"})
    anchors = [ a.find("td", {'class':"title"}).find("a", {'class':"hoverinfo_trigger"})["href"] for a in tableRecordsRow] # get hyperlink from each record
    datas = []
    for url in anchors[:2]:
        data = await extractDataFromURL(url)
        datas.append(data)
    response = {'response': datas}
    return response
