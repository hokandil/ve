
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

async def verify_centrifugo():
    # Mock settings
    with patch('app.core.config.settings.CENTRIFUGO_API_URL', "http://mock-url"), \
         patch('app.core.config.settings.CENTRIFUGO_API_KEY', "mock-key"):
        
        # Mock cent Client
        with patch('app.core.centrifugo.Client') as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            
            from app.core.centrifugo import get_centrifugo_client
            
            client = get_centrifugo_client()
            
            # Test publish
            await client.publish("test-channel", {"data": "test"})
            
            # Verify call
            # Note: The client in centrifugo.py is initialized at module level, 
            # so patching Client class might not affect the already initialized instance 
            # unless we reload the module or patch the instance directly.
            
            # Let's patch the instance method directly
            client.client.publish = AsyncMock()
            await client.publish("test-channel", {"data": "test"})
            
            client.client.publish.assert_called_with("test-channel", {"data": "test"})
            print("Centrifugo publish verified successfully")

from unittest.mock import AsyncMock
if __name__ == "__main__":
    asyncio.run(verify_centrifugo())
