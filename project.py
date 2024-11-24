import httpx
from typing import Dict, Any
import pandas as pd
import asyncio

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
                return line.split("=", 1)[1].strip()
    raise ValueError("serviceKey not found in the file.")

# using default servicekey
service_key = read_service_key_from_text('serviceKey.txt')

# take base date and fetch all of the listing, returning a df
async def main(
    service_key: str = service_key,
    result_type: str = 'json',
    basDt: str = '20241121'
) -> pd.DataFrame:
        
    return fetch_all_listings(service_key=service_key, result_type=result_type, basDt=basDt)


async def fetch_all_listings(
    service_key: str,
    result_type: str = "json",
    basDt: str = '20241121'
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

    while True:
        # Fetch data for the current page
        response = await fetch_and_handle_stock_info(
            service_key=service_key,
            num_of_rows=num_of_rows,
            page_no=page_no,
            result_type=result_type,
            basDt=basDt
        )

        # Check if there's an error in the response
        if "error" in response:
            print(f"Error on page {page_no}: {response['error']}")
            break

        # Parse the response into a DataFrame
        df = await parse_stock_info_httpx(response)

        # Append to the list of all items
        if df.empty:
            break  # Stop when no more data is returned
        all_items.append(df)

        # Increment page number for the next request
        page_no += 1

        # Stop if fewer rows than expected are returned (last page)
        if len(df) < num_of_rows:
            break

    # Combine all DataFrames into one
    if all_items:
        final_df = pd.concat(all_items, ignore_index=True)
    else:
        final_df = pd.DataFrame()  # Return an empty DataFrame if no data

    return final_df


async def fetch_and_handle_stock_info(
    service_key: str,
    num_of_rows: int = 1,
    page_no: int = 1,
    result_type: str = "json",
    basDt: str = '20241121',
    **kwargs
) -> Dict[str, Any]:
    """
    Fetch stock information from the KRX Listed Stocks API and handle errors.

    Args:
        service_key (str): Your API key.
        num_of_rows (int): Number of rows per page (default is 1).
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

            # Parse JSON if the response is in JSON format
            if result_type.lower() == "json":
                data = response.json()
                # Check for API-specific error codes
                result_code = data.get("response", {}).get("header", {}).get("resultCode", "")
                if result_code != "00":
                    error_message = interpret_error_code_httpx(result_code)
                    return {"error": f"API returned error: {error_message}"}
                return data
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
        print("Invalid response format.")
        return pd.DataFrame()

    items = response["response"]["body"].get("items", {}).get("item", [])
    if not items:
        print("No stock information found.")
        return pd.DataFrame()

    # Create a list of dictionaries to build the DataFrame
    data = [
        {
            "Stock Name": item.get("itmsNm", "N/A"),
            "Corporation Name": item.get("corpNm", "N/A"),
            "KRX Stock Code": item.get("srtnCd", "N/A"),
            "Market Type": item.get("mrktCtg", "N/A"),
        }
        for item in items
    ]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df



# take name either in Korean or English and return the code

# take name either in Korean or English and return the code to be fed into TradingView

if __name__ == "__main__":
    asyncio.run(main())