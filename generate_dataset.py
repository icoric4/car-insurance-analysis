import random
import datetime

from utils import generate_birthdate, calculate_age, save_to_mongodb


def temporal_price_bias(starting_price, created_at):

    start_date = datetime.date.today() - datetime.timedelta(days=4 * 365)
    passed_days = (created_at - start_date).days

    passed_years = passed_days / 365
    price = starting_price + passed_years * 5
    return price

def generate_record(insurers, vehicle_models, start_date, end_date):
    num_days = random.randint(0, 4 * 365)
    created_at = datetime.date.today() - datetime.timedelta(
        days=num_days)
    end_date = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - \
        datetime.timedelta(days=num_days)).strftime('%Y-%m-%d')

    record = {
        "calculationData": {
            "data": {
                "huo": {
                    "vehicleModel": random.choice(vehicle_models)
                },
                "vehicle": {
                    "powerKw": random.randint(50, 200),
                    "productionYear": str(random.randint(2000, 2022))
                },
                "owner": {
                        "birthDate": generate_birthdate(start_date, end_date)
                },
                "registration": {
                    "prefix": random.choice(["ZG", "RI", "ST", "DU"])
                }
            }
        },
        "createdAt":created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "prices": []
    }
    age = calculate_age(record["calculationData"]["data"]["owner"]["birthDate"],
                        created_at)
    production_year = int(
        record["calculationData"]["data"]["vehicle"]["productionYear"])
    current_year = datetime.datetime.now().year
    car_age = current_year - production_year

    # Exclude insurers based on location, user age, and car age
    for insurer in insurers:
        exclude = False
        location = record["calculationData"]["data"]["registration"][
            "prefix"]
        if insurer == "insurer1":
            if location == "DU" and random.random() < 0.3:
                exclude = True
        elif insurer == "insurer6":
            if age < 25 and random.random() < 0.4:
                exclude = True
        elif insurer == "insurer3":
            if car_age > 10 and random.random() < 0.2:
                exclude = True

        # Exclude on random
        if random.random() < 0.05:
            exclude = True

        if not exclude:
            if insurer == "insurer1":
                mean = temporal_price_bias(150, created_at)
                price = round(random.gauss(mean, 20), 2)
            elif insurer == "insurer5":
                mean = temporal_price_bias(145, created_at)
                price = round(random.gauss(mean, 30), 2)
            else:
                mean = temporal_price_bias(145, created_at)
                price = round(random.gauss(mean, 40), 2)

            # Apply demographic biases
            if age <= 25:
                if insurer == 'insurer2':
                    price *= random.uniform(1.1, 1.2)
                elif insurer == 'insurer4':
                    price *= random.uniform(1.3, 1.6)
                elif insurer == 'insurer6':
                    price *= random.uniform(1.3, 1.6)
                else:
                    price *= random.uniform(1.2, 1.5)
            elif age >= 65:
                if insurer == 'insurer8':
                    price *= random.uniform(1.1, 1.25)
                elif insurer == 'insurer0':
                    price *= random.uniform(1.4, 1.65)
                else:
                    price *= random.uniform(1.3, 1.5)

            # Apply car age biases
            if car_age <= 5:
                if insurer == 'insurer1':
                    price *= random.uniform(0.7, 0.9)
                elif insurer == 'insurer5':
                    price *= random.uniform(0.8, 0.9)
                else:
                    price *= random.uniform(0.9, 1)
            elif car_age >= 10:
                if insurer == 'insurer7':
                    price *= random.uniform(1, 1.4)
                elif insurer == 'insurer6':
                    price *= random.uniform(1.2, 1.4)
                else:
                    price *= random.uniform(1.1, 1.3)

            # Apply location biases
            if location == 'ZG':
                if insurer == 'insurer4':
                    price *= random.uniform(1.2, 1.5)
                elif insurer == 'insurer9':
                    price *= random.uniform(1.3, 1.6)
                else:
                    price *= random.uniform(1.1, 1.3)
            elif location == 'ST':
                if insurer == 'insurer5':
                    price *= random.uniform(1.2, 1.5)
                elif insurer == 'insurer0':
                    price *= random.uniform(1.3, 1.65)
                else:
                    price *= random.uniform(1.1, 1.3)

            # Apply seasonality biases
            current_month = created_at.month
            if current_month in [12, 1, 2]:
                if insurer == 'insurer1':
                    price *= random.uniform(1.2, 1.4)
                elif insurer == 'insurer5':
                    price *= random.uniform(1.2, 1.5)
                else:
                    price *= random.uniform(1.1, 1.3)
            elif current_month in [6, 7, 8]:
                if insurer == 'insurer3':
                    price *= random.uniform(1.1, 1.2)
                elif insurer == 'insurer7':
                    price *= random.uniform(1.2, 1.3)
                else:
                    price *= random.uniform(1, 1.1)
            record["prices"].append({"brandCode": insurer,
                                     "totalAmount": price})

    return record


def generate_dataset(num_records):
    insurers = [f'insurer{i}' for i in range(10)]
    vehicle_models = [
        'TOYOTA, COROLLA, 1.4 D-4D',
        'HONDA, CIVIC, 1.8 i-VTEC',
        'BMW, 3 Series, 320d',
        'VOLKSWAGEN, PASSAT, 2.0 TDI',
        'FORD, FOCUS, 1.6 TDCi',
        'AUDI, A4, 2.0 TDI',
        'MERCEDES-BENZ, E-Class, E220d',
        'RENAULT, CLIO, 0.9 TCE',
        'HYUNDAI, TUCSON, 1.6 GDi',
        'KIA, CEED, 1.0 T-GDi',
        'NISSAN, JUKE, 1.0 DIG-T',
        'SEAT, LEON, 1.5 TSI',
        'SKODA, KODIAQ, 2.0 TDI',
        'TOYOTA, RAV4, 2.0 D-4D',
        'VOLVO, S60, 2.0 T8',
        'PEUGEOT, 3008, 1.6 PureTech',
        'MERCEDES-BENZ, GLC, GLC220d',
        'BMW, 5 Series, 520d',
        'AUDI, Q5, 2.0 TDI',
        'VOLKSWAGEN, TIGUAN, 2.0 TDI',
        'LAND ROVER, DISCOVERY, 2.0 SD4'
    ]

    start_date = '1950-01-01'
    end_date = '2004-12-31'

    dataset = []
    for _ in range(num_records):
        record = generate_record(insurers, vehicle_models, start_date, end_date)
        dataset.append(record)

    return dataset


def main():
    print('Generating dataset...')
    dataset = generate_dataset(50000)
    print('Dataset generated. Saving to MongoDB...')
    save_to_mongodb(dataset)
    print('Dataset saved to MongoDB.')

if __name__ == '__main__':
    main()
