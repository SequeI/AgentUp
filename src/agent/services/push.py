from .base import Service
from .config import ConfigurationManager


class PushNotificationService(Service):
    """Manages push notifications for the agent.

    This service handles:
    - Push notification configuration
    - Webhook management
    - Notification delivery
    """

    def __init__(self, config_manager: ConfigurationManager):
        super().__init__(config_manager)
        self._push_notifier = None
        self._backend = None

    async def initialize(self) -> None:
        self.logger.info("Initializing push notification service")

        push_config = self.config.get("push_notifications", {})
        if not push_config.get("enabled", True):
            self.logger.info("Push notifications disabled")
            self._initialized = True
            return

        self._backend = push_config.get("backend", "memory")

        try:
            if self._backend == "valkey":
                await self._setup_valkey_backend(push_config)
            else:
                await self._setup_memory_backend()

            self._initialized = True
            self.logger.info(f"Push notification service initialized with {self._backend} backend")

        except Exception as e:
            self.logger.error(f"Failed to initialize push notification service: {e}")
            raise

    async def shutdown(self) -> None:
        self.logger.debug("Shutting down push notification service")
        self._push_notifier = None

    async def _setup_memory_backend(self) -> None:
        import httpx

        from agent.push.notifier import EnhancedPushNotifier

        client = httpx.AsyncClient()
        self._push_notifier = EnhancedPushNotifier(client=client)
        self.logger.debug("Using memory push notifier")

    @property
    def push_notifier(self):
        return self._push_notifier
