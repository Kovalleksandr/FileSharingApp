from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

logger = logging.getLogger('accounts')

class LoggingTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        logger.debug(f"Token request: username={request.data.get('username')}")
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Token issued for username={request.data.get('username')}")
        else:
            logger.warning(f"Token request failed: {response.data}")
        return response