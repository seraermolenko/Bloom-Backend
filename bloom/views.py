from django.shortcuts import render
from rest_framework import viewsets
from .models import Gardens
from rest_framework import viewsets
from .models import Plant
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q  
from .models import PersonalPlant
from .serializers import PlantSerializer
from .serializers import personalPlantSerializer
from confluent_kafka import Producer

def home(request):
    return render(request, 'home.html') 

# class GardensViewSet(viewsets.ModelViewSet):
#     queryset = Gardens.objects.all()
#     serializer_class = GardensSerializer

@api_view(['GET'])
def search_plants(request):
    query = request.GET.get('name')
    
    plants = Plant.objects.filter(
    Q(common_name__icontains=query) | Q(scientific_name__icontains=query) )

    if not plants:
        return Response('No plants found', status=status.HTTP_404_NOT_FOUND)
    
    serializer = PlantSerializer(plants, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

producer = Producer({
    # kafkas contact point, the host and port of broker 
    'bootstrap.servers': 'localhost:9092' 
})

@api_view(['POST'])
def send_humidity(request):
    try:
        # Reading the http post request from esp32
        data = request.json
        plant_id = data.get("sensor_id")
        humidity = data.get("humidity")

        if not plant_id or humidity is None:
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)

        # Kafka requires a serialized message
        producer.produce("humidity", key=str(plant_id), value=json.dumps(data))
        producer.flush()
        return Response({"message": "Data sent to Kafka"}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

