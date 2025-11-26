# Vanilla JavaScript Frontend Server Script
# Simple HTTP server to serve the vanilla JS frontend

echo "Starting Robot ML Web App - Vanilla JS Frontend"
echo "================================================"
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "Using Python3 HTTP Server"
    echo "Frontend will be available at: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    cd "$(dirname "$0")"
    python3 -m http.server 3000
elif command -v python &> /dev/null; then
    echo "Using Python HTTP Server"
    echo "Frontend will be available at: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    cd "$(dirname "$0")"
    python -m http.server 3000
else
    echo "Error: Python is not installed"
    echo "Please install Python or use another method to serve the files"
    echo ""
    echo "Alternative options:"
    echo "1. npm install -g http-server && npx http-server -p 3000"
    echo "2. Use VS Code Live Server extension"
    echo "3. Configure Nginx to serve the directory"
    exit 1
fi
