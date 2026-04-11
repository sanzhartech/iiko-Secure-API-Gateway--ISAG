import glob
import re

def fix_mocks():
    files = glob.glob("tests/test_*.py")
    
    # We will replace all occurrences of `mock_cm = AsyncMock()` etc with a simple helper block.
    # Actually, simpler is to just use a regex to replace the mock setup blocks.
    
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            
        # Pattern 1: test_jwt.py test_valid_token_accepted & test_rotated_key_token_accepted & test_no_kid_header_falls_back_to_primary
        # Also test_rbac.py get and post
        
        # It looks like:
        #        from unittest.mock import AsyncMock
        #        mock_response = httpx.Response(200, json={"ok": True})
        #        mock_cm = AsyncMock()
        #        mock_cm.__aenter__.return_value = mock_response
        #        mock_cm.__aexit__ = AsyncMock(return_value=None)
        #        mock_iiko.proxy_request_stream.return_value = mock_cm

        # We want to replace it with:
        helper = """        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield {mock_response}
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)"""

        # We can find `mock_response = ...` and then build it.
        pattern = re.compile(r'from unittest\.mock import AsyncMock\s+mock_response = (.*?)\s+mock_cm = AsyncMock\(\)\s+mock_cm\.__aenter__\.return_value = mock_response\s+mock_cm\.__aexit__ = AsyncMock\(return_value=None\)\s+mock_iiko\.proxy_request_stream\.return_value = mock_cm', re.DOTALL)
        
        def rep1(match):
            res_val = match.group(1)
            return f"""from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield {res_val}
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)"""
        
        content = pattern.sub(rep1, content)
        
        # Pattern 2: test_proxy.py test_upstream_timeout_returns_504
        #        mock_iiko.proxy_request_stream.side_effect = HTTPException(504, detail="Upstream service timed out")
        
        pattern_ex = re.compile(r'mock_iiko\.proxy_request_stream\.side_effect = (.*?)\n')
        def rep2(match):
            ex_val = match.group(1)
            return f"""from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            raise {ex_val}
            yield
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)
"""
        content = pattern_ex.sub(rep2, content)
        
        # Pattern 3: test_proxy.py test_server_headers_stripped_from_response
        #        mock_cm = AsyncMock()
        #        mock_cm.__aenter__.return_value = mock_response
        #        mock_iiko.proxy_request_stream.return_value = mock_cm
        pattern3 = re.compile(r'mock_cm = AsyncMock\(\)\s+mock_cm\.__aenter__\.return_value = mock_response\s+mock_iiko\.proxy_request_stream\.return_value = mock_cm', re.DOTALL)
        def rep3(match):
            return f"""from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _mock_cm(*args, **kwargs):
            yield mock_response
        from unittest.mock import MagicMock
        mock_iiko.proxy_request_stream = MagicMock(side_effect=_mock_cm)"""
        content = pattern3.sub(rep3, content)
        
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)

if __name__ == "__main__":
    fix_mocks()
