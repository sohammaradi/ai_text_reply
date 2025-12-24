"""
Simple English Assistant API
Deploy on Render: https://render.com
One endpoint: /suggest - returns replies + corrections
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ============================================
# CONFIGURATION
# ============================================

# Get API key from environment variable (set in Render dashboard)
# Important: DO NOT hardcode your key here!
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    print("⚠️ WARNING: OPENAI_API_KEY not found in environment variables!")
    print("   Please set it in Render dashboard → Environment tab")

# ============================================
# CORE FUNCTION
# ============================================

def get_smart_suggestions(user_text):
    """Get ALL suggestions formatted for display"""
    
    prompt = f"""TEXT: "{user_text}"

Return a JSON with these EXACT keys:
1. "display_text": Formatted string with ALL suggestions
2. "first_reply": First reply option (for auto-copy)
3. "all_replies": Array of all reply options

FORMAT the "display_text" like this example:
📤 Original: helo cant meet today

✅ Corrected: Hello, can't meet today

💬 Reply Options:
• No worries! Maybe tomorrow? 😊
• Got it, thanks for letting me know!
• Okay, another time then!

🔄 Similar Phrases:
• Hi, unavailable today
• Hey, busy today

Keep it CLEAN and SIMPLE."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON with display_text, first_reply, all_replies keys."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        content = response['choices'][0]['message']['content']
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return get_fallback_display(user_text)
            
    except Exception as e:
        print(f"API Error: {e}")
        return get_fallback_display(user_text)

def get_fallback_display(text):
    """Simple fallback with everything formatted"""
    # Basic correction
    corrected = text
    fixes = [(" helo ", " hello "), (" cant ", " can't "), (" im ", " I'm ")]
    for wrong, right in fixes:
        corrected = corrected.replace(wrong, right)
    
    if corrected and len(corrected) > 0:
        corrected = corrected[0].upper() + corrected[1:]
    
    return {
        "display_text": f"""📤 Original: {text}

✅ Corrected: {corrected}

💬 Reply Options:
• Thanks! 😊
• Got it, thanks!
• Okay, noted!

🔄 Similar Phrases:
• {corrected}
• {corrected}!""",
        "first_reply": "Thanks! 😊",
        "all_replies": ["Thanks! 😊", "Got it, thanks!", "Okay, noted!"]
    }

def get_fallback_display(text):
    """Simple fallback with everything formatted"""
    # Basic correction
    corrected = text
    fixes = [(" helo ", " hello "), (" cant ", " can't "), (" im ", " I'm ")]
    for wrong, right in fixes:
        corrected = corrected.replace(wrong, right)
    
    if corrected and len(corrected) > 0:
        corrected = corrected[0].upper() + corrected[1:]
    
    return {
        "display_text": f"""📤 Original: {text}

✅ Corrected: {corrected}

💬 Reply Options:
• Thanks! 😊
• Got it, thanks!
• Okay, noted!

🔄 Similar Phrases:
• {corrected}
• {corrected}!""",
        "first_reply": "Thanks! 😊",
        "all_replies": ["Thanks! 😊", "Got it, thanks!", "Okay, noted!"]
    }

def get_fallback_response(text):
    """Fallback response when OpenAI fails"""
    # Simple text cleaning
    cleaned = text
    fixes = [
        (" helo ", " hello "),
        (" im ", " I'm "),
        (" cant ", " can't "),
        (" dont ", " don't "),
        (" wont ", " won't "),
        (" ur ", " your "),
        (" u ", " you "),
        (" pls ", " please "),
        (" thx ", " thanks ")
    ]
    
    for wrong, right in fixes:
        cleaned = cleaned.replace(wrong, right)
    
    # Capitalize first letter
    if cleaned and len(cleaned) > 0:
        cleaned = cleaned[0].upper() + cleaned[1:]
    
    return {
        "suggested_replies": [
            "Thanks! 😊",
            "Got it, thanks!",
            "Okay, noted!"
        ],
        "corrected_text": cleaned,
        "similar_phrases": [
            cleaned,
            cleaned + "!",
            "Hey, " + cleaned.lower()
        ]
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/suggest', methods=['POST'])
def suggest():
    """ONE simple endpoint returning EVERYTHING formatted"""
    try:
        data = request.get_json()
        user_text = data.get('text', '').strip()
        
        if not user_text:
            return jsonify({"error": "No text provided"}), 400
        
        # Get everything in ONE call
        result = get_smart_suggestions(user_text)
        
        # Add original text
        result['original_text'] = user_text
        result['success'] = True
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "display_text": f"❌ Error: {e}",
            "first_reply": "Error occurred",
            "all_replies": ["Try again"]
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (for monitoring)"""
    status = "healthy" if openai.api_key else "warning_no_key"
    
    return jsonify({
        "status": status,
        "service": "English Assistant API",
        "version": "1.0",
        "openai_configured": bool(openai.api_key),
        "endpoints": {
            "POST /suggest": "Get replies + corrections",
            "GET /health": "This health check",
            "GET /test": "Example response"
        },
        "usage": "Send POST to /suggest with {'text': 'your message'}"
    })

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint with example response"""
    example_text = "helo cant meet today sorry"
    
    # Generate example without calling OpenAI
    example_response = {
        "original_text": example_text,
        "corrected_text": "Hello, can't meet today, sorry.",
        "suggested_replies": [
            "No worries! Maybe tomorrow? 😊",
            "Got it, thanks for letting me know!",
            "Okay, another time then!"
        ],
        "similar_phrases": [
            "Hi, unavailable today",
            "Hey, busy today"
        ],
        "success": True,
        "characters_processed": len(example_text),
        "note": "This is a static example. Real API calls will vary."
    }
    
    return jsonify(example_response)

@app.route('/', methods=['GET'])
def home():
    """Home page with instructions"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 English Assistant API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }
            code { background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>📱 English Assistant API</h1>
        <p>Server is running! Use the endpoints below:</p>
        
        <div class="endpoint">
            <h3>📤 Main Endpoint</h3>
            <p><code>POST /suggest</code> - Get replies + corrections</p>
            <p><strong>Request:</strong></p>
            <pre>{
  "text": "your message here"
}</pre>
            <p><strong>Response includes:</strong></p>
            <ul>
                <li>3 suggested casual replies</li>
                <li>Grammar-corrected version</li>
                <li>Similar alternative phrases</li>
            </ul>
        </div>
        
        <div class="endpoint">
            <h3>📊 Other Endpoints</h3>
            <p><code>GET /health</code> - Server status</p>
            <p><code>GET /test</code> - Example response</p>
        </div>
        
        <p>📱 <strong>For iPhone Shortcut:</strong> Use URL: <code>https://[your-app].onrender.com/suggest</code></p>
    </body>
    </html>
    """

# ============================================
# SERVER STARTUP
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses port 10000
    
    print("\n" + "="*60)
    print("🚀 ENGLISH ASSISTANT API - RENDER DEPLOYMENT")
    print("="*60)
    print(f"📡 Server starting on port {port}")
    print(f"🔗 Local: http://localhost:{port}")
    print(f"🔗 Health: http://localhost:{port}/health")
    
    # Check OpenAI configuration
    if openai.api_key:
        print(f"✅ OpenAI: CONFIGURED")
        # Test key with a simple call
        try:
            test_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            print(f"✅ OpenAI: KEY VALID (test successful)")
        except Exception as e:
            print(f"⚠️ OpenAI: KEY INVALID ({str(e)[:50]}...)")
    else:
        print(f"❌ OpenAI: NOT CONFIGURED - Set OPENAI_API_KEY in Render")
    
    print("\n📚 Endpoints:")
    print(f"   POST http://localhost:{port}/suggest  (main endpoint)")
    print(f"   GET  http://localhost:{port}/health   (status check)")
    print(f"   GET  http://localhost:{port}/test     (example)")
    print("="*60 + "\n")
    
    # Start the server
    # Note: debug=False for production
    app.run(host='0.0.0.0', port=port, debug=False)
