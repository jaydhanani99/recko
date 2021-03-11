from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import views

from django.conf import settings

import urllib, requests, base64

from core.models import Account, Integration
from xero import serializers

class XeroViewSet(viewsets.ModelViewSet):
    """ Manage xero account in database """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Account.objects.all()
    serializer_class = serializers.XeroSerializer

    def get_queryset(self):
        """Return objects for the current authenticated users only and for xero integration only"""
        return self.queryset.filter(user=self.request.user, integration=1)
    
    def create(self, request, *args, **kwargs):
            # Override create method to prevent duplicate object creation
            serializer = serializers.XeroSerializer(data=self.request.data)
            serializer.is_valid(raise_exception=True)

            user = self.request.user
            integration = 1

            # Default scope
            scopes = 'accounting.journals.read'

            if Account.objects.filter(user=user, integration=integration).exists():
                return Response(status=status.HTTP_409_CONFLICT)
                
            xero = serializer.save(user=self.request.user, integration=Integration.objects.get(pk=1), scopes=scopes)
            response_serialized_xero = serializers.XeroSerializer(xero).data
            return Response(response_serialized_xero, status=status.HTTP_201_CREATED)

class XeroAuthResponseView(views.APIView):
    """Custom viewset for xero auth response"""

    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        """Custome GET Endpoint to receive the authorization code"""

        authorization_code = request.query_params['code']
        state = request.query_params['state']

        # Can be merged to access_token store db call
        # state filter is used to  cross verify the request that request is initiated by our server only from XeroAuthRequestView
        Account.objects.filter(pk=state).update(authorization_code=authorization_code)

        xero_account = Account.objects.filter(pk=state).first()
        xero_integration = Integration.objects.filter(id=1).first()

        if not xero_account:
            return Response('No matching associated state found.', status=status.HTTP_400_BAD_REQUEST)

        # Generating token from the code
        xero_base_url = 'https://identity.xero.com/connect/token'
        authorization = base64.b64encode((xero_integration.client_id+':'+xero_integration.client_secret).encode('utf-8'))
        redirect_uri = settings.APPLICATION_URL+'/api/xero/auth/response'

        # Making post request to xero to generate the access token
        payload = {"grant_type": "authorization_code", 
                    "code": xero_account.authorization_code, 
                    "redirect_uri": redirect_uri}
        header = {"Content-type": "application/x-www-form-urlencoded",
                    "authorization": "Basic "+str(authorization, "utf-8")}

        response = requests.post(xero_base_url, data=payload, headers=header)
        if response.status_code != 200:
            return Response(response.json(), response.status_code)    
        response = response.json()

        Account.objects.filter(pk=state).update(access_token=response['access_token'], expires_in=response['expires_in'], 
                                                refresh_token=response['refresh_token'], is_authenticated=True)        

        return Response(response['access_token'])


class XeroAuthRequestView(views.APIView):
    """Custom viewset for xero auth response"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        """Custome GET Endpoint to request the authorization URL"""
        user = self.request.user
        xero_account = Account.objects.filter(user=user, integration=1).first()
        xero_integration = Integration.objects.filter(id=1).first()

        if not xero_account:
            return Response("No matching xero account available", status=status.HTTP_404_NOT_FOUND)

        xero_base_url = 'https://login.xero.com/identity/connect/authorize?'

        redirect_uri = settings.APPLICATION_URL+'/api/xero/auth/response'

        xero_url_params = (('response_type', 'code'), ('client_id', xero_integration.client_id), ('redirect_uri', redirect_uri),
                            ('scope', xero_account.scopes), ('state', xero_account.id))

        # return Response(redirect_uri)
        return Response(xero_base_url+urllib.parse.urlencode(xero_url_params))