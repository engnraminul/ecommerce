from django.apps import AppConfig


class IncompleteOrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incomplete_orders'
    verbose_name = 'Incomplete Orders'
    
    def ready(self):
        import incomplete_orders.signals
