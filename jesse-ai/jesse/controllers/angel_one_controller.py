"""
Angel One Authentication Controller
Handles login and session management for Angel One broker
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from SmartApi import SmartConnect
import pyotp
import jesse.helpers as jh

router = APIRouter(prefix="/angel-one", tags=["Angel One"])

# Store the authenticated session globally (can be moved to Redis for production)
angel_one_session = {
    "authenticated": False,
    "smart_api": None,
    "session_data": None,
    "client_code": None,
    "api_key": None,
    "feed_token": None,
    "jwt_token": None
}


class AngelOneLoginRequest(BaseModel):
    client_code: str
    api_key: str
    pin: str
    totp_key: str


class AngelOneLoginResponse(BaseModel):
    success: bool
    message: str
    client_code: str = None


@router.post("/login", response_model=AngelOneLoginResponse)
def angel_one_login(request: AngelOneLoginRequest):
    """
    Authenticate with Angel One using provided credentials.
    The TOTP key is used to generate the 6-digit OTP automatically.
    """
    global angel_one_session
    
    try:
        # Validate inputs
        if not request.client_code or not request.api_key or not request.pin or not request.totp_key:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "All fields are required"
                }
            )
        
        # Initialize SmartConnect
        smart_api = SmartConnect(api_key=request.api_key)
        
        # Generate TOTP from the secret key
        try:
            totp = pyotp.TOTP(request.totp_key).now()
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Invalid TOTP key format: {str(e)}"
                }
            )
        
        # Generate session with Angel One
        data = smart_api.generateSession(request.client_code, request.pin, totp)
        
        if data.get('status'):
            # Store session data globally
            angel_one_session = {
                "authenticated": True,
                "smart_api": smart_api,
                "session_data": data.get('data'),
                "client_code": request.client_code,
                "api_key": request.api_key,
                "feed_token": data.get('data', {}).get('feedToken'),
                "jwt_token": data.get('data', {}).get('jwtToken')
            }
            
            jh.info(f"Angel One login successful for client: {request.client_code}")
            
            return {
                "success": True,
                "message": "Login successful!",
                "client_code": request.client_code
            }
        else:
            error_msg = data.get('message', 'Unknown error')
            jh.error(f"Angel One login failed: {error_msg}")
            
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": f"Authentication failed: {error_msg}"
                }
            )
            
    except Exception as e:
        jh.error(f"Angel One login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
        )


@router.get("/status")
def angel_one_status():
    """
    Check if Angel One is currently authenticated
    """
    return {
        "authenticated": angel_one_session.get("authenticated", False),
        "client_code": angel_one_session.get("client_code")
    }


@router.post("/logout")
def angel_one_logout():
    """
    Logout from Angel One and clear the session
    """
    global angel_one_session
    
    try:
        if angel_one_session.get("smart_api"):
            try:
                angel_one_session["smart_api"].terminateSession(angel_one_session.get("client_code"))
            except:
                pass  # Ignore errors during logout
        
        angel_one_session = {
            "authenticated": False,
            "smart_api": None,
            "session_data": None,
            "client_code": None,
            "api_key": None,
            "feed_token": None,
            "jwt_token": None
        }
        
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


def get_angel_one_session():
    """
    Get the current Angel One session for use in trading operations.
    Returns the SmartConnect instance and session data.
    """
    if not angel_one_session.get("authenticated"):
        return None, None
    
    return angel_one_session.get("smart_api"), angel_one_session.get("session_data")
