from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings

from user.serializers import UserSerializers


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializers
    permission_classes = ()


class LoginUserView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializers
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
