import calendar
import os
from collections import defaultdict
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from pymongo import MongoClient

matplotlib.use('agg')


SIGNIFICANT_PRICE_DIFFERENCE = 50


def main():
    # MongoDB connection
    client = MongoClient("mongodb://localhost:27017")
    db = client["insurance_db"]
    collection = db["insurance_collection"]
    cmap = LinearSegmentedColormap.from_list('custom',
                                             ['green', 'white', 'red'])

    # Overall analysis
    pipeline = [
        {
            "$unwind": "$prices"
        },
        {
            "$group": {
                "_id": "$prices.brandCode",
                "prices": {"$push": "$prices.totalAmount"},
            }
        },
        {"$unwind": "$prices"},
        {"$sort": {"prices": 1}},
        {
            "$group": {
                "_id": "$_id",
                "avg": {"$avg": "$prices"},
                "minPrice": {"$first": "$prices"},
                "maxPrice": {"$last": "$prices"},
                "prices": {"$push": "$prices"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 1,
                "avg": 1,
                "minPrice": 1,
                "maxPrice": 1,
                "percentile25": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.25, "$count"]}}]},
                "median": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.5, "$count"]}}]},
                "percentile75": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.75, "$count"]}}]},
                "prices": 1,
            }
        },
    ]

    results = list(collection.aggregate(pipeline))

    results.sort(key=lambda x: x['_id'])
    insurers = [result['_id'] for result in results]
    prices = [result['prices'] for result in results]

    median_all = np.median(np.concatenate(prices))
    diff = [(np.median(prices_insurer) -
             median_all) / SIGNIFICANT_PRICE_DIFFERENCE + 0.5
            for prices_insurer in prices]

    fig, ax = plt.subplots()
    boxplots = ax.boxplot(prices, patch_artist=True, showfliers=False)

    for patch, color in zip(boxplots['boxes'], cmap(diff)):
        patch.set_facecolor(color)

    ax.set_xticklabels(insurers)
    ax.set_ylabel('Price')
    ax.set_title('Insurance Prices by Insurer')
    ax.tick_params(axis='x', rotation=20)

    folder_path = './figures'

    file_path = os.path.join(folder_path, 'insurers_prices_boxplot.png')
    plt.savefig(file_path)

    # Age breakdown
    pipeline_age = [
        {
            "$unwind": "$prices"
        },
        {
            "$group": {
                "_id": {
                    "insurer": "$prices.brandCode",
                    "age": {
                        "$subtract": [
                            {"$year": datetime.now()},
                            {"$year": {"$dateFromString": {
                                "dateString":
                                    "$calculationData.data.owner.birthDate"}}}
                        ]
                    }
                },
                "prices": {"$push": "$prices.totalAmount"},
            }
        },
        {"$unwind": "$prices"},
        {"$sort": {"prices": 1}},
        {
            "$group": {
                "_id": "$_id",
                "avg": {"$avg": "$prices"},
                "minPrice": {"$first": "$prices"},
                "maxPrice": {"$last": "$prices"},
                "prices": {"$push": "$prices"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "insurer": "$_id.insurer",
                "age": "$_id.age",
                "avg": 1,
                "minPrice": 1,
                "maxPrice": 1,
                "percentile25": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.25, "$count"]}}]},
                "median": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.5, "$count"]}}]},
                "percentile75": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.75, "$count"]}}]},
                "prices": 1,
            }
        },
    ]

    results_age = list(collection.aggregate(pipeline_age))

    # Grouping age categories
    age_groups = {
        '18-24': {'min': 0, 'max': 24},
        '25-65': {'min': 25, 'max': 65},
        '65+': {'min': 66, 'max': float('inf')}
    }

    # Grouping prices by age category and insurer
    grouped_prices = {group: {result['insurer']: [] for result in results_age}
                      for group in age_groups}

    for result in results_age:
        for group, age_range in age_groups.items():
            if age_range['min'] <= result['age'] <= age_range['max']:
                grouped_prices[group][result['insurer']].extend(
                    result['prices'])
                break

    fig, axes = plt.subplots(nrows=len(age_groups), ncols=1, figsize=(10, 8))

    for idx, (group, prices_by_insurer) in enumerate(grouped_prices.items()):
        ax = axes[idx]
        insurers_sorted = sorted(prices_by_insurer.keys())

        median_all = np.median(np.concatenate([prices_by_insurer[insurer]
                                               for insurer in
                                               prices_by_insurer]))
        diff = [(np.median(prices_by_insurer[insurer]) -
                 median_all) / SIGNIFICANT_PRICE_DIFFERENCE + 0.5
                for insurer in insurers_sorted]

        boxplots = ax.boxplot([prices_by_insurer[insurer]
                               for insurer in insurers_sorted],
                              patch_artist=True, showfliers=False)
        for patch, color in zip(boxplots['boxes'], cmap(diff)):
            patch.set_facecolor(color)

        ax.set_xticklabels(insurers_sorted)
        ax.set_ylabel('Price')
        ax.set_xlabel('Insurer')
        ax.set_title(f'Insurance Prices by Insurer - Age Group: {group}')

    fig.tight_layout()

    folder_path = './figures'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path,
                             'insurance_prices_age_insurer_boxplot.png')
    plt.savefig(file_path)

    # Car age breakdown
    pipeline_car_age = [
        {
            "$unwind": "$prices"
        },
        {
            "$addFields": {
                "carAgeGroup": {
                    "$let": {
                        "vars": {
                            "carAge": {
                                "$subtract": [
                                    {"$year": datetime.now()},
                                    {
                                        "$toInt":
                                "$calculationData.data.vehicle.productionYear"},
                                ]
                            }
                        },
                        "in": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$lt": ["$$carAge", 5]},
                                     "then": "Below 5 years"},
                                    {"case": {"$lt": ["$$carAge", 10]},
                                     "then": "5 to 10 years"},
                                    {"case": {"$lt": ["$$carAge", 15]},
                                     "then": "10 to 15 years"},
                                    {"case": {"$lt": ["$$carAge", 20]},
                                     "then": "15 to 20 years"},
                                    {"case": {"$lt": ["$$carAge", 25]},
                                     "then": "20 to 25 years"}
                                ],
                                "default": "Above 25 years"
                            }
                        }
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "insurer": "$prices.brandCode",
                    "carAgeGroup": "$carAgeGroup"
                },
                "prices": {"$push": "$prices.totalAmount"},
            }
        },
        {"$unwind": "$prices"},
        {"$sort": {"prices": 1}},
        {
            "$group": {
                "_id": "$_id",
                "avg": {"$avg": "$prices"},
                "minPrice": {"$first": "$prices"},
                "maxPrice": {"$last": "$prices"},
                "prices": {"$push": "$prices"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "insurer": "$_id.insurer",
                "carAgeGroup": "$_id.carAgeGroup",
                "avg": 1,
                "minPrice": 1,
                "maxPrice": 1,
                "percentile25": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.25, "$count"]}}]},
                "median": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.5, "$count"]}}]},
                "percentile75": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.75, "$count"]}}]},
                "prices": 1,
            }
        },
    ]

    results_car_age = list(collection.aggregate(pipeline_car_age))

    grouped_prices = defaultdict(lambda: {})
    for result in results_car_age:
        grouped_prices[result['carAgeGroup']][result['insurer']] = result[
            'prices']

    # Creating subplots for each car age category
    fig, axes = plt.subplots(nrows=len(grouped_prices), ncols=1,
                             figsize=(10, 20),
                             sharey=True)

    for idx, group in enumerate(['Below 5 years', '5 to 10 years',
                                 '10 to 15 years', '15 to 20 years',
                                 '20 to 25 years']):
        prices_by_insurer = grouped_prices[group]
        ax = axes[idx]
        insurers_sorted = sorted(prices_by_insurer.keys())

        median_all = np.median([np.median(prices_by_insurer[insurer])
                                for insurer in insurers_sorted])
        diff = [(np.median(prices_by_insurer[insurer]) -
                 median_all)/SIGNIFICANT_PRICE_DIFFERENCE + 0.5
                for insurer in insurers_sorted]

        boxplots = ax.boxplot([prices_by_insurer[insurer]
                               for insurer in insurers_sorted],
                              patch_artist=True, showfliers=False)

        for patch, color in zip(boxplots['boxes'], diff):
            patch.set_facecolor(cmap(color))

        ax.set_xticklabels(insurers_sorted)
        ax.set_ylabel('Price')
        ax.set_xlabel('Insurer')
        ax.set_title(f'Insurance Prices by Insurer - Car Age Group: {group}')

    # Adjusting the spacing between subplots
    fig.tight_layout()

    # Save the figure to a file
    folder_path = './figures'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path,
                             'insurance_prices_car_age_insurer_boxplot.png')
    plt.savefig(file_path)

    # Location breakdown
    pipeline_location = [
        {
            "$unwind": "$prices"
        },
        {
            "$group": {
                "_id": {
                    "insurer": "$prices.brandCode",
                    "location": "$calculationData.data.registration.prefix"
                },
                "prices": {"$push": "$prices.totalAmount"},
            }
        },
        {"$unwind": "$prices"},
        {"$sort": {"prices": 1}},
        {
            "$group": {
                "_id": "$_id",
                "avg": {"$avg": "$prices"},
                "minPrice": {"$first": "$prices"},
                "maxPrice": {"$last": "$prices"},
                "prices": {"$push": "$prices"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "insurer": "$_id.insurer",
                "location": "$_id.location",
                "avg": 1,
                "minPrice": 1,
                "maxPrice": 1,
                "percentile25": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.25, "$count"]}}]},
                "median": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.5, "$count"]}}]},
                "percentile75": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.75, "$count"]}}]},
                "prices": 1,
            }
        },
    ]

    results_location = list(collection.aggregate(pipeline_location))

    grouped_prices = defaultdict(lambda: {})
    for result in results_location:
        grouped_prices[result['location']][result['insurer']] = result['prices']

    # Creating subplots for each location
    fig, axes = plt.subplots(nrows=len(grouped_prices), ncols=1,
                             figsize=(10, 20))

    for idx, location in enumerate(['ZG', 'ST', 'RI', 'DU']):
        prices_by_insurer = grouped_prices[location]
        ax = axes[idx]
        insurers_sorted = sorted(prices_by_insurer.keys())
        median_all = np.median([np.median(prices_by_insurer[insurer])
                                for insurer in insurers_sorted])
        diff = [(np.median(prices_by_insurer[insurer]) -
                 median_all)/SIGNIFICANT_PRICE_DIFFERENCE + 0.5
                for insurer in insurers_sorted]

        boxplots = ax.boxplot([prices_by_insurer[insurer]
                               for insurer in insurers_sorted],
                              patch_artist=True, showfliers=False)

        for patch, color in zip(boxplots['boxes'], diff):
            patch.set_facecolor(cmap(color))

        ax.set_xticklabels(insurers_sorted)
        ax.set_ylabel('Price')
        ax.set_xlabel('Insurer')
        ax.set_title(f'Insurance Prices by Insurer - Location: {location}')

    # Adjusting the spacing between subplots
    fig.tight_layout()

    # Save the figure to a file
    folder_path = './figures'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path,
                             'insurance_prices_location_insurer_boxplot.png')
    plt.savefig(file_path)

    # Seasonality breakdown analysis
    pipeline_seasonality = [
        {
            "$unwind": "$prices"
        },
        {
            "$project": {
                "insurer": "$prices.brandCode",
                "month": {"$month": {"$toDate": "$createdAt"}},
                "price": "$prices.totalAmount"
            }
        },
        {
            "$group": {
                "_id": {
                    "insurer": "$insurer",
                    "month": "$month"
                },
                "prices": {"$push": "$price"},
            }
        },
        {"$unwind": "$prices"},
        {"$sort": {"prices": 1}},
        {
            "$group": {
                "_id": "$_id",
                "avg": {"$avg": "$prices"},
                "minPrice": {"$first": "$prices"},
                "maxPrice": {"$last": "$prices"},
                "prices": {"$push": "$prices"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "insurer": "$_id.insurer",
                "month": "$_id.month",
                "avg": 1,
                "minPrice": 1,
                "maxPrice": 1,
                "percentile25": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.25, "$count"]}}]},
                "median": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.5, "$count"]}}]},
                "percentile75": {"$arrayElemAt": ["$prices", {
                    "$ceil": {"$multiply": [0.75, "$count"]}}]},
                "prices": 1,
            }
        },
        {"$sort": {"insurer": 1, "month": 1}}
    ]

    results_seasonality = list(collection.aggregate(pipeline_seasonality))

    grouped_prices = defaultdict(lambda: {})
    for result in results_seasonality:
        grouped_prices[result['month']][result['insurer']] = result['prices']

    months = list(grouped_prices.keys())
    months_textual = [calendar.month_name[int(month)] for month in months]

    fig, axes = plt.subplots(nrows=len(months), ncols=1, figsize=(15, 30))
    for idx, month in enumerate(months):
        ax = axes[idx]
        insurers_sorted = sorted(grouped_prices[month].keys())
        prices_month = [grouped_prices[month][insurer] for insurer in
                        insurers_sorted]

        median_all = np.median(np.concatenate(prices_month))
        diff = [(np.median(prices) -
                    median_all)/SIGNIFICANT_PRICE_DIFFERENCE + 0.5
                    for prices in prices_month]

        boxplot = ax.boxplot(prices_month, patch_artist=True,
                             labels=insurers_sorted, showfliers=False)

        for patch, color in zip(boxplot['boxes'], diff):
            patch.set_facecolor(cmap(color))

        ax.set_xlabel('Insurer')
        ax.set_ylabel('Price')
        ax.set_title(f'Insurance Prices by Insurer - {months_textual[idx]}')

    # Adjust the spacing between subplots
    fig.tight_layout()

    # Save the figure to a file
    folder_path = './figures'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path,
                             'insurance_prices_seasonality_insurer_boxplot.png')
    plt.savefig(file_path)


if __name__ == '__main__':
    main()