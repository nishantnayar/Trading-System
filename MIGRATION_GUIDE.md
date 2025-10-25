# Migration Guide: HTMX to Streamlit UI

This guide documents the migration from the HTMX-based web interface to the new Streamlit UI.

## What Changed

### ✅ **Removed Components**
- **HTML Templates**: All Jinja2 templates removed (`src/web/templates/`)
- **Static Files**: CSS, JS, and image files removed (`src/web/static/`)
- **Web Routes**: HTML response routes removed from FastAPI
- **Template Dependencies**: Jinja2Templates and StaticFiles removed

### ✅ **New Components**
- **Streamlit App**: Complete UI rebuilt in `streamlit_app.py`
- **Streamlit Utils**: Helper functions in `streamlit_utils.py`
- **Startup Script**: `run_streamlit.py` for easy launching
- **Configuration**: `.streamlit/config.toml` for Streamlit settings

## Migration Benefits

### 🚀 **Performance Improvements**
- **Faster Development**: No more HTML/CSS/JS complexity
- **Real-time Updates**: Streamlit's reactive framework
- **Better Charts**: Plotly integration for financial visualizations
- **Simplified Deployment**: Single Python app

### 📊 **Enhanced Features**
- **Interactive Charts**: Advanced Plotly charts with zoom, pan, hover
- **Real-time Data**: Automatic refresh and live updates
- **Better UX**: Modern Streamlit interface with sidebar navigation
- **Technical Analysis**: Built-in technical indicators (RSI, MACD, Bollinger Bands)

### 🛠️ **Developer Experience**
- **Python-Only**: No more HTML/CSS/JS knowledge required
- **Type Safety**: Full Python type hints and error handling
- **Modular Design**: Clean separation of concerns
- **Easy Testing**: Streamlit's built-in testing capabilities

## Architecture Changes

### **Before (HTMX)**
```
FastAPI Server (Port 8001)
├── HTML Templates (Jinja2)
├── Static Files (CSS/JS)
├── HTMX Interactions
└── API Endpoints
```

### **After (Streamlit)**
```
FastAPI API Server (Port 8001)     Streamlit UI (Port 8501)
├── Pure API Endpoints            ├── Interactive Dashboard
├── JSON Responses                ├── Real-time Charts
└── API Documentation            ├── Trading Interface
                                 └── Analysis Tools
```

## File Changes

### **Removed Files**
```
src/web/templates/          # All HTML templates
src/web/static/            # All static assets
├── base.html
├── dashboard.html
├── trading.html
├── analysis.html
├── strategies.html
├── profile.html
├── landing.html
└── components/
```

### **Added Files**
```
streamlit_app.py           # Main Streamlit application
streamlit_utils.py         # Utility functions
run_streamlit.py          # Startup script
.streamlit/config.toml    # Streamlit configuration
README_STREAMLIT.md       # Streamlit documentation
MIGRATION_GUIDE.md        # This file
```

### **Modified Files**
```
src/web/main.py           # Removed web interface dependencies
src/web/api/routes.py     # Removed HTML routes
requirements.txt          # Added Streamlit dependencies
```

## API Changes

### **Removed Endpoints**
- `GET /` (HTML landing page)
- `GET /dashboard` (HTML dashboard)
- `GET /trading` (HTML trading page)
- `GET /analysis` (HTML analysis page)
- `GET /strategies` (HTML strategies page)
- `GET /profile` (HTML profile page)

### **Updated Endpoints**
- `GET /` → Returns JSON with UI information
- `GET /health` → Updated with UI information

### **Unchanged Endpoints**
All API endpoints remain the same:
- `/api/alpaca/*` - Trading operations
- `/api/market-data/*` - Market data
- `/api/company-info/*` - Company information
- `/api/key-statistics/*` - Financial metrics
- `/api/financial-statements/*` - Financial data
- `/api/institutional-holders/*` - Institutional data
- `/api/company-officers/*` - Company officers

## Usage Changes

### **Starting the System**

**Before:**
```bash
python main.py  # Started both API and web interface
```

**After:**
```bash
# Terminal 1: Start API server
python main.py

# Terminal 2: Start Streamlit UI
python run_streamlit.py
```

### **Accessing the Interface**

**Before:**
- Web Interface: http://localhost:8001
- API Docs: http://localhost:8001/docs

**After:**
- Streamlit UI: http://localhost:8501 (Primary)
- API Docs: http://localhost:8001/docs
- API Health: http://localhost:8001/health

## Feature Mapping

| HTMX Feature | Streamlit Equivalent | Status |
|-------------|---------------------|---------|
| Dashboard | Dashboard Page | ✅ Enhanced |
| Trading Interface | Trading Page | ✅ Enhanced |
| Market Analysis | Analysis Page | ✅ Enhanced |
| Strategy Management | Strategy Management Page | ✅ Enhanced |
| Company Info | Company Info Page | ✅ Enhanced |
| Real-time Charts | Plotly Charts | ✅ Improved |
| Data Tables | Streamlit Dataframes | ✅ Improved |
| Forms | Streamlit Forms | ✅ Improved |

## Development Workflow

### **Adding New Features**

**Before:**
1. Create HTML template
2. Add CSS styling
3. Write JavaScript for interactivity
4. Update FastAPI routes
5. Test across browsers

**After:**
1. Add function to `streamlit_app.py`
2. Use Streamlit components
3. Test in Streamlit
4. Deploy

### **Debugging**

**Before:**
- Browser developer tools
- HTML/CSS debugging
- JavaScript console
- Network tab for API calls

**After:**
- Streamlit debug mode
- Python debugger
- Streamlit logs
- API endpoint testing

## Deployment Considerations

### **Production Deployment**

**Streamlit:**
```bash
# Using Streamlit Cloud
streamlit run streamlit_app.py --server.port 8501

# Using Docker
docker run -p 8501:8501 trading-system

# Using reverse proxy (nginx)
upstream streamlit {
    server localhost:8501;
}
```

### **Scaling**

**Before:**
- Single FastAPI instance
- Static file serving
- Template rendering

**After:**
- Separate API and UI servers
- API can be scaled independently
- UI can be deployed separately

## Troubleshooting

### **Common Issues**

1. **Port Conflicts**
   - API: Change port in `main.py`
   - Streamlit: Change port in `.streamlit/config.toml`

2. **API Connection**
   - Check `API_BASE_URL` in `streamlit_app.py`
   - Verify FastAPI server is running
   - Check firewall settings

3. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Streamlit Issues**
   ```bash
   streamlit run streamlit_app.py --logger.level debug
   ```

## Rollback Plan

If you need to rollback to HTMX:

1. **Restore Templates** (from git history)
2. **Restore Static Files** (from git history)
3. **Revert FastAPI Changes** (from git history)
4. **Remove Streamlit Files**

```bash
git checkout HEAD~1 -- src/web/templates/
git checkout HEAD~1 -- src/web/static/
git checkout HEAD~1 -- src/web/main.py
git checkout HEAD~1 -- src/web/api/routes.py
rm streamlit_app.py streamlit_utils.py run_streamlit.py
```

## Support

For issues with the new Streamlit UI:
- Check `README_STREAMLIT.md` for detailed documentation
- Review Streamlit logs for errors
- Test API endpoints directly
- Check FastAPI server status

## Conclusion

The migration to Streamlit provides:
- **Simplified Development**: Python-only interface
- **Enhanced Features**: Better charts and interactivity
- **Improved Performance**: Faster development and deployment
- **Better UX**: Modern, responsive interface
- **Easier Maintenance**: Single codebase for UI logic

The new Streamlit UI is now the primary interface for the Trading System, providing all the functionality of the previous HTMX interface with significant improvements in usability and development experience.
