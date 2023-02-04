#!/usr/bin/python

from datetime import date, datetime, timedelta
from lxml import html

import requests
import calendar
import pytz
import re
import boto3


def parseCalendar(ddb_table, year):
    url = 'http://www.seasky.org/astronomy/astronomy-calendar-%s.html'
    page = requests.get(url % year)
    dom = html.fromstring(page.text)

    events = dom.xpath('//div[@id="right-column-content"]/ul/li/p')

    print('Processing the year %i which contains %i events.' %
          (year, len(events)))

    for event in events:
        date = getDate(event, year)
        summary = getSummary(event)
        description = getDescription(event)

        # print(getID(date, summary))
        # print(dateToInt(date[0]))
        # print(dateToInt(date[1]))
        # print(summary)
        # print(description)

        ddb_table.put_item(
            Item={
                'ID': getID(date, summary),
                'DateStart': dateToInt(date[0]),
                'DateEnd': dateToInt(date[1]),
                'Summary': summary,
                'Description': description,
            }
        )


def getDate(event, year):
    raw = ''.join(event.xpath('span[@class="date-text"]/text()'))
    month = list(calendar.month_name).index(
        ''.join(re.findall('[a-zA-Z]+', raw)))
    days = [int(day) for day in re.findall('\d+', raw)]

    return (date(year, month, days[0]), getNextDay(date(year, month, days[-1])))


def dateToInt(date: date) -> int:
    return date.year * 10000 + date.month * 100 + date.day


def getNextDay(date):
    return date + timedelta(days=1)


def getSummary(event):
    return ''.join(event.xpath('span[@class="title-text"]/text()')).rstrip(' .')


def getDescription(event):
    return ''.join(event.xpath('text()')).strip(' -')

def getID(date, summary):
    summary   = ''.join(summary.lower().split(' '))
    timestamp = ''.join(map(lambda x: x.strftime('%Y%m%d'), date))

    return summary + '_' + timestamp


def main():
    # Init aws resources
    dynamodb = boto3.resource('dynamodb', region_name="us-west-2")
    table = dynamodb.Table('astronomy-events')
    print(table.creation_date_time)

    for year in range(2015, 2031):
        calendar = parseCalendar(table, year)


if __name__ == "__main__":
    main()
