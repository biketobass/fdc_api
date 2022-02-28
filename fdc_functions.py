import pandas as pd
import json
import requests

# A few simple functions for accessing the information at FoodData
# Central (https://fdc.nal.usda.gov/). You will need to get an API
# key here: https://fdc.nal.usda.gov/api-key-signup.html

apikey = "cZngILx3FMisXOAIi4hC3860HUGONBU2Z1TwFbhO"
#apikey= "[Enter your API Key here]"


# Given an fdc_id, return the top level dictionary of information
# about that food. Unfortunately, different food types (branded,
# foundation food, etc.) return dictionaries with different
# information. This makes it difficult to have a uniform system for
# accessing information. More on that in the functions below. If you
# want info on only a subset of nutrients in the food, pass in a list
# of the nutrient ids you're interested in.
def get_food_by_fdcid(fdc_id, nutrient_list=None) :
    # Construct the URL
    base_url = "https://api.nal.usda.gov/fdc/v1/"
    url_end = "food/"+fdc_id
    url = base_url+url_end
    prms={'api_key' : apikey, "nutrients" : nutrient_list}
    # Make the api call, get the dictionary out of the json, and
    # return it.
    r = requests.get(url, params=prms)
    top_level_dict = r.json()
    print(top_level_dict['dataType'])
    return top_level_dict


# Get the serving size information after you have the top level
# dictionary returned by get_food_by_fdcid. This doesn't do much
# except print out some information including the serving size. In a
# real setting, you'd probably do something with that info. Note that
# what you do is different for different food types.
def get_serving_size(top_level_dict) :
    # For branded foods getting the serving size is easy. Use the
    # servingSize key.
    if top_level_dict["dataType"] == "Branded" :
        print(top_level_dict['brandOwner'], top_level_dict['description'], "Serving Size", top_level_dict['servingSize'],  top_level_dict['servingSizeUnit'], " UPC Code ", top_level_dict['gtinUpc'])
    elif (top_level_dict["dataType"] == "Foundation") or (top_level_dict["dataType"] == "SR Legacy"):
        # For Foundation foods or SR Legacy, we need the foodPortions key because
        # there is no servingSize key.
        food_portions_df = pd.DataFrame.from_dict(top_level_dict['foodPortions'])
        to_print = str(food_portions_df.loc[0]["amount"]) + " " + food_portions_df.loc[0]['measureUnit']['abbreviation'] + " (" + str(food_portions_df.loc[0]["gramWeight"]) + "g)"
        print(to_print)
    elif top_level_dict["dataType"] == "Survey (FNDDS)" :
        food_portions_df = pd.DataFrame.from_dict(top_level_dict['foodPortions'])
        to_print = str(food_portions_df.loc[0]["portionDescription"]) + " (" + str(food_portions_df.loc[0]["gramWeight"]) + "g)"
        print(to_print)



# Given the top level dictionary returned by get_food_by_fdcid, return
# a pandas Series containing info about a particular nutrient in that
# food.
#
# Takes the top level dictionary, and a nutrient ID.
def get_nutrient_info(top_level_dict, nutrient_id) :
    # Get the value of the 'foodNutrients' key. It's a list of
    # dictionaries. Turn that list into a DataFrame indexed by
    # nutrient number so that we can easily get the nutrients we want.
    # Step 1 is just to turn it into a dataframe.
    nutrients_df = pd.DataFrame.from_dict(top_level_dict['foodNutrients'])
    # The DF above has two columns we're interested in. One is called
    # 'nutrient' which is another dictionary which contains the detail
    # about a specific nutrient. The other is called 'amount' which
    # contains (you guessed it) the amount of that nutrient.

    # Step 2 is to turn the 'nutrient' column into a DF.
    nutrients_detail_df = pd.DataFrame.from_dict(nutrients_df['nutrient'].tolist())
    # Step 3: Add the 'amount' column to the DF you just created.
    nutrients_detail_df['amount'] = nutrients_df['amount']
    # Set the index to be the nutrient id.
    nutrients_detail_df = nutrients_detail_df.set_index("number")
    # Yay! Now we can access the information about a particular
    # nutrient, but beware! not all nutrients are in every food.
    try :
        return nutrients_detail_df.loc[nutrient_id]
    except KeyError :
        print("Nutrient not found.")



# Returns a DataFrame containing the results of the search for the
# query term.
def search_food(qury) :
    base_url = "https://api.nal.usda.gov/fdc/v1/"
    url_end = "foods/search"
    url = base_url+url_end
    # We'll just use the max page size to return.
    page_size = 200
    # Keep track of what page of the results we're on.
    page = 1
    # A DF to hold the results.
    resultsDF = pd.DataFrame()
    # Make requests until we have all of the results.
    while True :
        print('page = ', page)
        prms={'api_key' : apikey, 'query' : qury, 'pageSize' : page_size, 'pageNumber': str(page)}
        r = requests.get(url, params=prms)
        r = r.json()
        page_results_df = pd.DataFrame.from_dict(r['foods'])
        # Append this page of results to our main DF.
        resultsDF = resultsDF.append(page_results_df)
        # Conveniently, the results tell you how many total pages
        # there will be which makes it easy to check if we're at the
        # end of the results.
        if (page == r['totalPages']) :
            print('Breaking when page = ', page)
            break
        page += 1
    resultsDF = resultsDF.reset_index()
    return resultsDF


# Some examples.
#
# 1. Show that we can get serving size and nutrient info for branded,
# foundation, and survey foods.
#
# 2. Show how to search for a food.
def main() :
    # Example 1
    # This list holds the fdcids of a branded, foundation, survey food, sr legacy.
    fdc_ids = ["1106573", "321358", "1097512", "172454"]

    # If you want only a subset of nutrients specify them in the list.
    # If you want all nutrients return don't include a list.
    # nutrient_list = [208, 203, 205]

    for fdc_id in fdc_ids :
        # top_lev_dict = get_food_by_fdcid("1106573", nutrient_list)
        top_lev_dict = get_food_by_fdcid(fdc_id)
        # Get the serving information about this food and a bit more info
        # because we can.

        get_serving_size(top_lev_dict)
        # Get the information about a particular nutrient in this food.
        # Let's try it with protein.
        protein_series = get_nutrient_info(top_lev_dict, "203")
        print(protein_series, "\n")

    # Example 2
    # Search for a particular food.
    search_res_df = search_food("hummus")

    # Now find out some information about the first food in the
    # results. Again, in a real application we'd do something
    # interesting.
    fdc_id = str(search_res_df.loc[0]["fdcId"])
    top_lev_dict = get_food_by_fdcid(fdc_id)
    get_serving_size(top_lev_dict)
    protein_series = get_nutrient_info(top_lev_dict, "203")
    print(protein_series, "\n")



if __name__ == "__main__" :
    main()
