import datetime
import random

from pymongo import MongoClient

def generate_birthdate(start_date, end_date):
    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    random_birthdate = start + datetime.timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )
    return random_birthdate.strftime('%Y-%m-%d')


def get_location_bias(insurer, registration):
    # Set different biases based on insurer and registration location
    if insurer == 'insurer1':
        if registration == 'ZG':
            return 1.4
        elif registration == 'RI':
            return 1.1
        elif registration == 'ST':
            return 1.0
        elif registration == 'DU':
            return 1.0
    elif insurer == 'insurer2':
        if registration == 'ZG':
            return 1.3
        elif registration == 'RI':
            return 1.3
        elif registration == 'ST':
            return 1.0
        elif registration == 'DU':
            return 1.0
    elif insurer == 'insurer4':
        if registration == 'ZG':
            return 1.4
        elif registration == 'RI':
            return 1.2
        elif registration == 'ST':
            return 1.0
        elif registration == 'DU':
            return 1.0
    else:
        if registration == 'ZG':
            return random.uniform(1.1, 1.3)
        elif registration == 'RI':
            return random.uniform(1.0, 1.2)
        elif registration == 'ST':
            return random.uniform(1.0, 1.2)
        elif registration == 'DU':
            return random.uniform(1.0, 1.2)
    return 1.0


def calculate_age(birth_date, created_at):
    birth_date = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    age = created_at.year - birth_date.year
    if created_at.month < birth_date.month or (
            created_at.month == birth_date.month
            and created_at.day < birth_date.day):
        age -= 1
    return age


def save_to_mongodb(dataset):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['insurance_db']
    collection = db['insurance_collection']
    collection.insert_many(dataset)
    client.close()


def truncate_mongodb():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['insurance_db']
    collection = db['insurance_collection']
    collection.delete_many({})
    client.close()