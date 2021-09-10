import pyxivapi
from pyxivapi.models import Filter, Sort

import config


async def fetch_example_results(search):
    client = pyxivapi.XIVAPIClient(api_key=config.xivapi_key)

    filters = [
        Filter("LevelItem", "gte", 100)
    ]

    sort = Sort("LevelItem", True)

    item = await client.index_search(
        name=search,
        indexes=["Item"],
        columns=["ID"],
        filters=[],
        sort=[],
        language="en"
    )

    await client.session.close()
    return item


