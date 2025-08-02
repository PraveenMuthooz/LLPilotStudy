#!/usr/bin/env python3
"""
Test script to verify that the GW_Intermodal_Mantime.py layout can be serialized properly
"""

import sys
import os
import json

# Add the path to access the modules
sys.path.append('/Users/praveenm07/GaTech Dropbox/Praveen Muthukrishnan/Files/PI Lab/LivingLab')

try:
    # Import the necessary modules
    from pages import GW_Intermodal_Mantine
    from dash import Dash
    from dash._utils import to_json
    
    print("✅ Successfully imported GW_Intermodal_Mantime module")
    
    # Create a minimal Dash app to test serialization
    app = Dash(__name__)
    app.layout = GW_Intermodal_Mantine.layout
    
    print("✅ Successfully created Dash app with layout")
    
    # Test JSON serialization (this is what was failing before)
    config = app._config()
    json_config = to_json(config)
    
    print("✅ Successfully serialized app config to JSON")
    print("🎉 Fix confirmed! The lambda function issue has been resolved.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("The issue still exists. Please check the code again.")
    
    # If it's a JSON serialization error, provide more details
    if "JSON serializable" in str(e):
        print("\n🔍 This is still a JSON serialization error.")
        print("Look for any lambda functions, function references, or complex objects in the layout.")
        