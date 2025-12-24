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
    """Get suggested replies and corrected text in ONE API call"""
    
    # Smart prompt for ChatGPT
    prompt = f"""You are an English conversation assistant helping someone learn natural English.

TEXT: "{user_text}"

Return a JSON object with EXACTLY these 3 keys:
1. "suggested_replies": 3 casual, friendly reply options (array of strings)
2. "corrected_text": Grammar-corrected version (string)
3. "similar_phrases": 2-3 different ways to say the same thing (array of strings)

Rules for replies:
- Keep it NATURAL (like real people talk)
- Use SIMPLE English (not complex vocabulary)
- Make it FRIENDLY
- Include 1 reply with emoji if appropriate 😊
- All replies should be 1 short sentence

Example format:
{{
  "suggested_replies": ["Thanks!", "Got it!", "Okay!"],
  "corrected_text": "Hello there",
  "similar_phrases": ["Hi there", "Hey"]
}}"""

    try:
        # OpenAI API call (works with openai==0.28)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use gpt-4 if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Return ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Balanced creativity
            max_tokens=350    # Enough for all responses
        )
        
        # Extract response content
        content = response['choices'][0]['message']['content'].strip()
        
        # Debug logging (prints to Render logs)
        print(f"📨 Received: {user_text[:50]}...")
        print(f"🤖 ChatGPT raw response: {content[:100]}...")
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            
            # Validate required keys exist
            required_keys = ["suggested_replies", "corrected_text", "similar_phrases"]
            if all(key in result for key in required_keys):
                return result
            else:
                print(f"⚠️ Missing keys in response: {result.keys()}")
                
        # If JSON parsing failed, use fallback
        print("⚠️ JSON parsing failed, using fallback")
        return get_fallback_response(user_text)
            
    except openai.error.AuthenticationError:
        print("❌ OpenAI Authentication Error: Invalid API key")
        return {
            "error": "OpenAI API key is invalid",
            "suggested_replies": ["Please check API key", "Setup required", "Contact admin"],
            "corrected_text": user_text,
            "similar_phrases": [user_text]
        }
    except openai.error.RateLimitError:
        print("❌ OpenAI Rate Limit: Too many requests")
        return {
            "error": "Rate limit exceeded",
            "suggested_replies": ["Try again later", "Server busy", "Please wait"],
            "corrected_text": user_text,
            "similar_phrases": [user_text]
        }
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return get_fallback_response(user_text)

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
    """
    Main endpoint - returns everything in one response
    Expected JSON: {"text": "your message here"}
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No JSON data received",
                "solution": "Send JSON: {'text': 'your message'}"
            }), 400
        
        user_text = data.get('text', '').strip()
        
        # Validate input
        if not user_text:
            return jsonify({
                "error": "Empty text",
                "example": "Send {'text': 'hello world'}"
            }), 400
        
        if len(user_text) > 500:
            return jsonify({
                "error": "Text too long (max 500 characters)",
                "received_length": len(user_text)
            }), 400
        
        # Get AI suggestions
        result = get_smart_suggestions(user_text)
        
        # Add metadata
        result['original_text'] = user_text
        result['success'] = 'error' not in result
        result['characters_processed'] = len(user_text)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Server error in /suggest: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "original_text": user_text if 'user_text' in locals() else "unknown",
            "suggested_replies": ["Server error", "Please try again"],
            "corrected_text": "Error occurred",
            "similar_phrases": ["Try again later"]
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
