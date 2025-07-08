import asyncio
import logging
from aiohttp import web
import threading

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, port=8000):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup health check routes"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.health_check)
    
    async def health_check(self, request):
        """Simple health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'service': 'telegram-voice-bot',
            'message': 'Bot is running'
        })
    
    async def start_server(self):
        """Start the health check server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            logger.info(f"Health server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
    
    def run_in_background(self):
        """Run health server in background thread"""
        def start_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_server())
            loop.run_forever()
        
        thread = threading.Thread(target=start_loop, daemon=True)
        thread.start()
        logger.info("Health server thread started") 