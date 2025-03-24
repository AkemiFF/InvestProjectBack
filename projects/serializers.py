# projects/serializers.py
from rest_framework import serializers
from .models import Project, ProjectMedia, Sector
from users.serializers import UserProfileSerializer

class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['id', 'name', 'description']

class ProjectMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMedia
        fields = ['id', 'file_url', 'file_type', 'title', 'uploaded_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class ProjectListSerializer(serializers.ModelSerializer):
    sector = SectorSerializer(read_only=True)
    owner = UserProfileSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'owner', 'sector', 'amount_needed', 
            'amount_raised', 'status', 'created_at', 'deadline', 
            'is_featured', 'progress', 'days_left', 'participants_count',
            'interests_count'
        ]
    
    def get_progress(self, obj):
        return obj.funding_percentage()
    
    def get_days_left(self, obj):
        from django.utils import timezone
        import datetime
        
        if not obj.deadline:
            return 0
        
        delta = obj.deadline - timezone.now().date()
        return max(0, delta.days)

class ProjectDetailSerializer(serializers.ModelSerializer):
    sector = SectorSerializer(read_only=True)
    owner = UserProfileSerializer(read_only=True)
    media = ProjectMediaSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'owner', 'description', 'sector', 
            'funding_type', 'amount_needed', 'amount_raised', 'minimum_investment',
            'status', 'created_at', 'updated_at', 'deadline', 'is_featured',
            'is_boosted', 'views_count', 'interests_count', 'participants_count',
            'video_url', 'media', 'progress', 'days_left', 'is_favorite'
        ]
    
    def get_progress(self, obj):
        return obj.funding_percentage()
    
    def get_days_left(self, obj):
        from django.utils import timezone
        import datetime
        
        if not obj.deadline:
            return 0
        
        delta = obj.deadline - timezone.now().date()
        return max(0, delta.days)
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.favorite_projects.filter(id=obj.id).exists()
        return False

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    sector_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'sector_id', 'funding_type', 
            'amount_needed', 'minimum_investment', 'deadline', 'video_url'
        ]
    
    def create(self, validated_data):
        sector_id = validated_data.pop('sector_id')
        sector = Sector.objects.get(id=sector_id)
        
        user = self.context['request'].user
        project = Project.objects.create(
            owner=user,
            sector=sector,
            **validated_data
        )
        return project
    
    def update(self, instance, validated_data):
        if 'sector_id' in validated_data:
            sector_id = validated_data.pop('sector_id')
            instance.sector = Sector.objects.get(id=sector_id)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class ProjectMediaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMedia
        fields = ['file', 'file_type', 'title']