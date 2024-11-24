import project
import pytest

def test_read_serviceKey():
    assert project.read_service_key_from_text('serviceKey.txt')
    
@pytest.mark.asyncio
async def test_fetch_all_listings():
    service_key = project.read_service_key_from_text('serviceKey.txt')
    result = await project.fetch_all_listings(service_key=service_key)
    assert result