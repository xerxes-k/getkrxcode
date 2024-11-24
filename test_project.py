import project
import pytest
import pandas as pd

def test_read_serviceKey():
    assert project.read_service_key_from_text('serviceKey.txt')
    
def test_read_serviceKeywithdoublequotes():
    assert project.read_service_key_from_text('serviceKeywithdoublequotes.txt')

def test_read_serviceKeywithsinglequotes():
    assert project.read_service_key_from_text('serviceKeywithsinglequotes.txt')

def test_read_serviceKey_not_found():    
    with pytest.raises(FileNotFoundError):
        project.read_service_key_from_text('nonsense.txt')

@pytest.mark.asyncio
async def test_parse_stock_info_httpx():
    result = await project.parse_stock_info_httpx([]) 
    assert isinstance(result, pd.DataFrame)

@pytest.mark.asyncio
async def test_fetch_and_handle_stock_info():
    service_key = project.read_service_key_from_text('serviceKey.txt')   
    result = await project.fetch_and_handle_stock_info(service_key=service_key) 
    print(type(result))
    assert isinstance(result, pd.DataFrame)

@pytest.mark.asyncio
async def test_fetch_all_listings_async():
    service_key = project.read_service_key_from_text('serviceKey.txt')
    result = await project.fetch_all_listings_async(service_key=service_key)
    assert isinstance(result, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(result).__name__}"

def test_fetch_all_listings():
    service_key = project.read_service_key_from_text('serviceKey.txt')
    result = project.fetch_all_listings(service_key=service_key)
    assert isinstance(result, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(result).__name__}"
    
def test_main():
    result = project.main()    
    assert isinstance(result, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(result).__name__}"

def test_fetch_stock_by_name():
    service_key = project.read_service_key_from_text('serviceKey.txt')
    result = project.fetch_stock_by_name(service_key=service_key)
    assert isinstance(result, pd.DataFrame), f"Expected a pandas DataFrame, but got {type(result).__name__}"
    
def test_fetch_code_by_name():
    service_key = project.read_service_key_from_text('serviceKey.txt')
    result = project.fetch_code_by_name(service_key=service_key)
    assert isinstance(result, list), f"Expected a pandas list, but got {type(result).__name__}"