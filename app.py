from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

def fix_text(text):
    """Simple text improvements - FREE API"""
    # Common fixes dictionary
    fixes = {
        " im ": " I'm ",
        " cant ": " can't ",
        " dont ": " don't ",
        " wont ": " won't ",
        " ur ": " your ",
        " u ": " you ",
        " r ": " are ",
        " pls ": " please ",
        " thx ": " thanks ",
        " helo ": " hello ",
        " wat ": " what ",
        " wen ": " when ",
        " wer ": " where ",
        " y ": " why ",
        " how r ": " how are ",
        "omw": "On my way",
        "brb": "Be right back",
        "tbh": "to be honest",
        "idk": "I don't know",
        "btw": "by the way"
    }
    
    corrected = " " + text.lower() + " "
    for wrong, right in fixes.items():
        corrected = corrected.replace(wrong, " " + right + " ")
    
    corrected = corrected.strip()
    
    # Capitalize first letter
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]
    
    # Generate suggestions
    suggestions = [
        corrected,
        corrected + "!",
        "💡 " + corrected,
        "FYI: " + corrected,
        "PS: " + corrected,
        "👉 " + corrected
    ]
    
    return {
        'original': text,
        'corrected': corrected,
        'suggestions': suggestions[:3]  # Return first 3
    }

@app.route('/improve', methods=['POST'])
def improve():
    """Main endpoint for iPhone shortcut"""
    try:
        data = request.get_json()
        text = data.get('text', 'Hel hfdhdjhfdj dlo').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = fix_text(text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'fixed': 'Error occurred'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (for monitoring)"""
    return jsonify({
        'status': 'online',
        'service': 'AI Writing Assistant',
        'version': '1.0',
        'endpoints': ['POST /improve', 'GET /health']
    })

@app.route('/test', methods=['GET'])
def test():
    """Quick test endpoint"""
    return jsonify(fix_text("helo world im here"))

@app.route('/', methods=['GET'])
def home():
    """Home page with instructions"""
    return """
    <h1>📱 AI Writing Assistant</h1>
    <p>Server is running! Use endpoints:</p>
    <ul>
        <li><strong>POST /improve</strong> - Improve text (for iPhone shortcut)</li>
        <li><strong>GET /health</strong> - Check server status</li>
        <li><strong>GET /test</strong> - Test the service</li>
    </ul>
    <p>iPhone Shortcut URL: <code>https://[your-url].onrender.com/improve</code></p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Server starting on port {port}")
    print("📱 Use this in your iPhone Shortcut:")
    print(f"   POST https://your-url.onrender.com/improve")
    app.run(host='0.0.0.0', port=port)
