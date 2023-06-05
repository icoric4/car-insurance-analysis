# Car Insurance Pricing Analysis Project

This project aims to analyze car insurance pricing data and provide insights to
insurance companies. The analysis is performed using Python and MongoDB.

## Setup

To set up the project, follow these steps:

1. Install Docker on your machine.
2. Clone this repository.
3. Open a terminal and navigate to the project directory.
4. Run the following command to start the MongoDB container:
   ```
   docker-compose up -d
   ```

## Dependencies

Make sure you have the necessary Python dependencies installed. To install them,
run the following command in your terminal:

```
pip install -r requirements.txt
```

## Dataset Generation

Before performing the analysis, you need to generate the car insurance pricing
dataset. This can be done by running the following command:

```
python generate_dataset.py
```

The script will generate a dataset with realistic car insurance pricing data
based on various factors.

## Analysis

To analyze the car insurance pricing data and generate insights, run the
following command:

```
python analyze.py
```
This command generates analysis in form of figures saved in [figures](figures/) folder.

The analysis script will perform various calculations and generate insights
regarding pricing differences among insurers, demographic breakdowns, location,
car age, and seasonality.

For a more detailed overview of the brainstorming session conducted for this
project, please refer to [this](Brainstorming%20session.pdf) file.

The comprehensive analysis report can be found
in [this](Analysis%20of%20Insurer%20Data.pdf) file.

## Conclusion

This project offers a starting point for car insurance pricing analysis. By
leveraging the generated dataset and the provided analysis script, insurance
companies can gain valuable insights into pricing strategies, demographic
preferences, seasonality effects, and more. The project can be expanded upon to
include additional analyses and data products to further enhance pricing
optimization and competitive monitoring efforts.
