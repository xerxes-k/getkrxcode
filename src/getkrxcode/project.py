import httpx
from typing import Dict, Any
import pandas as pd
import asyncio
import nest_asyncio
nest_asyncio.apply()

# need to have serviceKey saved in a txt file named serviceKey.txt
def read_service_key_from_text(file_path: str) -> str:
    """
    Reads the serviceKey from a plain text file.
    
    Args:
        file_path (str): Path to the servicekey.txt file.
        
    Returns:
        str: The service key.
    """
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith("serviceKey"):
                return line.split("=", 1)[1].strip().strip('\"\'')
    raise ValueError("serviceKey not found in the file.")

# using default servicekey
# service_key = read_service_key_from_text('src\getkrxcode\serviceKey.txt')

# take base date and fetch all of the listing, returning a df
def main(
    service_key: str = 'service_key',
    result_type: str = 'json',
    basDt: str = '20241121',
    **kwargs,
) -> pd.DataFrame:
    kwargs.update({
        "service_key": service_key,
        "result_type": result_type,
        "basDt": basDt,
    })
    df = fetch_all_listings(**kwargs)
    return df

def fetch_all_listings(
    service_key: str,
    result_type: str = "json",
    basDt: str = '20241121',
    **kwargs,
) -> pd.DataFrame:
    kwargs.update({
        "service_key": service_key,
        "result_type": result_type,
        "basDt": basDt,
    })
    return asyncio.run(
        fetch_all_listings_async(**kwargs)
        )

async def fetch_all_listings_async(
    service_key: str,
    result_type: str = "json",
    basDt: str = '20241121',
    **kwargs
) -> pd.DataFrame:
    """
    Fetch all stock listings for a given base date, handling pagination.

    Args:
        service_key (str): Your API key.
        result_type (str): Format of the response, 'json' or 'xml'. Default is 'json'.
        basDt (str): Base date for filtering data (default: '20241121'). If omitted, the API returns all data, potentially exceeding 3 million items.

    Returns:
        pd.DataFrame: DataFrame containing all stock listings.
    """
    all_items = []  # To store all records
    page_no = 1
    num_of_rows = 10000
    
    kwargs.update({
        "service_key": service_key,
        "result_type": result_type,
        "basDt": basDt,
        "page_no": page_no,
        "num_of_rows": num_of_rows,        
    })

    while True:
        # Fetch data for the current page
        response = await fetch_and_handle_stock_info(**kwargs)        

        # Check if there's an error in the response
        if "error" in response:
            print(f"Error on page {page_no}: {response['error']}")
            break


        # Append to the list of all items
        if response.empty:
            break  # Stop when no more data is returned
        all_items.append(response)

        # Increment page number for the next request
        page_no += 1

        # Stop if fewer rows than expected are returned (last page)
        if len(response) < num_of_rows:
            break

    # Combine all DataFrames into one
    if all_items:
        final_df = pd.concat(all_items, ignore_index=True)
    else:
        final_df = pd.DataFrame()  # Return an empty DataFrame if no data

    return final_df


async def fetch_and_handle_stock_info(
    service_key: str,
    num_of_rows: int = 10,
    page_no: int = 1,
    result_type: str = "json",
    basDt: str = '20241121',
    **kwargs
) -> pd.DataFrame:
    """
    Fetch stock information from the KRX Listed Stocks API and handle errors.

    Args:
        service_key (str): Your API key.
        num_of_rows (int): Number of rows per page (default is 10).
        page_no (int): Page number to fetch (default is 1).
        result_type (str): Format of the response, either 'xml' or 'json' (default is 'json').
        kwargs: Additional query parameters (e.g., basDt, likeIsinCd, etc.).

    Returns:
        Dict[str, Any]: Parsed JSON response or interpreted error message.
    """
    base_url = "https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo"
    params = {
        "serviceKey": service_key,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
        "resultType": result_type,
        "basDt": basDt,
        **kwargs,
    }

    async with httpx.AsyncClient() as client:
        try:
            # Send the GET request
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            # curiously api returns 200 when service key is not registered. so manually pulling it out.
            if "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in str(response.content):
                raise ValueError("Service key is invalid or not recognized.")

            # Parse JSON if the response is in JSON format
            if result_type.lower() == "json":
                data = response.json()
                # Check for API-specific error codes
                result_code = data.get("response", {}).get("header", {}).get("resultCode", "")
                if result_code != "00":
                    error_message = interpret_error_code_httpx(result_code)
                    raise ValueError(f"API returned error of {result_code}: {error_message}")
                return await parse_stock_info_httpx(data)
            else:
                return response.text

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error occurred: {e}"}

def interpret_error_code_httpx(error_code: str) -> str:
    """
    Interpret the error code from the API.

    Args:
        error_code (str): Error code from the API response.

    Returns:
        str: Human-readable error message.
    """
    error_messages = {
        "1": "Application error",
        "10": "Invalid request parameter",
        "12": "No OpenAPI service or deprecated service",
        "20": "Access denied",
        "22": "Request limit exceeded",
        "30": "Service key not registered",
        "31": "Service key expired",
        "32": "IP not registered",
        "99": "Unknown error",
    }
    return error_messages.get(error_code, "Unknown error code")


async def parse_stock_info_httpx(response: Dict[str, Any]) -> pd.DataFrame:
    """
    Parse stock information from the API response and return it as a DataFrame.

    Args:
        response (Dict[str, Any]): The API response as a dictionary.

    Returns:
        pd.DataFrame: A DataFrame containing the parsed stock information.
    """
    if "response" not in response or "body" not in response["response"]:
        print("Invalid response format")
        return pd.DataFrame()

    items = response["response"]["body"].get("items", {}).get("item", [])
    if not items:
        print("No stock information found. Check if Bsdt is a business day.")
        return pd.DataFrame()

    # Create a list of dictionaries to build the DataFrame
    data = [
        {
            "Stock Name": item.get("itmsNm", "N/A"),
            "Corporation Name": item.get("corpNm", "N/A"),
            "KRX Stock Code": item.get("srtnCd", "N/A"),
            "Corporation Reg Number": item.get("crno", "N/A"),
            "Market Type": item.get("mrktCtg", "N/A"),
        }
        for item in items
    ]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df



# take name either in Korean and return the stock
def fetch_stock_by_name(
    service_key: str,
    result_type: str = "json",
    basDt: str = '20241121',
    likeItmsNm: str = '삼성전자',
    **kwargs
) -> pd.DataFrame:
    """
    takes a Korean keyword and returns the results that includes the keyword
    returns 10 results by default, pass num_of_rows to change
    """
    kwargs.update({
        "service_key": service_key,
        "result_type": result_type,
        "basDt": basDt,
        "likeItmsNm":likeItmsNm,
    })
    return asyncio.run(fetch_and_handle_stock_info(**kwargs))

# take name either in Korean or English and return the code to be fed into TradingView
def fetch_code_by_name(
    service_key: str,
    result_type: str = "json",
    basDt: str = '20241121',
    likeItmsNm: str = '삼성전자',
    **kwargs
) -> list:
    """
    takes a Korean keyword and returns a list of stock codes that can be fed into TradingView
    returns 10 results by default, pass num_of_rows to change
    """
    kwargs.update({
        "service_key": service_key,
        "result_type": result_type,
        "basDt": basDt,
        "likeItmsNm":likeItmsNm,
    })
    df = asyncio.run(fetch_and_handle_stock_info(**kwargs))
    try:
        result = df['KRX Stock Code'].str.replace("^A", "KRX:", regex=True).to_list()
        return result
    except KeyError:
        print("No stock information found. Check if company name is correct.")


if __name__ == "__main__":
    main()