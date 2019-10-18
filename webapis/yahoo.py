def etf_components(symbol):
    from bs4 import BeautifulSoup
    from urllib.request import urlopen
    url="https://finance.yahoo.com/quote/%5E" + symbol + "/components/"
    page = urlopen(url)
    soup = BeautifulSoup(page)
    components = [c.contents[0].text for c in soup.find_all(text="Company Name")[0].parent.parent.parent.parent.parent.contents[1].contents]
    return components

