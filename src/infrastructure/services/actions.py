import time
import numpy as np
from threading import Thread
import ctypes
from ctypes import wintypes
import pyautogui



user32 = ctypes.WinDLL('user32', use_last_error=True)

# Constants
TOUCH_FEEDBACK_DEFAULT = 0x1
POINTER_INPUT_TYPE_TOUCH = 0x00000002
POINTER_FLAG_DOWN = 0x00010000
POINTER_FLAG_UP = 0x00040000
POINTER_FLAG_INRANGE = 0x00000008
POINTER_FLAG_INCONTACT = 0x00000004

# Structs
class POINTER_INFO(ctypes.Structure):
    _fields_ = [
        ("pointerType", wintypes.DWORD),
        ("pointerId", wintypes.UINT),
        ("frameId", wintypes.UINT),
        ("pointerFlags", wintypes.INT),
        ("sourceDevice", wintypes.HANDLE),
        ("hwndTarget", wintypes.HWND),
        ("ptPixelLocation", wintypes.POINT),
        ("ptHimetricLocation", wintypes.POINT),
        ("ptPixelLocationRaw", wintypes.POINT),
        ("ptHimetricLocationRaw", wintypes.POINT),
        ("dwTime", wintypes.DWORD),
        ("historyCount", wintypes.UINT),
        ("inputData", wintypes.INT),
        ("dwKeyStates", wintypes.DWORD),
        ("PerformanceCount", wintypes.UINT),
        ("ButtonChangeType", wintypes.INT),
    ]

class POINTER_TOUCH_INFO(ctypes.Structure):
    _fields_ = [
        ("pointerInfo", POINTER_INFO),
        ("touchFlags", wintypes.DWORD),
        ("touchMask", wintypes.DWORD),
        ("rcContact", wintypes.RECT),
        ("rcContactRaw", wintypes.RECT),
        ("orientation", wintypes.UINT),
        ("pressure", wintypes.UINT),
    ]

InitializeTouchInjection = user32.InitializeTouchInjection
InitializeTouchInjection.argtypes = (wintypes.UINT, wintypes.DWORD)
InitializeTouchInjection.restype = wintypes.BOOL

InjectTouchInput = user32.InjectTouchInput
InjectTouchInput.argtypes = (wintypes.UINT, ctypes.POINTER(POINTER_TOUCH_INFO))
InjectTouchInput.restype = wintypes.BOOL

def touch_click(x, y):
    if not InitializeTouchInjection(1, TOUCH_FEEDBACK_DEFAULT):
        raise ctypes.WinError(ctypes.get_last_error())

    pti = POINTER_TOUCH_INFO()
    pti.pointerInfo.pointerType = POINTER_INPUT_TYPE_TOUCH
    pti.pointerInfo.pointerId = 0
    pti.pointerInfo.ptPixelLocation.x = x
    pti.pointerInfo.ptPixelLocation.y = y
    pti.pointerInfo.pointerFlags = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT
    pti.touchFlags = 0
    pti.touchMask = 0x0003  # TOUCH_MASK_CONTACTAREA | TOUCH_MASK_ORIENTATION
    pti.orientation = 90
    pti.pressure = 32000

    # تحديد الكونتاكت اريا
    pti.rcContact.left = x - 2
    pti.rcContact.right = x + 2
    pti.rcContact.top = y - 2
    pti.rcContact.bottom = y + 2

    if not InjectTouchInput(1, ctypes.byref(pti)):
        raise ctypes.WinError(ctypes.get_last_error())

    time.sleep(0.05)  

    pti.pointerInfo.pointerFlags = POINTER_FLAG_UP
    if not InjectTouchInput(1, ctypes.byref(pti)):
        raise ctypes.WinError(ctypes.get_last_error())






class ActionController:
    def __init__(self):
        # Action states
        self.is_dragging = False
        self.drag_start_pos = None
        self.last_click_time = 0
        self.click_cooldown = 0.5  # Prevent rapid clicks
        
        # Thread for handling actions
        self.action_thread = None
        self.is_running = False
        
        # Keyboard state
        self.keyboard_active = False
        self.current_key = None
        self.last_key_time = 0
        self.key_cooldown = 0.3  # Prevent rapid key presses
        
        # Initialize Windows API
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.shell32 = ctypes.WinDLL('shell32', use_last_error=True)
        
        # Define Windows API structures
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]
        
        class APPBARDATA(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("hWnd", wintypes.HWND),
                ("uCallbackMessage", ctypes.c_uint),
                ("uEdge", ctypes.c_uint),
                ("rc", RECT),
                ("lParam", ctypes.c_long),
            ]
        
        class INPUT(ctypes.Structure):
            class _MOUSEINPUT(ctypes.Structure):
                _fields_ = [("dx", ctypes.c_long),
                            ("dy", ctypes.c_long),
                            ("mouseData", ctypes.c_ulong),
                            ("dwFlags", ctypes.c_ulong),
                            ("time", ctypes.c_ulong),
                            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
                
            _fields_ = [("type", ctypes.c_ulong),
                        ("mi", _MOUSEINPUT)]
        
        # Store structures
        self.POINT = POINT
        self.INPUT = INPUT
        self.RECT = RECT
        self.APPBARDATA = APPBARDATA
        
        # Define mouse event constants
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_WHEEL = 0x0800
        self.INPUT_MOUSE = 0
        
        # Taskbar constants
        self.ABM_GETTASKBARPOS = 0x00000005
        
        # Set up Windows API functions
        self.SetCursorPos = self.user32.SetCursorPos
        self.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self.SetCursorPos.restype = wintypes.BOOL
        
        self.GetCursorPos = self.user32.GetCursorPos
        self.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self.GetCursorPos.restype = wintypes.BOOL
        
        self.SendInput = self.user32.SendInput
        self.SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
        self.SendInput.restype = ctypes.c_uint
        
        # Debug mode
        self.debug_mode = True
        
        # Dashboard tracking
        self.last_dashboard_region = None
        self.dashboard_window = None

    def start(self):
        """Start the action controller thread"""
        self.is_running = True
        self.action_thread = Thread(target=self._action_loop)
        self.action_thread.daemon = True
        self.action_thread.start()
    
    def stop(self):
        """Stop the action controller thread"""
        self.is_running = False
        if self.action_thread:
            self.action_thread.join()
    
    def _action_loop(self):
        """Main loop for handling actions"""
        while self.is_running:
            time.sleep(0.01)  # Small delay to prevent high CPU usage
    
    def check_cooldown(self):
        """Check if enough time has passed since last action"""
        current_time = time.time()
        if current_time - self.last_click_time >= self.click_cooldown:
            self.last_click_time = current_time
            return True
        return False

    def get_cursor_position(self):
        """Get current cursor position"""
        point = self.POINT()
        self.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    def set_cursor_position(self, x, y):
        """Set cursor position"""
        return self.SetCursorPos(x, y)

    def touch_click_current_position(self):
        """Perform a touch click at the current cursor position"""
        if self.check_cooldown():
            x, y = self.get_cursor_position()
            try:
                # Initialize touch injection (لو مش متعمل قبل كده)
                if not InitializeTouchInjection(1, TOUCH_FEEDBACK_DEFAULT):
                    raise ctypes.WinError(ctypes.get_last_error())
                
                pti = POINTER_TOUCH_INFO()
                pti.pointerInfo.pointerType = POINTER_INPUT_TYPE_TOUCH
                pti.pointerInfo.pointerId = 0
                pti.pointerInfo.ptPixelLocation.x = x
                pti.pointerInfo.ptPixelLocation.y = y
                pti.pointerInfo.pointerFlags = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT
                pti.touchFlags = 0
                pti.touchMask = 0x0003  # TOUCH_MASK_CONTACTAREA | TOUCH_MASK_ORIENTATION
                pti.orientation = 90
                pti.pressure = 32000

                # Contact Area حوالي النقطة
                pti.rcContact.left = x - 2
                pti.rcContact.right = x + 2
                pti.rcContact.top = y - 2
                pti.rcContact.bottom = y + 2

                # Send touch down
                if not InjectTouchInput(1, ctypes.byref(pti)):
                    raise ctypes.WinError(ctypes.get_last_error())

                time.sleep(0.05)  # Delay طبيعي

                # Send touch up
                pti.pointerInfo.pointerFlags = POINTER_FLAG_UP
                if not InjectTouchInput(1, ctypes.byref(pti)):
                    raise ctypes.WinError(ctypes.get_last_error())

                if self.debug_mode:
                    print(f"Touch clicked at ({x}, {y})")
            
            except Exception as e:
                print(f"Error during touch click: {e}")

    
    
    def click(self):
        """Perform a left click"""
        if self.check_cooldown():
            # Create mouse down event
            input_down = self.INPUT()
            input_down.type = self.INPUT_MOUSE
            input_down.mi.dwFlags = self.MOUSEEVENTF_LEFTDOWN
            self.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(self.INPUT))
            
            # Small delay between down and up
            time.sleep(0.01)
            
            # Create mouse up event
            input_up = self.INPUT()
            input_up.type = self.INPUT_MOUSE
            input_up.mi.dwFlags = self.MOUSEEVENTF_LEFTUP
            self.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(self.INPUT))
            # self.touch_click_current_position()
            if self.debug_mode:
                print("clicked")

    def double_click(self):
        """Perform a double click"""
        if self.check_cooldown():
            pyautogui.click(button='left', clicks=2)
            if self.debug_mode: 
                print("double clicked")

    def right_click(self):
        """Perform a right click"""
        if self.check_cooldown():
            # Create mouse down event
            input_down = self.INPUT()
            input_down.type = self.INPUT_MOUSE
            input_down.mi.dwFlags = self.MOUSEEVENTF_RIGHTDOWN
            self.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(self.INPUT))
            
            # Small delay between down and up
            time.sleep(0.01)
            
            # Create mouse up event
            input_up = self.INPUT()
            input_up.type = self.INPUT_MOUSE
            input_up.mi.dwFlags = self.MOUSEEVENTF_RIGHTUP
            self.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(self.INPUT))
            if self.debug_mode:
                print("right clicked")

    def scroll_up(self):
        """Scroll up"""
        if self.check_cooldown():
            input_scroll = self.INPUT()
            input_scroll.type = self.INPUT_MOUSE
            input_scroll.mi.dwFlags = self.MOUSEEVENTF_WHEEL
            input_scroll.mi.mouseData = 120  # Standard scroll amount
            self.SendInput(1, ctypes.byref(input_scroll), ctypes.sizeof(self.INPUT))
            if self.debug_mode:
                print("scrolled up")

    def scroll_down(self):
        """Scroll down"""
        if self.check_cooldown():
            input_scroll = self.INPUT()
            input_scroll.type = self.INPUT_MOUSE
            input_scroll.mi.dwFlags = self.MOUSEEVENTF_WHEEL
            input_scroll.mi.mouseData = -120  # Standard scroll amount
            self.SendInput(1, ctypes.byref(input_scroll), ctypes.sizeof(self.INPUT))
            if self.debug_mode:
                print("scrolled down")

    def mouse_down(self):
        """Simulate mouse button down"""
        input_down = self.INPUT()
        input_down.type = self.INPUT_MOUSE
        input_down.mi.dwFlags = self.MOUSEEVENTF_LEFTDOWN
        self.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(self.INPUT))

    def mouse_up(self):
        """Simulate mouse button up"""
        input_up = self.INPUT()
        input_up.type = self.INPUT_MOUSE
        input_up.mi.dwFlags = self.MOUSEEVENTF_LEFTUP
        self.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(self.INPUT))

    def drag_and_drop(self):
        """Handle drag and drop operation"""
        if not self.is_dragging:
            self.mouse_down()
            self.is_dragging = True
        else:
            self.mouse_up()
            self.is_dragging = False

    def get_taskbar_position(self):
        """Get the taskbar position and dimensions"""
        try:
            abd = self.APPBARDATA()
            abd.cbSize = ctypes.sizeof(self.APPBARDATA)
            
            result = self.shell32.SHAppBarMessage(self.ABM_GETTASKBARPOS, ctypes.byref(abd))
            
            if result:
                rect = abd.rc
                return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
            return None
        except Exception as e:
            if self.debug_mode:
                print(f"Error getting taskbar position: {str(e)}")
            return None

    def is_in_taskbar(self, x, y):
        """Check if coordinates are within the taskbar region"""
        taskbar = self.get_taskbar_position()
        if taskbar:
            left, top, width, height = taskbar
            return (left <= x <= left + width and 
                    top <= y <= top + height)
        return False

    def update_dashboard_region(self, dashboard_region):
        """Update the current dashboard region"""
        if dashboard_region != self.last_dashboard_region:
            self.last_dashboard_region = dashboard_region
            if self.debug_mode:
                print(f"\nDashboard Region Updated:")
                print(f"New Region: {dashboard_region}\n")

    def is_in_control_region(self, x, y, dashboard_region=None):
        """Check if coordinates are in either taskbar or dashboard region"""
        # Update dashboard region if provided
        if dashboard_region:
            self.update_dashboard_region(dashboard_region)
        
        # Check taskbar
        if self.is_in_taskbar(x, y):
            return True
        
        # Check dashboard region using last known position
        if self.last_dashboard_region:
            d_left, d_top, d_width, d_height = self.last_dashboard_region
            
            # Calculate absolute coordinates of dashboard boundaries
            dashboard_right = d_left + d_width
            dashboard_bottom = d_top + d_height
            
            # Check if cursor is within dashboard bounds
            is_in_dashboard = (d_left <= x <= dashboard_right and 
                                d_top <= y <= dashboard_bottom)
            
            if self.debug_mode and is_in_dashboard:
                current_time = time.time()
                if current_time - self.t > 1:
                    
                    print(f"Is in dashboard: {is_in_dashboard}\n")
                    print(f"Dashboard Region: Left={d_left}, Top={d_top}, Right={dashboard_right}, Bottom={dashboard_bottom}")
                    self.t = current_time
            
            return is_in_dashboard
        
        return False
    

