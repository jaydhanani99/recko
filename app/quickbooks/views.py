from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import views

from django.conf import settings

from datetime import datetime

from core.models import Account, Integration
from quickbooks import serializers

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError

class QuickbooksViewSet(viewsets.ModelViewSet):
    """ Manage quickbooks account in database """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Account.objects.all()
    serializer_class = serializers.QuickbooksSerializer

    def get_queryset(self):
        """Return objects for the current authenticated users only and for quickbooks integration only"""
        return self.queryset.filter(user=self.request.user, integration=2)
    
    def create(self, request, *args, **kwargs):
            # Override create method to prevent duplicate object creation
            serializer = serializers.QuickbooksSerializer(data=self.request.data)
            serializer.is_valid(raise_exception=True)

            user = self.request.user
            integration = 2

            # Default scope
            scopes = 'com.intuit.quickbooks.accounting'

            if Account.objects.filter(user=user, integration=integration).exists():
                return Response(status=status.HTTP_409_CONFLICT)
                
            quickbooks = serializer.save(user=self.request.user, integration=Integration.objects.get(pk=2), scopes=scopes)
            response_serialized_quickbooks = serializers.QuickbooksSerializer(quickbooks).data
            return Response(response_serialized_quickbooks, status=status.HTTP_201_CREATED)

# class QuickbooksAuthResponseViewSet(GenericViewSet):
#     """Custom viewset for quickbooks auth response"""

#     serializer_class = serializers.QuickbooksAuthResponseSerializer
#     queryset = Account.objects.all()

#     def get_queryset(self):
#         return Account.objects.all()
    
#     @action(methods=['get'], detail=False)
#     def me(self, request):
#         """Custome GET Endpoint to receive the authorization code"""
#         serializer = self.get_serializer_class()
#         # serializer.is_valid(raise_exception=True)
#         # data = serializer(data=self.request.data).data
#         return Response([], status=status.HTTP_200_OK)

class QuickbooksAuthResponseView(views.APIView):
    """Custom viewset for quickbooks auth response"""

    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        """Custome GET Endpoint to receive the authorization code"""

        state = request.query_params['state']
        authorization_code = request.query_params['code']
        realm_id = request.query_params['realmId']

        # Can be merged to access_token store db call
        # Identifying  user based on state
        Account.objects.filter(pk=state).update(authorization_code=authorization_code, realm_id=realm_id)

        quickbook_account = Account.objects.filter(pk=state).first()
        quickbook_integration = Integration.objects.filter(id=2).first()

        if not quickbook_account:
            return Response('No matching associated state found.', status=status.HTTP_400_BAD_REQUEST)


        # Creating auth_client object
        redirect_uri = settings.APPLICATION_URL+'/api/quickbooks/auth/response'
        auth_client = AuthClient(quickbook_integration.client_id, quickbook_integration.client_secret, redirect_uri, "sandbox", state)
        # Generating access token
        try:
            auth_client.get_bearer_token(authorization_code, realm_id=realm_id)
            
            access_token = auth_client.access_token
            expires_in = auth_client.expires_in
            refresh_token = auth_client.refresh_token
            x_refresh_token_expires_in = auth_client.x_refresh_token_expires_in
            id_token = auth_client.id_token

            Account.objects.filter(pk=state).update(access_token=access_token, expires_in=expires_in, 
                                                refresh_token=refresh_token, x_refresh_token_expires_in=x_refresh_token_expires_in,
                                                id_token=id_token, is_authenticated=True)

        except AuthClientError as e:
            error = 'status_code='+str(e.status_code)+', error='+str(e.content)
            error_at = datetime.now()
            Account.objects.filter(pk=state).update(error_desc=error, error_at=error_at)

        # Redirect to frontend page after successfull generation of access token
        return Response(auth_client.access_token)

class QuickbooksAuthRequestView(views.APIView):
    """Custom viewset for quickbooks auth response"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_quickbook_scopes(self, scope):
        """Used to return scopes in ENUM format provided by quickbooks SDK"""
        switcher = {
            'com.intuit.quickbooks.accounting': Scopes.ACCOUNTING,
            'com.intuit.quickbooks.payment': Scopes.PAYMENT,
            'com.intuit.quickbooks.payroll': Scopes.PAYROLL,
            'com.intuit.quickbooks.payroll.timetracking': Scopes.PAYROLL_TIMETRACKING,
            'com.intuit.quickbooks.payroll.benefits': Scopes.PAYROLL_BENEFITS,
        }
        return switcher.get(scope, None)
    
    def get(self, request, *args, **kwargs):
        """Custome GET Endpoint to request the authorization URL"""
        user = self.request.user
        quickbook_account = Account.objects.filter(user=user, integration=2).first()
        quickbook_integration = Integration.objects.filter(id=2).first()
        
        if not quickbook_account:
            return Response("No matching quickbooks account available", status=status.HTTP_404_NOT_FOUND)

        # Creating quickbooks client to generate the authentication url
        # auth_client = AuthClient( client_id, client_secret, redirect_uri, environment )
        # environmen could be sandbox or production
        redirect_uri = settings.APPLICATION_URL+'/api/quickbooks/auth/response'
        auth_client = AuthClient( quickbook_integration.client_id, quickbook_integration.client_secret, redirect_uri, "sandbox", quickbook_account.id)


        scopes = []
        if not quickbook_account.scopes:
            scopes.append(Scopes.ACCOUNTING)
        else:
            for scope in [x.strip() for x in quickbook_account.scopes.split(' ')]:
                current_scope = self.get_quickbook_scopes(scope)
                if current_scope:
                    scopes.append(current_scope)
            if not scopes:
                scopes.append(Scopes.ACCOUNTING)

        auth_url = auth_client.get_authorization_url(scopes)

        return Response(auth_url)
